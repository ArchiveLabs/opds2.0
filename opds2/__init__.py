"""OPDS 2.0 Feed Generator Library

A Python library for generating OPDS 2.0 compliant feeds using Pydantic.
Based on the OPDS 2.0 specification at https://drafts.opds.io/opds-2.0
"""

__version__ = "0.1.0"

from opds2.catalog import create_catalog, create_search_catalog, add_pagination
from opds2.models import (
    Catalog,
    Contributor,
    Link,
    Metadata,
    Navigation,
    Paginator,
    Publication,
)
from opds2.provider import DataProvider, DataProviderRecord

__all__ = [
    "add_pagination",
    "create_catalog",
    "create_search_catalog",
    "Catalog",
    "Contributor",
    "DataProvider",
    "DataProviderRecord",
    "Link",
    "Metadata",
    "Navigation",
    "Paginator",
    "Publication",
]
