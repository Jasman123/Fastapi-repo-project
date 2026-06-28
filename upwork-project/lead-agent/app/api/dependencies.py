from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)


def get_settings_dep():
    return get_settings()
