import asyncio
from app.agent.graph import lead_graph
from app.agent.state import AgentState
from app.schemas.lead import LeadInput, LeadOutput
from app.schemas.job import BatchJobRequest, BatchJobResponse, LeadJobResult
from app.services.sheets_services import append_lead_to_sheet
from app.services.email_services import send_hot_lead_alert
from app.services.sqlite_services import save_lead_to_db
from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)


async def run_single_lead(lead_input: LeadInput) -> LeadOutput:
    logger.info(f"Starting pipeline for: {lead_input.url}")

    initial_state: AgentState = {
        "lead_input": lead_input,
        "raw_text": "",
        "scrape_error": None,
        "enriched": None,
        "email_subject": None,
        "email_body": None,
        "output": None,
        "pipeline_error": None,
    }

    try:
        final_state = await lead_graph.ainvoke(initial_state)
        output: LeadOutput = final_state["output"]

    except Exception as e:
        logger.exception(f"Pipeline crashed for {lead_input.url}: {e}")
        output = LeadOutput(
            url=lead_input.url,
            company_name=None,
            industry=None,
            location=None,
            company_size=None,
            contact_email=None,
            score=0,
            tier="cold",
            score_breakdown={},
            error=str(e),
        )
    
    try: 
        db_id = await save_lead_to_db(output)
        output.db_id = db_id
        logger.info(f"Saved to SQLite: id={db_id}")
    
    except Exception as e:
        logger.error(f"SQLite saved failed: {e}")

    settings = get_settings()
    if settings.GOOGLE_SHEET_ID:
        try: 
            row_num = await append_lead_to_sheet(output)
            output.sheets_row = row_num
            logger.info(f"Append to Sheets: row {row_num}")

        except Exception as e:
            logger.error(f"Sheets append failed: {e}")
        
    if output.tier == "hot":
        try:
            await send_hot_lead_alert(output)
            output.alert_sent = True
            logger.info(f"Hot lead alert sent for {output.company_name}")
        
        except Exception as e :
            logger.error(f"Email alert failed: {e}")

    logger.info(
        f"Pipeline complete: {output.company_name} | "
        f"score={output.score} | tier={output.tier}"
    )
    return output

async def run_batch_leads(request: BatchJobRequest) -> BatchJobResponse:
    logger.info(
        f"Starting batch: {len(request.leads)} leads | "
        f"label='{request.job_label}'"
    )

    tasks = [run_single_lead(lead) for lead in request.leads]
    results_raw = await asyncio.gather(*tasks, return_exceptions=True)

    results: list[LeadJobResult] = []
    succeeded = failed = hot = warm = cold = 0

    for lead_input, result in zip(request.leads, results_raw):
        if isinstance(result, Exception):
            results.append(LeadJobResult(
                url=lead_input.url,
                status="failed",
                error=str(result),
            ))
            failed += 1
        else:
            output: LeadOutput = result
            if output.error:
                results.append(LeadJobResult(
                    url=lead_input.url,
                    status="failed",
                    output=output,
                    error=output.error,
                ))
                failed += 1
            else:
                results.append(LeadJobResult(
                    url=lead_input.url,
                    status="success",
                    output=output,
                ))
                succeeded += 1
                if output.tier == "hot":   hot += 1
                elif output.tier == "warm": warm += 1
                else:                       cold += 1

    logger.info(
        f"Batch complete: {succeeded} succeeded, {failed} failed | "
        f"hot={hot} warm={warm} cold={cold}"
    )

    return BatchJobResponse(
        job_label=request.job_label,
        total=len(request.leads),
        succeeded=succeeded,
        failed=failed,
        hot_leads=hot,
        warm_leads=warm,
        cold_leads=cold,
        results=results,
    )