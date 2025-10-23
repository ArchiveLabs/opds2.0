"""Abstract base class for data providers.

Data providers implement the logic for searching and retrieving publications.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from opds2.models import Metadata
from pydantic import BaseModel, Field
from typing import Optional


class DataProviderRecord(BaseModel, ABC):
    """Abstract base class for data records returned by DataProvider.
    
    Consumers of this library should extend this class to define
    their own data record structure.
    """

    @abstractmethod
    def metadata(self) -> Metadata:
        """Return DataProviderRecord as OPDS Metadata."""
        pass


class DataProvider(ABC):
    """Abstract base class for OPDS 2.0 data providers.
    
    Consumers of this library should extend this class to provide
    their own implementation for searching and retrieving publications.
    
    Example:
        class MyDataProvider(DataProvider):
            def search(self, query: str, limit: int = 50, offset: int = 0) -> List[Publication]:
                # Implement search logic
                results = my_search_function(query, limit, offset)
                return [self._to_publication(item) for item in results]
    """
    
    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[DataProviderRecord], int]:
        """Search for publications matching the query.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return (default: 50)
            offset: Offset for pagination (default: 0)
            
        Returns:
            List of Publication objects matching the search criteria
        """
        pass
