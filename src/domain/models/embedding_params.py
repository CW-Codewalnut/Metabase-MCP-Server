from dataclasses import dataclass
from typing import Optional

@dataclass
class EmbeddingParams:
    """
    Represents embedding parameters for Metabase dashboards.

    Attributes:
        url (Optional[str]): The embedding URL
        custom_css (Optional[str]): Custom CSS for the embedded view
    """
    url: Optional[str] = None
    custom_css: Optional[str] = None
