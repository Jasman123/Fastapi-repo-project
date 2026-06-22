import json
from openai import AsyncOpenAI
from app.agent.state import AgentState
from app.schemas.lead import EnrichedLead, ScoredLead, LeadOutput
from app.utils.scraper import fetch_page_text
from app.utils.cleaner import clean_text, truncate_for_llm, extract_emails_from_text
from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)

async def scrape_node(state: AgentState) -> dict:
    url = state["lead_input"].url
    logger.info(f"[scrape] Processing: {url}")

    raw_text, error = await fetch_page_text(url)

    if error:
        logger.warning(f"[scrape] Fialed for {url}: {error}")
        return{
            "raw_text": "",
            "scrape_error": error,
            "pipeline_error": f"Scrape failed: {error}",
        }
    
    cleaned = clean_text(raw_text)
    logger.info(f"[scrape] Success: {len(cleaned)} chars from {url}")
    return {"raw_text": cleaned, "scrape_error": None}

async def extract_node(state: AgentState) -> dict:
    if state.get("pipeline_error"):
        logger.warning("[extract] Skipping - pipeline error from scrape")
        enriched = EnrichedLead(
            url=state["lead_input"].url,
            scrape_succes=False,
            scrape_error=state.get("scrape_error"),
        )
        return {"enriched": enriched}
    
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    text = truncate_for_llm(state["raw_text"])
    url = state["lead_input"].url

    prompt = f"""You are a B2B lead researcher. Analyse the following website content and extract structured information.

Website URL: {url}
Website content:
{text}

Extract the following and respond ONLY with valid JSON — no markdown, no explanation:
{{
  "company_name": "string or null",
  "industry": "string or null (e.g. SaaS, Legal, E-commerce, Healthcare)",
  "location": "string or null (city, country)",
  "company_size": "string or null (e.g. 1-10, 11-50, 51-200, 201-500, 500+)",
  "description": "1-2 sentence summary of what they do",
  "tech_stack": ["list of technologies mentioned"],
  "pain_points": ["list of problems or challenges they mention"],
  "contact_email": "string or null",
  "contact_name": "string or null (founder/CEO/contact person name if found)",
  "key_signals": ["phrases that suggest they might need AI/automation services"]
}}

If you cannot find a field, use null. For lists, use empty array [] if nothing found."""
    try: 
        response = await client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800,
        )

        raw_json = response.choices[0].message.content.strip()

        raw_json = raw_json.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_json)