"""Abstract base class for data providers.

Data providers implement the logic for searching and retrieving publications.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from opds2.types import SearchResult, ItemMapping


class DataProvider(ABC):
    """Abstract base class for OPDS 2.0 data providers.
    
    Consumers of this library should extend this class to provide
    their own implementation for searching and retrieving data.
    
    The DataProvider separates data retrieval from OPDS feed generation:
    - search() retrieves raw data and returns SearchResult
    - get_item_mapping() defines how to map raw items to OPDS fields
    
    Example:
        class MyDataProvider(DataProvider):
            def search(self, query: str, page: int = 1, rows: int = 50) -> SearchResult:
                results = my_api.search(query, page=page, limit=rows)
                return SearchResult(
                    items=results['docs'],
                    page=page,
                    num_found=results['numFound'],
                    rows=rows
                )
            
            def get_item_mapping(self) -> ItemMapping:
                return ItemMapping(
                    title=lambda item: item.get("title"),
                    author=lambda item: item.get("author_name", []),
                    # ... more field mappings
                )
    """

    @abstractmethod
    def search(
        self,
        query: str,
        page: int = 1,
        rows: int = 50,
    ) -> SearchResult:
        """Search for items matching the query.
        
        Args:
            query: Search query string
            page: Page number (1-indexed, default: 1)
            rows: Number of items per page (default: 50)
            
        Returns:
            SearchResult containing items, pagination info, and total count
        """
        pass
    
    @abstractmethod
    def get_item_mapping(self) -> ItemMapping:
        """Get the mapping configuration for converting items to OPDS fields.
        
        Returns:
            ItemMapping that defines how to extract OPDS fields from raw items
        """
        pass
