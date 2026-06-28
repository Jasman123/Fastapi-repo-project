"""
services/email_service.py
--------------------------
SMTP email alert for hot leads (score >= threshold).
Uses standard smtplib — no third-party email SDK needed.
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.schemas.lead import LeadOutput
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_alert_email(output: LeadOutput) -> MIMEMultipart:
    """Builds the HTML alert email for a hot lead."""
    settings = get_settings()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔥 Hot Lead ({output.score}/100): {output.company_name or output.url}"
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.ALERT_RECIPIENT

    # Plain text fallback
    plain = f"""
HOT LEAD ALERT — Score: {output.score}/100

Company:  {output.company_name or 'Unknown'}
Industry: {output.industry or 'Unknown'}
Location: {output.location or 'Unknown'}
Email:    {output.contact_email or 'Not found'}
URL:      {output.url}

Score breakdown: {output.score_breakdown}

--- DRAFTED EMAIL ---
Subject: {output.email_subject or 'N/A'}

{output.email_body or 'No email generated'}
"""

    # HTML version
    score_color = "#16a34a" if output.score >= 70 else "#d97706"
    html = f"""
<html><body style="font-family:sans-serif;max-width:600px;margin:auto">
  <div style="background:#f0fdf4;border:2px solid #16a34a;border-radius:8px;padding:20px">
    <h2 style="color:#15803d;margin:0">🔥 Hot Lead — {output.score}/100</h2>
    <p style="color:#166534">{output.company_name or output.url}</p>
  </div>
  <table style="width:100%;border-collapse:collapse;margin-top:16px">
    <tr><td style="padding:8px;color:#6b7280;width:140px">Industry</td>
        <td style="padding:8px;font-weight:500">{output.industry or '—'}</td></tr>
    <tr style="background:#f9fafb">
        <td style="padding:8px;color:#6b7280">Location</td>
        <td style="padding:8px">{output.location or '—'}</td></tr>
    <tr><td style="padding:8px;color:#6b7280">Contact Email</td>
        <td style="padding:8px;color:#2563eb">{output.contact_email or 'Not found'}</td></tr>
    <tr style="background:#f9fafb">
        <td style="padding:8px;color:#6b7280">Score</td>
        <td style="padding:8px;font-weight:700;color:{score_color}">{output.score}/100</td></tr>
    <tr><td style="padding:8px;color:#6b7280">URL</td>
        <td style="padding:8px"><a href="{output.url}">{output.url}</a></td></tr>
  </table>
  <div style="margin-top:24px;background:#fefce8;border:1px solid #fde047;
              border-radius:8px;padding:16px">
    <p style="font-weight:600;margin:0 0 8px;color:#854d0e">Drafted outreach email</p>
    <p style="font-size:13px;color:#713f12;margin:0 0 4px">
      <strong>Subject:</strong> {output.email_subject or 'N/A'}
    </p>
    <hr style="border:none;border-top:1px solid #fde047;margin:8px 0">
    <p style="font-size:13px;white-space:pre-line;color:#1c1917">
{output.email_body or 'No email generated'}
    </p>
  </div>
</body></html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


async def send_hot_lead_alert(output: LeadOutput) -> None:
    """
    Sends an email alert for a hot lead via SMTP.
    Runs synchronous smtplib in thread pool to avoid blocking.
    """
    settings = get_settings()

    if not settings.SMTP_USER or not settings.ALERT_RECIPIENT:
        logger.warning("SMTP not configured — skipping email alert")
        return

    def _sync_send():
        msg = _build_alert_email(output)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.SMTP_USER,
                settings.ALERT_RECIPIENT,
                msg.as_string(),
            )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_send)
    logger.info(f"Alert email sent for {output.company_name} to {settings.ALERT_RECIPIENT}")