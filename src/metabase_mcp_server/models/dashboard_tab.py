from dataclasses import dataclass
from typing import Optional

@dataclass
class DashboardTab:
    """
    Represents a tab within a Metabase dashboard.
    
    Attributes:
        id (Optional[int]): The tab ID, optional for new tabs
        name (str): The name of the tab
    """
    id: Optional[int] = None
    name: str = "" 