import asyncio
from datetime import datetime
from functools import lru_cache
import gspread
from google.oauth2.service_account import Credentials

from app.schemas.lead import LeadOutput
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

HEADERS = [
    "Date",
    "Company",
    "Industry",
    "Location",
    "Size",
    "Score",
    "Tier",
    "Contact Email",
    "Email Subject",
    "URL",
    "Score Breakdown",
    "Alert Sent",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@lru_cache
def _get_client() -> gspread.Client:
    """Singleton gspread client — created once."""
    settings = get_settings()
    creds = Credentials.from_service_account_file(
        settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def _get_sheet():
    settings = get_settings()
    client = _get_client()
    spreadsheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
    return spreadsheet.sheet1

def _ensure_headers(sheet) -> None:
    try:
        first_row = sheet.row_values(1)
        if not first_row:
            sheet.insert_row(HEADERS, index=1)
            logger.info("Wrote header row to Google sheet")
    except Exception as e:
        logger.warning(f"Could not check/write headers: {e}")

async def append_lead_to_sheet(output: LeadOutput) -> int:
    
    def _sync_append():
        sheet = _get_sheet()
        _ensure_headers(sheet)

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            output.company_name or "",
            output.industry or "",
            output.location or "",
            output.company_size or "",
            output.score,
            output.tier.upper(),
            output.contact_email or "",
            output.email_subject or "",
            output.url,
            str(output.score_breakdown),
            "Yes" if output.alert_sent else "No",
        ]

        sheet.append_row(row, value_input_option="USER_ENTERED")

        return len(sheet.get_all_values())

    loop = asyncio.get_event_loop()
    row_num = await loop.run_in_executor(None, _sync_append)
    logger.info(f"Appended lead to Google Sheet: row {row_num}")
    return row_num
