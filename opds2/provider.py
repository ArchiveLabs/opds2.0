"""Abstract base class for data providers.

Data providers implement the logic for searching and retrieving publications.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel
from typing import Optional

from opds2.models import Metadata, Publication, Link, Catalog, Paginator
from opds2.catalog import create_catalog, add_pagination


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
    def create_catalog(
        cls,
        publications: List[Publication],
        identifier: str = "",
        title: Optional[str] = None,
        pagination: Optional[Paginator] = None
    ):
        """Create an OPDS catalog with optional pagination.
        
        Args:
            publications: List of publications to include in the catalog
            identifier: Optional unique identifier for the catalog
            title: Optional title for the catalog (defaults to cls.TITLE)
            pagination: Optional Paginator object for adding pagination links
            
        Returns:
            Catalog object with optional pagination
        """
        if title is None:
            title = cls.TITLE
            
        catalog = create_catalog(
            title=title,
            publications=publications,
            self_link=cls.CATALOG_URL,
            search_link=cls.SEARCH_URL,
            identifier=identifier
        )
        
        # Add pagination if provided
        if pagination is not None:
            params: dict[str, str] = {}
            
            # Add limit to params to preserve it in pagination links
            if pagination.limit:
                params["limit"] = str(pagination.limit)
            
            # Add sort parameter if provided
            if pagination.sort:
                params["sort"] = pagination.sort
            
            base_url = cls.SEARCH_URL.replace("{?query}", "")
            catalog = add_pagination(
                catalog=catalog,
                total=pagination.numfound or 0,
                limit=pagination.limit,
                offset=pagination.offset,
                base_url=base_url,
                params=params
            )
        
        return catalog

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
