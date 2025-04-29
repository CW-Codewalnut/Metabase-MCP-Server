from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class DashboardCard:
    """
    Represents a card within a Metabase dashboard.
    
    Attributes:
        id (int): Use negative numbers to auto generate the ids 
            or use any unique value but,
            it must be unique within the dashboard
        card_id (int): The ID of the card/visualization
        row (int): The row position in the dashboard grid
        col (int): The column position in the dashboard grid
        size_x (int): The width of the card in grid units
        size_y (int): The height of the card in grid units
        parameter_mappings (List[Dict[str, Any]]): Parameter mappings for the card
    """
    id: int  # Use negative numbers to auto generate the ids
    card_id: int
    row: int
    col: int
    size_x: int
    size_y: int
    parameter_mappings: List[Dict[str, Any]] = field(default_factory=list)