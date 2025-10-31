"""OPDS 2.0 data models using Pydantic.

Based on the OPDS 2.0 specification and Web Publication Manifest.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from urllib.parse import urlencode

from pydantic import BaseModel, Field # field_validator


if TYPE_CHECKING:
    from opds2.provider import DataProvider, SearchResponse


class Link(BaseModel):
    """Represents a link in OPDS 2.0.
    
    Links are used to associate resources with a publication or catalog.
    """
    href: str = Field(..., description="URI or URI template of the linked resource")
    type: Optional[str] = Field(None, description="MIME type of the linked resource")
    rel: Optional[str] = Field(None, description="Relation between resource and parent")
    title: Optional[str] = Field(None, description="Title of the link")
    templated: Optional[bool] = Field(None, description="Indicates the href is a URI template")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional properties")

    model_config = {"extra": "allow"}


class Contributor(BaseModel):
    """Represents a contributor (author, illustrator, etc.)."""
    name: str = Field(..., description="Name of the contributor")
    identifier: Optional[str] = Field(None, description="Unique identifier for the contributor")
    sort_as: Optional[str] = Field(None, alias="sortAs", description="String to use for sorting")
    role: Optional[str] = Field(None, description="Role of the contributor")
    links: Optional[List[Link]] = Field(None, description="Links associated with the contributor")

    model_config = {"populate_by_name": True, "extra": "allow"}


class Metadata(BaseModel):
    """Metadata for a publication or catalog.
    
    Contains descriptive information about the resource.
    """
    title: str = Field(..., description="Title of the resource")
    identifier: Optional[str] = Field(None, alias="@id", description="Unique identifier")
    type: Optional[str] = Field(None, alias="@type", description="Type of the resource")
    modified: Optional[datetime] = Field(None, description="Last modification date")
    published: Optional[datetime] = Field(None, description="Publication date")
    language: Optional[List[str]] = Field(None, description="Language codes")
    description: Optional[str] = Field(None, description="Description of the resource")
    author: Optional[List[Contributor]] = Field(None, description="Authors")
    illustrator: Optional[List[Contributor]] = Field(None, description="Illustrators")
    translator: Optional[List[Contributor]] = Field(None, description="Translators")
    editor: Optional[List[Contributor]] = Field(None, description="Editors")
    publisher: Optional[List[Contributor]] = Field(None, description="Publishers")
    subject: Optional[List[str]] = Field(None, description="Subject tags")
    numberOfItems: Optional[int] = Field(None, description="Number of items in collection")

    model_config = {"populate_by_name": True, "extra": "allow"}


class Publication(BaseModel):
    """Represents a publication in OPDS 2.0.
    
    A publication is a digital work (book, audiobook, etc.) with metadata and links.
    """
    metadata: Metadata = Field(..., description="Metadata about the publication")
    links: List[Link] = Field(default_factory=list, description="Links to resources")
    images: Optional[List[Link]] = Field(None, description="Cover images and thumbnails")

    model_config = {"extra": "allow"}

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Export to dict, filtering None values."""
        kwargs.setdefault('exclude_none', True)
        data = super().model_dump(**kwargs)
        return {k: v for k, v in data.items() if v is not None}


class Navigation(BaseModel):
    """Navigation link in a catalog."""
    href: str = Field(..., description="URI of the navigation target")
    title: str = Field(..., description="Title of the navigation item")
    type: Optional[str] = Field(None, description="MIME type")
    rel: Optional[str] = Field(None, description="Relation type")

    model_config = {"extra": "allow"}


class Catalog(BaseModel):
    """Represents an OPDS 2.0 catalog/feed.
    
    A catalog is a collection of publications with optional navigation.
    """
    metadata: Metadata = Field(..., description="Metadata about the catalog")
    links: List[Link] = Field(default_factory=list, description="Links (self, search, etc.)")
    publications: Optional[List[Publication]] = Field(
        None, 
        description="List of publications in this catalog"
    )
    navigation: Optional[List[Navigation]] = Field(
        None,
        description="Navigation links for browsing"
    )
    groups: Optional[List['Catalog']] = Field(
        None,
        description="Grouped collections of publications"
    )
    facets: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Facets for filtering catalog"
    )

    model_config = {"extra": "allow"}

    #@field_validator("links", mode="before")
    @classmethod
    def ensure_self_link(cls, v: List[Link]) -> List[Link]:
        """Ensure there's at least a structure for links."""
        if v is None:
            return []
        return v

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Export to dict, filtering None values."""
        kwargs.setdefault('exclude_none', True)
        data = super().model_dump(**kwargs)
        # Add JSON-LD context
        result = {
            "@context": "https://readium.org/webpub-manifest/context.jsonld",
        }
        # Filter out None values
        for key, value in data.items():
            if value is not None:
                result[key] = value
        return result

    def model_dump_json(self, **kwargs) -> str:
        """Export to JSON string with proper formatting."""
        import json
        # Use model_dump to get the dict with @context, then serialize to JSON
        data = self.model_dump(**kwargs)
        return json.dumps(data, default=str)

    @staticmethod
    def create(
        provider: 'DataProvider',

        # Catalog properties
        metadata: Metadata | None = None,
        links: list[Link] | None = None,
        publications: list[Publication] | None = None,
        navigation: list[Navigation] | None = None,
        groups: list['Catalog'] | None = None,
        facets: list[dict[str, Any]] | None = None,
        search: 'SearchResponse | None' = None,
    ) -> 'Catalog':
        """
        Search for publications and return an OPDS Catalog.

        Args:
            search: SearchResponse from DataProvider to convert to publication/etc.
        """

        metadata = metadata or Metadata()
        links = links or []

        if search:
            req = search.request
            if publications:
                raise ValueError("Unexpected publication with query")

            publications = [record.to_publication() for record in search.records]
            params: dict[str, str] = {}
            if req.query:
                params["query"] = req.query
            if req.limit:
                params["limit"] = str(req.limit)
            if search.page > 1:
                params["page"] = str(search.page)
            if req.sort:
                params["sort"] = req.sort

            metadata.numberOfItems = search.total
            metadata.itemsPerPage = req.limit
            metadata.currentPage = search.page

            base_url = provider.SEARCH_URL.replace("{?query}", "")
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

            if search.page > 1:
                links.append(
                    Link(
                        rel="previous",
                        href=base_url + "?" + urlencode(params | {"page": str(search.page - 1)}),
                        type="application/opds+json",
                    )
                )

            if search.has_more:
                links.append(
                    Link(
                        rel="next",
                        href=base_url + "?" + urlencode(params | {"page": str(search.page + 1)}),
                        type="application/opds+json",
                    )
                )
                links.append(
                    Link(
                        rel="last",
                        href=base_url + "?" + urlencode(params | {"page": str(search.last_page)}),
                        type="application/opds+json",
                    )
                )

        return Catalog(
            metadata=metadata,
            links=links,
            publications=publications,
            navigation=navigation,
            groups=groups,
            facets=facets,
        )
