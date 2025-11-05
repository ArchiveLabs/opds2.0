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
from pyopds2 import Catalog, DataProvider, DataProviderRecord, Metadata, Link

class MyRecord(DataProviderRecord):
    def metadata(self):
        return Metadata(title="Example Book")
    def links(self):
        return [Link(href="/books/1", rel="self", type="application/epub+zip")]
    def images(self):
            return None

class MyProvider(DataProvider):
    @staticmethod
    def search(query, limit=50, offset=0, sort=None):
        records = [MyRecord()]
        # Return a list of MyRecord instances and total count
        return MyProvider.SearchResponse(
            MyProvider,
            records=records,
            total=len(records),
            query=query,
            limit=limit,
            offset=offset,
            sort=sort
        )

catalog = Catalog.create(MyProvider.search("example"))
catalog.model_dump_json()
```

See `examples/openlibrary.py` for a real-world integration with OpenLibrary.


### API Reference

#### Core Models

- **`Catalog`**: Represents an OPDS 2.0 catalog/feed
- **`Publication`**: Represents a publication (book, audiobook, etc.)
- **`Metadata`**: Metadata for catalogs and publications
- **`Link`**: Links to resources
- **`Contributor`**: Authors, illustrators, publishers, etc.
- **`Navigation`**: Navigation links for browsing

#### Catalog Functions

- **`Catalog()`**: Create a basic catalog
- **`Catalog.create()`**: Run a search and create a paginated Catalog from the search results

## Similar Implementations

This library was inspired by [The Palace Project's OPDS implementation](https://github.com/ThePalaceProject/circulation/blob/main/src/palace/manager/opds/opds2.py).

## License

AGPLv3 License. See `LICENSE` for details.
