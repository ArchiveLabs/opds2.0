"""OPDS 2.0 Feed Generator Library

A Python library for generating OPDS 2.0 compliant feeds using Pydantic.
Based on the OPDS 2.0 specification at https://drafts.opds.io/opds-2.0
"""

__version__ = "0.1.0"

from opds2.catalog import create_catalog, create_search_catalog
from opds2.models import (
    Catalog,
    Contributor,
    Link,
    Metadata,
    Publication,
)
from opds2.provider import DataProvider
from opds2.types import (
    ItemMapping,
    OPDS_RESERVED_FIELDS,
    SCHEMA_ORG_FIELDS,
    SearchResult,
)

__all__ = [
    "Catalog",
    "Contributor",
    "DataProvider",
    "ItemMapping",
    "Link",
    "Metadata",
    "OPDS_RESERVED_FIELDS",
    "Publication",
    "SCHEMA_ORG_FIELDS",
    "SearchResult",
    "create_catalog",
    "create_search_catalog",
]
