"""Abstract base class for data providers.

Data providers implement the logic for searching and retrieving publications.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import functools
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

    TITLE: str = "Generic OPDS Service"

    BASE_URL: str = "http://localhost"
    """The base url for the data provider."""

    SEARCH_URL: str = "/opds/search{?query}"
    """The relative url template for search queries."""

    @dataclass
    class SearchResponse:
        """Response from a search query."""
        provider: 'DataProvider | type[DataProvider]'
        query: str
        limit: int
        offset: int
        sort: Optional[str]
        records: List[DataProviderRecord]
        total: int

        def get_search_url(self, **kwargs: str) -> str:
            base_url = self.provider.SEARCH_URL.replace("{?query}", "")
            if base_url.startswith("/"):
                base_url = self.provider.BASE_URL.rstrip('/') + base_url
            return build_url(base_url, params=self.params | kwargs)

        @functools.cached_property
        def params(self) -> dict:
            p: dict[str, str] = {}
            if self.query:
                p["query"] = self.query
            if self.limit:
                p["limit"] = str(self.limit)
            if self.page > 1:
                p["page"] = str(self.page)
            if self.sort:
                p["sort"] = self.sort
            return p

        @property
        def page(self) -> int:
            """Calculate current page number based on offset and limit."""
            return (self.offset // self.limit) + 1 if self.limit else 1

        @property
        def last_page(self) -> int:
            """Calculate last page number based on total and limit."""
            return (self.total + self.limit - 1) // self.limit

        @property
        def has_more(self) -> bool:
            """Determine if there are more results beyond the current page."""
            return (self.offset + self.limit) < self.total

    @staticmethod
    @abstractmethod
    def search(
        query: str,
        limit: int = 50,
        offset: int = 0,
        sort: Optional[str] = None,
    ) -> 'DataProvider.SearchResponse':
        """Search for publications matching the query.

        Args:
            query: Search query string
            limit: Maximum number of results to return (default: 50)
            offset: Offset for pagination (default: 0)
            sort: Optional sorting parameter

        Returns:
            SearchResponse object containing search results
        """
        return DataProvider.SearchResponse(
            DataProvider,
            records=[],
            total=0,
            query=query,
            limit=limit,
            offset=offset,
            sort=sort
        )
