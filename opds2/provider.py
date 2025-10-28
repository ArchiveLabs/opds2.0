"""Abstract base class for data providers.

Data providers implement the logic for searching and retrieving publications.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlencode

from pydantic import BaseModel
from typing import Optional

from opds2.models import Metadata, Publication, Link, Catalog
from opds2.catalog import create_catalog


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
    URL: str = "http://localhost/"
    CATALOG_URL: str = "/opds/catalog"
    SEARCH_URL: str = "/opds/search{?query}"
    
    @classmethod
    def create_catalog(cls, publications: List[Publication], identifier=""):
        return create_catalog(
            title=cls.TITLE,
            publications=publications,
            self_link=cls.CATALOG_URL,
            search_link=cls.SEARCH_URL,
            identifier=identifier
        )

    @staticmethod
    @abstractmethod
    def search(
        query: str,
        limit: int = 50,
        offset: int = 0,
        sort: Optional[str] = None,
    ) -> tuple[List[DataProviderRecord], int]:
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

    def search_catalog(
        self,
        title: Optional[str] = None,
        query: str = "",
        limit: int = 50,
        offset: int = 0,
        sort: Optional[str] = None,
    ) -> Catalog:
        """
        Search for publications and return an OPDS Catalog.

        Args:
            title: Optional title for the catalog
            query: Search query string
            limit: Maximum number of results to return (default: 50)
            offset: Offset for pagination (default: 0)
            sort: Optional sorting parameter
        """

        if not title:
            title = f"Search results for '{query}'"
        results, total = self.search(
            query=query,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        page = (offset // limit) + 1 if limit else 1
        publications = [record.to_publication() for record in results]
        params: dict[str, str] = {}
        if query:
            params["query"] = query
        if limit:
            params["limit"] = str(limit)
        if page > 1:
            params["page"] = str(page)
        if sort:
            params["sort"] = sort
        
        links: list[Link] = []
        base_url = self.SEARCH_URL.replace("{?query}", "")

        self_url = base_url + ("?" + urlencode(params) if params else "")
        links.append(
            Link(
                rel="self",
                href=self_url,
                type="application/opds+json",
            )
        )
        links.append(
            Link(
                rel="first",
                href=base_url + "?" + urlencode(params | {"page": "1"}),
                type="application/opds+json",
            )
        )

        if page > 1:
            links.append(
                Link(
                    rel="previous",
                    href=base_url + "?" + urlencode(params | {"page": str(page - 1)}),
                    type="application/opds+json",
                )
            )

        has_more = (offset + limit) < total
        if has_more:
            links.append(
                Link(
                    rel="next",
                    href=base_url + "?" + urlencode(params | {"page": str(page + 1)}),
                    type="application/opds+json",
                )
            )
            last_page = (total + limit - 1) // limit
            links.append(
                Link(
                    rel="last",
                    href=base_url + "?" + urlencode(params | {"page": str(last_page)}),
                    type="application/opds+json",
                )
            )

        return Catalog(
            metadata=Metadata(
                title=title,
                numberOfItems=total,
                itemsPerPage=limit,
                currentPage=page,
            ),
            publications=publications,
            links=links,
        )
