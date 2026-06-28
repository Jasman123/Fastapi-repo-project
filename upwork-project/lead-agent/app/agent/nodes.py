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

        if not data.get("contact_email"):
            emails = extract_emails_from_text(state["raw_text"])
            if emails:
                data["contact_email"] = emails[0]

        enriched = EnrichedLead(url=url, scrape_succes=True, **data)
        logger.info(
            f"[extract] Done: {enriched.company_name} | "
            f"{enriched.industry} | email: {enriched.contact_email}" 

        )

        return {"enriched": enriched}
    
    except json.JSONDecodeError as e:
        logger.error(f"[extract] JSON parse failed: {e}")
        return {"enriched": EnrichedLead(url=url, scrape_succes=True)}
    
    except Exception as e:
        logger.exception(f"[extract] Unexpected error {e}")
        return {
            "enriched": EnrichedLead(url=url, scrape_succes=True),
            "pipeline_error": f"Extract failed: {str(e)}",
        }

def score_node(state:  AgentState) -> dict:
    settings = get_settings()
    enriched = state["enriched"]

    if not enriched:
        return {"scored": None}
    
    keywords = [k.strip().lower() for k in settings.SCORE_KEYWORDS.split(",")]

    breakdown: dict[str, int] = {}
    score = 0

    if enriched.contact_email:
        breakdown["has_contact_email"] = 20
        score += 20

    tech_text = " ".join(enriched.tech_stack).lower()
    tech_matches = [k for k in keywords if k in tech_text]
    tech_points = min(len(tech_matches) * 5, 25)

    if tech_points:
        breakdown["tech_stack_match"] = tech_points
        score += tech_points

    desc_text = (
        (enriched.description or "") + " " +
        " ".join(enriched.pain_points) + " " +
        " ".join(enriched.key_signals)
    ).lower()
    desc_matches = [k for k in keywords if k in desc_text]
    desc_points = min(len(desc_matches) * 5, 25)
    if desc_points:
        breakdown["content_keyword_match"] = desc_points
        score += desc_points

    size = (enriched.company_size or "").lower()
    if any(s in size for s in ["11", "50", "51", "100", "200"]):
        breakdown["ideal_company_size"] = 15
        score += 15

    high_value_industries = ["saas", "software", "fintech", "legal", "healthcare", "ecommerce"]
    industry = (enriched.industry or "").lower()
    if any(ind in industry for ind in high_value_industries):
        breakdown["high_value_industry"] = 15
        score += 15

    score = min(score, 100)

    if score >= settings.SCORE_THRESHOLD_HOT:
        tier = "hot"
    elif score >= settings.SCORE_THRESHOLD_WARM:
        tier = "warm"
    else:
        tier = "cold"

    scored = ScoredLead(
        enriched=enriched,
        score=score,
        tier=tier,
        score_breakdown=breakdown,
    )

    logger.info(f"[score] {enriched.company_name}: {score}/100 → {tier.upper()}")
    return {"scored": scored}

async def compose_node(state: AgentState) -> dict:
    scored = state.get("scored")
    if not scored or scored.tier == "cold":
        logger.info("[compose] Skipping cold lead — no email generated")
        return {"email_subject": None, "email_body": None}
    
    settings = get_settings()
    client = AsyncOpenAI(api_key= settings.OPENAI_API_KEY)
    enriched = scored.enriched
    custom_context = state["lead_input"].custom_context or ""


    prompt = f"""You are a senior B2B sales consultant writing a cold outreach email.
Write a short, personalised email to this company.

Company details:
- Name: {enriched.company_name or 'the company'}
- Industry: {enriched.industry or 'unknown'}
- Location: {enriched.location or 'unknown'}
- Size: {enriched.company_size or 'unknown'}
- What they do: {enriched.description or 'unknown'}
- Tech stack: {', '.join(enriched.tech_stack) if enriched.tech_stack else 'unknown'}
- Pain points: {', '.join(enriched.pain_points) if enriched.pain_points else 'none identified'}
- Key signals: {', '.join(enriched.key_signals) if enriched.key_signals else 'none'}
- Contact: {enriched.contact_name or 'the team'}
- Lead score: {scored.score}/100

Additional context: {custom_context if custom_context else 'None'}

Your offer: You are an AI/ML freelancer who builds RAG pipelines, AI agents,
and automation systems using Python, LangChain, FastAPI, and LangGraph.

Rules:
- Under 120 words for the body
- Mention ONE specific thing about their company (not generic)
- No buzzwords like "synergy", "leverage", "game-changing"
- End with ONE simple question (not "would you like to chat?")
- Tone: professional but human, not salesy
- Do NOT mention the lead score

Respond with ONLY valid JSON — no markdown:
{{
  "subject": "email subject line",
  "body": "full email body with line breaks as \\n"
}}"""


    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=400,
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)

        logger.info(f"[compose] Email written for {enriched.company_name}")
        return {
            "email_subject": data.get("subject"),
            "email_body": data.get("body"),
        }

    except Exception as e:
        logger.error(f"[compose] Failed: {e}")
        return {"email_subject": None, "email_body": None}
    
def deliver_node(state: AgentState) -> dict:
    scored = state.get("scored")
    enriched = state.get("enriched")

    if not enriched:
        output = LeadOutput(
            url=state["lead_input"].url,
            company_name=None,
            industry=None,
            location=None,
            company_size=None,
            contact_email=None,
            score=0,
            tier="cold",
            score_breakdown={},
            error=state.get("pipeline_error"),
        )
    
    else:
        output = LeadOutput(
            url = enriched.url,
            company_name=enriched.company_name,
            industry=enriched.industry,
            location=enriched.location,
            company_size=enriched.company_size,
            contact_email=enriched.contact_email,
            score=scored.score if scored else 0,
            tier=scored.tier if scored else "cold",
            score_breakdown=scored.score_breakdown if scored else {},
            email_subject=state.get("email_subject"),
            email_body=state.get("email_body"),
            error=state.get("pipeline_error"),
        )
    logger.info(
        f"[deliver] Packaged: {output.company_name} | "
        f"score={output.score} | tier={output.tier}"
    )
    return {"output": output}

        
