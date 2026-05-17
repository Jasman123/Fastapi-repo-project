"""
demo.py — Run a batch of sample tickets through the agent pipeline
          and render a rich terminal dashboard suitable for screenshots.

Usage:
    ANTHROPIC_API_KEY=sk-... python scripts/demo.py

    # Or with a real .env file:
    python scripts/demo.py
"""

import json
import os
import sys
import time
from unittest.mock import MagicMock, patch

# ── Add project root to path ──────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()

# ─────────────────────────────────────────────────────────────────────────────
# Sample tickets (no real API key needed — we mock the LLM)
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_TICKETS = [
    {
        "ticket_id":     "TKT-001",
        "customer_name": "Sarah Chen",
        "message":       "I was charged twice for my subscription this month. Please refund the duplicate charge.",
        "priority":      "high",
        "_mock_responses": [
            '{"category": "billing", "confidence": 0.94}',
            "Hi Sarah, I'm so sorry about the duplicate charge! I can see your account and will process a refund for the extra payment within 3–5 business days. You'll receive a confirmation email shortly.",
            '{"ok": true, "reason": "Clear, empathetic, actionable response with timeline."}',
        ],
    },
    {
        "ticket_id":     "TKT-002",
        "customer_name": "James Okafor",
        "message":       "The app keeps crashing on iOS 18 every time I try to open a document.",
        "priority":      "medium",
        "_mock_responses": [
            '{"category": "technical", "confidence": 0.91}',
            "Hi James, thanks for reporting this iOS 18 issue! Our engineering team is actively working on a fix. In the meantime, try force-closing the app and re-opening it. A patch will be released within 48 hours.",
            '{"ok": true, "reason": "Addresses the issue, provides workaround, sets expectations."}',
        ],
    },
    {
        "ticket_id":     "TKT-003",
        "customer_name": "Priya Sharma",
        "message":       "How do I reset my password? I can't find the button.",
        "priority":      "low",
        "_mock_responses": [
            '{"category": "account", "confidence": 0.97}',
            "Hi Priya! To reset your password, click 'Forgot Password' on the login screen and enter your email. You'll receive a reset link within a few minutes. Let me know if you need further help!",
            '{"ok": true, "reason": "Direct answer with clear steps."}',
        ],
    },
    {
        "ticket_id":     "TKT-004",
        "customer_name": "Marcus Webb",
        "message":       "Something weird happened with my account and I'm not sure what.",
        "priority":      "medium",
        "_mock_responses": [
            '{"category": "general", "confidence": 0.38}',  # Low → will escalate
        ],
    },
    {
        "ticket_id":     "TKT-005",
        "customer_name": "Lin Fang",
        "message":       "Can I use your API in a commercial product and what are the rate limits?",
        "priority":      "medium",
        "_mock_responses": [
            '{"category": "general", "confidence": 0.82}',
            "Hi Lin! Yes, you can use our API in commercial products under our Business tier. Rate limits depend on your plan — Starter is 100 req/min, Pro is 1,000 req/min. Check our pricing page for full details.",
            '{"ok": true, "reason": "Informative, links to further resources, appropriate for general category."}',
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Mock LLM so the demo runs without a real API key
# ─────────────────────────────────────────────────────────────────────────────

class _MockQueue:
    """Returns pre-baked responses in order for each ticket run."""
    def __init__(self):
        self._queue = []

    def load(self, responses: list[str]):
        self._queue = list(reversed(responses))  # pop from end

    def next(self) -> str:
        return self._queue.pop() if self._queue else '{"ok": true, "reason": "fallback"}'


_mock_queue = _MockQueue()


def _mock_get_llm_response(prompt: str, **kwargs) -> str:
    return _mock_queue.next()


# ─────────────────────────────────────────────────────────────────────────────
# Run pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_demo():
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]AI Customer Support Agent[/bold cyan]\n"
            "[dim]LangChain · LangGraph · FastAPI · GCP[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    from app.agents.support_graph import run_support_agent
    from app.models.schemas import SupportTicket

    results = []

    with patch("app.agents.support_graph.get_llm_response", side_effect=_mock_get_llm_response):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing tickets …", total=len(SAMPLE_TICKETS))

            for raw in SAMPLE_TICKETS:
                mock_responses = raw.pop("_mock_responses")
                _mock_queue.load(mock_responses)

                ticket = SupportTicket(**raw)
                time.sleep(0.3)  # simulate realistic latency in demo

                progress.update(task, description=f"Processing {ticket.ticket_id} …")
                result = run_support_agent(ticket)
                results.append((ticket, result))
                progress.advance(task)

    console.print()

    # ── Results table ─────────────────────────────────────────────────────────
    table = Table(
        title="[bold]Ticket Processing Results[/bold]",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold white on #1a1a2e",
        show_lines=True,
    )

    table.add_column("Ticket",    style="bold", width=9)
    table.add_column("Customer",  width=14)
    table.add_column("Category",  width=11)
    table.add_column("Conf",      width=6, justify="right")
    table.add_column("Action",    width=10)
    table.add_column("Graph Path",width=42)
    table.add_column("Time (ms)", width=10, justify="right")

    action_colors = {"answer": "green", "escalate": "yellow", "clarify": "blue"}
    category_icons = {
        "billing": "💳", "technical": "🔧", "account": "👤",
        "general": "💬", "escalation": "🚨",
    }

    for ticket, r in results:
        action_color = action_colors.get(r.action.value, "white")
        cat_icon     = category_icons.get(r.category.value, "")
        path         = " → ".join(r.node_trace)

        table.add_row(
            r.ticket_id,
            ticket.customer_name,
            f"{cat_icon} {r.category.value}",
            f"{r.confidence:.0%}",
            f"[{action_color}]{r.action.value.upper()}[/{action_color}]",
            f"[dim]{path}[/dim]",
            str(r.processing_time_ms),
        )

    console.print(table)
    console.print()

    # ── Summary stats ─────────────────────────────────────────────────────────
    total     = len(results)
    resolved  = sum(1 for _, r in results if r.action.value == "answer")
    escalated = total - resolved
    avg_conf  = sum(r.confidence for _, r in results) / total

    stats = Table.grid(padding=(0, 2))
    stats.add_column(justify="center")
    stats.add_column(justify="center")
    stats.add_column(justify="center")
    stats.add_column(justify="center")

    stats.add_row(
        Panel(f"[bold green]{total}[/bold green]\n[dim]Total Tickets[/dim]",    border_style="dim"),
        Panel(f"[bold green]{resolved}[/bold green]\n[dim]AI Resolved[/dim]",   border_style="green"),
        Panel(f"[bold yellow]{escalated}[/bold yellow]\n[dim]Escalated[/dim]",  border_style="yellow"),
        Panel(f"[bold cyan]{avg_conf:.0%}[/bold cyan]\n[dim]Avg Confidence[/dim]", border_style="cyan"),
    )

    console.print(stats)
    console.print()

    # ── Show one full answer ──────────────────────────────────────────────────
    answered = [(t, r) for t, r in results if r.answer]
    if answered:
        t, r = answered[0]
        console.print(
            Panel(
                f"[dim]Customer:[/dim] [bold]{t.customer_name}[/bold]\n"
                f"[dim]Message:[/dim]  {t.message}\n\n"
                f"[green]AI Answer:[/green]\n{r.answer}",
                title=f"[bold cyan]Sample Answer — {r.ticket_id}[/bold cyan]",
                border_style="green",
            )
        )
        console.print()

    # ── Graph topology ────────────────────────────────────────────────────────
    console.print(
        Panel(
            "[bold cyan]LangGraph Pipeline Topology[/bold cyan]\n\n"
            "  [START]\n"
            "     │\n"
            "     ▼\n"
            "  [cyan]classify_ticket[/cyan]          ← Node 1: LLM classifies category + confidence\n"
            "     │\n"
            "     ├─ conf < 0.55 ──► [yellow]escalate_ticket[/yellow]   ← Node 3: routed to human\n"
            "     │\n"
            "     └─ conf ≥ 0.55 ──► [green]generate_answer[/green]   ← Node 2: AI drafts reply\n"
            "                              │\n"
            "                              ▼\n"
            "                         [green]review_answer[/green]      ← Node 4: QA quality gate\n"
            "                              │\n"
            "                    ┌─────────┴───────────┐\n"
            "               pass │                     │ fail\n"
            "                    ▼                     ▼\n"
            "                  [END]           [yellow]escalate_ticket[/yellow]\n",
            title="[bold]Architecture[/bold]",
            border_style="cyan",
        )
    )

    console.print("[bold green]✓ Demo complete.[/bold green] Screenshot this terminal for your Upwork profile!\n")


if __name__ == "__main__":
    run_demo()
