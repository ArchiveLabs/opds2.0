"""Abstract base class for data providers.

Data providers implement the logic for searching and retrieving publications.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import List, Optional
from pydantic import BaseModel

from pyopds2.models import Metadata, Publication, Link
from pyopds2.helpers import build_url


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


class Search(BaseModel, Mapping):
    query: str
    limit: int = 50
    offset: int = 0
    sort: Optional[str] = None

    def __iter__(self):
        """Allows **Search(...) to unpack into a dict for DataProvider.search(**s)"""
        return iter(self.model_dump())

    def __getitem__(self, item):
        return getattr(self, item)

    def __len__(self):
        return len(self.model_fields)
    
    @property
    def params(self) -> dict[str, str]:
        d = self.model_dump(exclude_none=True)
        return {k: str(v) for k, v in d.items()}


class SearchResponse(BaseModel):
    """Response from a search query."""
    provider: type["DataProvider"]
    search: Search
    records: List[DataProviderRecord]
    total: int

    @property
    def params(self) -> dict[str, str]:
        return self.search.params

    @property
    def limit(self) -> int:
        """Return limit from search."""
        return self.search.limit

    @property
    def page(self) -> int:
        """Calculate current page number based on offset and limit."""
        if self.search.limit <= 0: return 1
        return (self.search.offset // self.search.limit) + 1

    @property
    def last_page(self) -> int:
        """Calculate last page number based on total and limit."""
        if self.search.limit <= 0 or self.total == 0: return 1
        return (self.total + self.search.limit - 1) // self.search.limit

    @property
    def has_more(self) -> bool:
        """Determine if there are more results beyond the current page."""
        return (self.search.offset + self.search.limit) < self.total

    @property
    def title(self) -> str:
        """Return provider title."""
        return self.provider.TITLE

    def get_search_url(self, page: Optional[int] = None) -> str:
        """Build search URL with parameters.
        
        Args:
            page: Optional page number to override current page
        """
        params = self.params.copy()
        
        if page is not None:
            # Calculate offset for the requested page
            params['offset'] = str((page - 1) * self.search.limit)
        
        return build_url(
            f"{self.provider.BASE_URL}{self.provider.SEARCH_URL.split('{')[0]}",
            params
        )


class DataProvider(ABC):
    """Abstract base class for OPDS 2.0 data providers.

    Consumers of this library should extend this class to provide
    their own implementation for searching and retrieving publications.
    """

    TITLE: str = "Generic OPDS Service"
    BASE_URL: str = "http://localhost"
    SEARCH_URL: str = "/opds/search{?query}"

    @classmethod
    def search(
        cls,
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
            SearchResponse object containing search results
        """
        return SearchResponse(
            provider=cls,
            search=Search(query=query, limit=limit, offset=offset, sort=sort),
            records=[],
            total=0,
        )
