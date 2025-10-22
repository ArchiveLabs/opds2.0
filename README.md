# opds2.0

A Python library for generating OPDS 2.0 compliant feeds using Pydantic and type hints.

Based on the [OPDS 2.0 specification](https://drafts.opds.io/opds-2.0).

## Features

- 🎯 **Type-safe**: Built with Pydantic for robust type checking and validation
- 📚 **OPDS 2.0 Compliant**: Implements core OPDS 2.0 structures (Catalog, Publication, Search)
- 🔍 **Search Support**: Abstract DataProvider class for implementing custom search
- 🗺️ **Flexible Mapping**: Separate data retrieval from OPDS feed generation with ItemMapping
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

Extend the `DataProvider` abstract class to implement your search logic. The new architecture separates data retrieval from OPDS feed generation:

```python
from opds2 import DataProvider, ItemMapping, SearchResult

class MyDataProvider(DataProvider):
    def search(self, query: str, page: int = 1, rows: int = 50) -> SearchResult:
        # Your search implementation here - returns raw data
        results = your_search_function(query, page=page, limit=rows)
        
        return SearchResult(
            items=results['docs'],          # Raw item dictionaries
            page=page,
            num_found=results['total'],     # Total matching items
            rows=rows
        )
    
    def get_item_mapping(self) -> ItemMapping:
        # Define how to map your raw data to OPDS fields
        return ItemMapping(
            title=lambda item: item.get("title"),
            author=lambda item: item.get("author_names", []),
            description=lambda item: item.get("description"),
            cover_url=lambda item: item.get("cover_url"),
            acquisition_link=lambda item: item.get("download_url"),
            acquisition_type=lambda item: "application/epub+zip",
        )
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
    page=1,
    rows=20,
    self_link="https://example.com/search?q=science+fiction"
)

# Export to JSON
json_output = search_results.model_dump_json()
```

## Architecture

The library uses a clean separation of concerns:

1. **DataProvider**: Retrieves raw data from your source (API, database, etc.)
   - `search()` returns `SearchResult` with raw items
   - `get_item_mapping()` defines field mappings

2. **ItemMapping**: Maps raw data fields to schema.org vocabulary
   - Uses lambda functions for flexible field extraction
   - Based on schema.org types (Book, Person, CreativeWork)
   - Supports legacy OPDS field names for backwards compatibility

3. **OPDS Generation**: The library handles conversion to OPDS format
   - Uses list comprehension to map items efficiently
   - Generates compliant OPDS 2.0 JSON-LD output

## Schema.org Integration

Field names are based on [schema.org](https://schema.org) vocabulary to promote interoperability and standardization. The library primarily uses types from:

- **[schema.org/Book](https://schema.org/Book)** - For publication metadata
- **[schema.org/Person](https://schema.org/Person)** - For authors and contributors  
- **[schema.org/CreativeWork](https://schema.org/CreativeWork)** - For general content properties

### Schema.org Fields

The library defines standard schema.org fields that can be mapped from your data:

| Schema.org Field | Type | Description | Legacy Name |
|-----------------|------|-------------|-------------|
| `name` | Text | Title of the publication | `title` |
| `identifier` | Text/URL | Unique identifier (ISBN, URI) | `identifier` |
| `description` | Text | Description or summary | `description` |
| `inLanguage` | Text/List | Language code(s) | `language` |
| `author` | Person/List | Author(s) | `author` |
| `publisher` | Organization/List | Publisher(s) | `publisher` |
| `datePublished` | Date | Publication date | `published` |
| `dateModified` | Date | Last modification date | `modified` |
| `image` | URL | Cover image URL | `cover_url` |
| `thumbnailUrl` | URL | Thumbnail image URL | `thumbnail_url` |
| `url` | URL | Resource URL | `acquisition_link` |
| `encodingFormat` | Text | MIME type | `acquisition_type` |
| `about` | Text/List | Subject matter | `subject` |
| `keywords` | Text/List | Keywords/tags | - |
| `genre` | Text | Genre | - |

### Backwards Compatibility

Legacy field names (e.g., `title`, `cover_url`, `acquisition_link`) are still supported and automatically mapped to their schema.org equivalents:

```python
# Both of these work identically:

# Using schema.org field names (recommended)
ItemMapping(
    name=lambda item: item.get("title"),
    image=lambda item: item.get("cover")
)

# Using legacy field names (backwards compatible)
ItemMapping(
    title=lambda item: item.get("title"),  # Mapped to 'name'
    cover_url=lambda item: item.get("cover")  # Mapped to 'image'
)
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
      ],
      "images": [
        {
          "href": "https://example.com/covers/pride.jpg",
          "type": "image/jpeg",
          "rel": "http://opds-spec.org/image"
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

### Type Definitions

- **`SearchResult`**: Standardized search result container with pagination info
- **`ItemMapping`**: Field mapping configuration using schema.org vocabulary
- **`SCHEMA_ORG_FIELDS`**: Dictionary of schema.org field definitions
- **`OPDS_RESERVED_FIELDS`**: Legacy field name mappings (for backwards compatibility)

### Helper Functions

- **`create_catalog()`**: Create a basic catalog with optional search
- **`create_search_catalog()`**: Create a catalog from search results

### Abstract Classes

- **`DataProvider`**: Extend this to implement your search logic
  - `search()` - Return SearchResult with raw data
  - `get_item_mapping()` - Define field mappings

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Running the Examples

```bash
# Basic usage example
python examples/basic_usage.py

# OpenLibrary integration example
python examples/openlibrary_example.py
```

## Examples

The repository includes two complete examples:

1. **`examples/basic_usage.py`** - Simple in-memory book provider
2. **`examples/openlibrary_example.py`** - Real-world Open Library API integration

## Inspiration

This library was inspired by [The Palace Project's OPDS implementation](https://github.com/ThePalaceProject/circulation/blob/main/src/palace/manager/opds/opds2.py).

## License

Apache-2.0

