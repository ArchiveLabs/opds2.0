# opds2.0

A Python library for generating OPDS 2.0 compliant feeds using Pydantic and type hints.

Based on the [OPDS 2.0 specification](https://drafts.opds.io/opds-2.0).

## Features

- 🎯 **Type-safe**: Built with Pydantic for robust type checking and validation
- 📚 **OPDS 2.0 Compliant**: Implements core OPDS 2.0 structures (Catalog, Publication, Search)
- 🔍 **Search Support**: Abstract DataProvider class for implementing custom search
- 🚀 **Easy to Use**: Simple API for creating catalogs and feeds
- ✅ **Tested**: Comprehensive test suite included

## Installation

```bash
pip install opds2
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Create a DataProvider

Extend the `DataProvider` abstract class to implement your search logic:

```python
from opds2 import DataProvider, Publication, Metadata, Link, Contributor
from typing import List

class MyDataProvider(DataProvider):
    def search(self, query: str, limit: int = 50, offset: int = 0) -> List[Publication]:
        # Your search implementation here
        results = your_search_function(query, limit, offset)
        
        # Convert to Publication objects
        publications = []
        for item in results:
            metadata = Metadata(
                title=item.title,
                author=[Contributor(name=item.author, role="author")],
                language=[item.language]
            )
            links = [Link(
                href=item.url,
                type="application/epub+zip",
                rel="http://opds-spec.org/acquisition"
            )]
            publications.append(Publication(metadata=metadata, links=links))
        
        return publications
```

### 2. Create a Catalog

```python
from opds2 import create_catalog

catalog = create_catalog(
    title="My Library",
    self_link="https://example.com/catalog",
    search_link="https://example.com/search?q={searchTerms}",
    identifier="urn:uuid:my-catalog-001"
)

# Export to JSON
json_output = catalog.model_dump_json()
```

### 3. Create a Search Feed

```python
from opds2 import create_search_catalog

provider = MyDataProvider()

search_results = create_search_catalog(
    provider=provider,
    query="science fiction",
    limit=20,
    self_link="https://example.com/search?q=science+fiction"
)

# Export to JSON
json_output = search_results.model_dump_json()
```

## Example Output

```json
{
  "@context": "https://readium.org/webpub-manifest/context.jsonld",
  "metadata": {
    "title": "Search results for \"Pride\"",
    "modified": "2024-01-01T12:00:00+00:00",
    "numberOfItems": 1
  },
  "links": [
    {
      "href": "https://example.com/search?q=Pride",
      "type": "application/opds+json",
      "rel": "self"
    }
  ],
  "publications": [
    {
      "metadata": {
        "title": "Pride and Prejudice",
        "language": ["en"],
        "description": "A romantic novel of manners",
        "author": [
          {
            "name": "Jane Austen",
            "role": "author"
          }
        ]
      },
      "links": [
        {
          "href": "https://example.com/books/pride-prejudice.epub",
          "type": "application/epub+zip",
          "rel": "http://opds-spec.org/acquisition"
        }
      ]
    }
  ]
}
```

## API Reference

### Core Models

- **`Catalog`**: Represents an OPDS 2.0 catalog/feed
- **`Publication`**: Represents a publication (book, audiobook, etc.)
- **`Metadata`**: Metadata for catalogs and publications
- **`Link`**: Links to resources
- **`Contributor`**: Authors, illustrators, publishers, etc.
- **`Navigation`**: Navigation links for browsing

### Helper Functions

- **`create_catalog()`**: Create a basic catalog with optional search
- **`create_search_catalog()`**: Create a catalog from search results

### Abstract Classes

- **`DataProvider`**: Extend this to implement your search logic

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Running the Example

```bash
python examples/basic_usage.py
```

## Inspiration

This library was inspired by [The Palace Project's OPDS implementation](https://github.com/ThePalaceProject/circulation/blob/main/src/palace/manager/opds/opds2.py).

## License

Apache-2.0

