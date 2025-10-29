# opds2.0

A Python library for generating OPDS (Open Publication Distribution System) 2.0 compliant feeds using Pydantic and type hints.

Based on the [OPDS 2.0 specification](https://drafts.opds.io/opds-2.0).

## Installation

This package is not yet on PyPI. Install directly from GitHub:

```bash
pip install git+https://github.com/ArchiveLabs/opds2.0.git
```

## Running Tests
```bash
pytest tests/ -v
```

## Developer's Guide

To use this library, you must implement two key classes:

- **DataProvider**: Defines how to search and retrieve records. You must subclass and implement the `search` method.
- **DataProviderRecord**: Defines the structure of a single record in your catalog. You must subclass and implement the `metadata`, `links`, and `images` methods.

### Example

```python
from opds2.catalog import add_pagination
from opds2 import Paginator
from pyopds2_openlibrary import OpenLibraryDataProvider

# Get search results from any data provider
records, num_found = OpenLibraryDataProvider.search(query="python", limit=10)

# Create paginated catalog with publications
catalog = OpenLibraryDataProvider.create_catalog(
    publications=[record.to_publication() for record in records],
    pagination=Paginator(
        limit=10,
        offset=0,
        numfound=num_found
    )
)

# Or manually add pagination to any catalog
catalog = add_pagination(
    catalog=OpenLibraryDataProvider.create_catalog(
        publications=[record.to_publication() for record in records]
    ),
    total=num_found,
    limit=10,
    offset=0,
    base_url="/opds/search",
    params={"query": "python", "limit": "10"}
)
```

For a real-world integration example, see the [pyopds2_openlibrary](https://github.com/ArchiveLabs/pyopds2_openlibrary) package, which provides an OpenLibrary data provider implementation.


### API Reference

#### Core Models

- **`Catalog`**: Represents an OPDS 2.0 catalog/feed
- **`Publication`**: Represents a publication (book, audiobook, etc.)
- **`Metadata`**: Metadata for catalogs and publications
- **`Link`**: Links to resources
- **`Contributor`**: Authors, illustrators, publishers, etc.
- **`Navigation`**: Navigation links for browsing
- **`Paginator`**: Pagination parameters for catalogs

#### Catalog Functions

- **`create_catalog()`**: Create a basic catalog with optional search
- **`create_search_catalog()`**: Create a catalog from search results
- **`add_pagination()`**: Add pagination links and metadata to a catalog

## Similar Implementations

This library was inspired by [The Palace Project's OPDS implementation](https://github.com/ThePalaceProject/circulation/blob/main/src/palace/manager/opds/opds2.py).

## License

AGPLv3 License. See `LICENSE` for details.