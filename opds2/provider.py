"""Abstract base class for data providers.

Data providers implement the logic for searching and retrieving publications.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel

from opds2.models import Metadata, Publication, Link


class DataProviderRecord(BaseModel, ABC):
    """Abstract base class for data records returned by DataProvider.

    Consumers of this library should extend this class to define
    their own data record structure.
    """

    @abstractmethod
    def metadata(self) -> Metadata:
        """Return DataProviderRecord as OPDS Metadata."""
        pass

    @abstractmethod
    def links(self) -> List[Link]:
        """Return list of Links associated with this record."""
        pass

    @abstractmethod
    def images(self) -> Optional[List[Link]]:
        """Return list of Images associated with this record."""
        pass

    def to_publication(self) -> Publication:
        """Convert DataProviderRecord to OPDS Publication."""
        return Publication(
            metadata=self.metadata(),
            links=self.links(),
            images=self.images()
        )


@dataclass
class SearchRequest:
    """Request parameters for a search query."""
    query: str
    limit: int = 50
    offset: int = 0
    sort: Optional[str] = None


@dataclass
class SearchResponse:
    """Response from a search query."""
    records: List[DataProviderRecord]
    total: int
    request: SearchRequest

    @property
    def page(self) -> int:
        """Calculate current page number based on offset and limit."""
        limit = self.request.limit
        return (self.request.offset // limit) + 1 if limit else 1

    @property
    def last_page(self) -> int:
        """Calculate last page number based on total and limit."""
        return (self.total + self.request.limit - 1) // self.request.limit

    @property
    def has_more(self) -> bool:
        """Determine if there are more results beyond the current page."""
        req = self.request
        return (req.offset + req.limit) < self.total


class DataProvider(ABC):
    """Abstract base class for OPDS 2.0 data providers.

    Consumers of this library should extend this class to provide
    their own implementation for searching and retrieving publications.

    Example:
        class MyDataProvider(DataProvider):
            def search(
                self,
                query: str,
                limit: int = 50,
                offset: int = 0
            ) -> List[Publication]:
                # Implement search logic
                results = my_search_function(query, limit, offset)
                return [self._to_publication(item) for item in results]
    """

    TITLE: str = "Generic OPDS Service"

    BASE_URL: str = "http://localhost"
    """The base url for the data provider."""

    SEARCH_URL: str = "/opds/search{?query}"
    """The relative url template for search queries."""

    @staticmethod
    @abstractmethod
    def search(
        query: str,
        limit: int = 50,
        offset: int = 0,
        sort: Optional[str] = None,
    ) -> SearchResponse:
        """Search for publications matching the query.

        Args:
            query: Search query string
            limit: Maximum number of results to return (default: 50)
            offset: Offset for pagination (default: 0)
            sort: Optional sorting parameter

        Returns:
            List of Publication objects matching the search criteria
        """
        pass
