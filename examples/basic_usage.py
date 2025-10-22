"""Example usage of the OPDS 2.0 library.

This example demonstrates:
1. Creating a custom DataProvider
2. Generating a catalog with search capability
3. Performing searches and generating search result catalogs
"""

import json
from typing import List

from opds2 import (
    Catalog,
    Contributor,
    DataProvider,
    Link,
    Metadata,
    Publication,
    create_catalog,
    create_search_catalog,
)


class SimpleBookProvider(DataProvider):
    """A simple data provider with a small book collection."""

    def __init__(self):
        # Sample book data
        self.books = [
            {
                "title": "Pride and Prejudice",
                "author": "Jane Austen",
                "language": "en",
                "description": "A romantic novel of manners",
                "url": "https://example.com/books/pride-prejudice.epub",
            },
            {
                "title": "Moby Dick",
                "author": "Herman Melville",
                "language": "en",
                "description": "The saga of Captain Ahab",
                "url": "https://example.com/books/moby-dick.epub",
            },
            {
                "title": "The Odyssey",
                "author": "Homer",
                "language": "en",
                "description": "Ancient Greek epic poem",
                "url": "https://example.com/books/odyssey.epub",
            },
        ]

    def search(self, query: str, limit: int = 50, offset: int = 0) -> List[Publication]:
        """Search books by title or author."""
        query_lower = query.lower()
        results = [
            book
            for book in self.books
            if query_lower in book["title"].lower()
            or query_lower in book["author"].lower()
        ]

        # Apply pagination
        results = results[offset : offset + limit]

        # Convert to Publication objects
        publications = []
        for book in results:
            metadata = Metadata(
                title=book["title"],
                author=[Contributor(name=book["author"], role="author")],
                language=[book["language"]],
                description=book["description"],
            )
            links = [
                Link(
                    href=book["url"],
                    type="application/epub+zip",
                    rel="http://opds-spec.org/acquisition",
                )
            ]
            publications.append(Publication(metadata=metadata, links=links))

        return publications


def main():
    """Run example demonstrations."""
    print("=" * 80)
    print("OPDS 2.0 Library Example")
    print("=" * 80)
    print()

    # Create a data provider
    provider = SimpleBookProvider()

    # Example 1: Create a basic catalog
    print("Example 1: Basic Catalog")
    print("-" * 80)
    catalog = create_catalog(
        title="My Book Collection",
        self_link="https://example.com/catalog",
        search_link="https://example.com/search?q={searchTerms}",
        identifier="urn:uuid:example-catalog-001",
    )
    print(json.dumps(json.loads(catalog.model_dump_json()), indent=2))
    print()

    # Example 2: Create a catalog with publications
    print("Example 2: Catalog with All Books")
    print("-" * 80)
    all_publications = provider.search("")  # Empty query returns all
    catalog_with_books = create_catalog(
        title="Complete Book Collection",
        publications=all_publications,
        self_link="https://example.com/catalog/all",
    )
    print(json.dumps(json.loads(catalog_with_books.model_dump_json()), indent=2))
    print()

    # Example 3: Search catalog
    print("Example 3: Search Results for 'Pride'")
    print("-" * 80)
    search_catalog = create_search_catalog(
        provider=provider,
        query="Pride",
        self_link="https://example.com/search?q=Pride",
    )
    print(json.dumps(json.loads(search_catalog.model_dump_json()), indent=2))
    print()

    # Example 4: Another search
    print("Example 4: Search Results for 'Homer'")
    print("-" * 80)
    search_catalog2 = create_search_catalog(
        provider=provider,
        query="Homer",
        self_link="https://example.com/search?q=Homer",
    )
    print(json.dumps(json.loads(search_catalog2.model_dump_json()), indent=2))
    print()


if __name__ == "__main__":
    main()
