"""
Domain exceptions — raised by services/agent, caught by API layer.
Never import FastAPI here; this ring has zero framework dependencies.
"""


class ResearchAgentError(Exception):
    """Base for all domain errors."""


class PlanningError(ResearchAgentError):
    """LLM failed to generate a valid research plan."""


class SearchError(ResearchAgentError):
    """All search queries failed."""


class ExtractionError(ResearchAgentError):
    """Structured extraction from search results failed."""


class SynthesisError(ResearchAgentError):
    """Report synthesis or generation failed."""


class ReportNotFoundError(ResearchAgentError):
    """Requested report ID does not exist in the database."""


class AuthError(ResearchAgentError):
    """Invalid or missing API key."""