"""Example: OpenLibrary Data Provider for OPDS 2.0

This example demonstrates how to create a DataProvider that interfaces
with the Open Library API to search for books and generate OPDS feeds.

Open Library API: https://openlibrary.org/developers/api
"""

import json
from typing import Dict, Any

try:
    import requests
except ImportError:
    print("This example requires the 'requests' library.")
    print("Install it with: pip install requests")
    exit(1)

from opds2 import (
    DataProvider,
    ItemMapping,
    SearchResult,
    create_catalog,
    create_search_catalog,
)


DEFAULT_ROWS = 10  # Default number of results per page


class OpenLibraryDataProvider(DataProvider):
    """Data provider for Open Library search API.
    
    This provider demonstrates the new architecture where:
    1. search() returns raw data in a SearchResult
    2. get_item_mapping() defines how to map Open Library fields to OPDS fields
    """
    
    URL = "https://openlibrary.org"
    
    def search(self, query: str, page: int = 1, rows: int = DEFAULT_ROWS) -> SearchResult:
        """Search Open Library for books.
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            rows: Number of results per page
            
        Returns:
            SearchResult with Open Library search data
        """
        fields = [
            "key", "title", "editions", "description", "providers",
            "author_name", "cover_i", "availability"
        ]
        params = {
            "editions": "true",
            "page": page,
            "q": query,
            "limit": rows,
            "fields": ",".join(fields),
        }
        
        try:
            r = requests.get(f"{self.URL}/search.json", params=params)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Error fetching from Open Library: {e}")
            return SearchResult(items=[], page=page, num_found=0, rows=rows)
        
        items = data.get('docs', [])
        num_found = data.get('numFound', 0)
        
        return SearchResult(
            items=items,
            page=page,
            num_found=num_found,
            rows=rows
        )
    
    def get_item_mapping(self) -> ItemMapping:
        """Define how to map Open Library items to OPDS fields.
        
        Returns:
            ItemMapping with field extractors for Open Library data
        """
        return ItemMapping(
            # Required field
            title=lambda item: item.get("title", "Untitled"),
            
            # Identifier - use Open Library key
            identifier=lambda item: f"https://openlibrary.org{item['key']}" if item.get('key') else None,
            
            # Description - Open Library sometimes has this as a string or dict
            description=lambda item: self._extract_description(item),
            
            # Language - usually not in search results, could be enhanced
            language=lambda item: ["en"] if item.get("language") else None,
            
            # Author names
            author=lambda item: item.get("author_name", []),
            
            # Cover image URL
            cover_url=lambda item: f"https://covers.openlibrary.org/b/id/{item.get('cover_i')}-L.jpg" 
                if item.get('cover_i') else None,
            
            # Thumbnail image URL
            thumbnail_url=lambda item: f"https://covers.openlibrary.org/b/id/{item.get('cover_i')}-M.jpg" 
                if item.get('cover_i') else None,
            
            # Acquisition link - link to the book page
            acquisition_link=lambda item: f"https://openlibrary.org{item['key']}" if item.get('key') else None,
            
            # Type is HTML page (in real implementation, you might link to downloadable formats)
            acquisition_type=lambda item: "text/html",
        )
    
    @staticmethod
    def _extract_description(item: Dict[str, Any]) -> str:
        """Extract description from Open Library item.
        
        Open Library descriptions can be strings or dicts with 'value' key.
        """
        desc = item.get("description")
        if desc:
            if isinstance(desc, str):
                return desc
            elif isinstance(desc, dict):
                return desc.get("value", "")
        return None


def main():
    """Demonstrate the OpenLibrary data provider."""
    print("=" * 80)
    print("Open Library OPDS 2.0 Example")
    print("=" * 80)
    print()
    
    # Create the provider
    provider = OpenLibraryDataProvider()
    
    # Example 1: Create a main catalog with search capability
    print("Example 1: Main Catalog with Search")
    print("-" * 80)
    catalog = create_catalog(
        title="Open Library Catalog",
        self_link="https://example.com/openlibrary/catalog",
        search_link="https://example.com/openlibrary/search?q={searchTerms}",
        identifier="urn:uuid:openlibrary-catalog-001",
    )
    print(json.dumps(json.loads(catalog.model_dump_json()), indent=2))
    print()
    
    # Example 2: Search for books
    search_query = "science fiction"
    print(f'Example 2: Search Results for "{search_query}"')
    print("-" * 80)
    
    # Perform the search
    search_catalog = create_search_catalog(
        provider=provider,
        query=search_query,
        page=1,
        rows=5,  # Limit to 5 results for the example
        self_link=f"https://example.com/openlibrary/search?q={search_query.replace(' ', '+')}"
    )
    
    print(json.dumps(json.loads(search_catalog.model_dump_json()), indent=2))
    print()
    
    # Example 3: Show raw search result data
    print("Example 3: Raw Search Result Data (before OPDS mapping)")
    print("-" * 80)
    raw_result = provider.search("python programming", page=1, rows=3)
    print(f"Found {raw_result.num_found} total results")
    print(f"Page: {raw_result.page}, Rows per page: {raw_result.rows}")
    print(f"Returned {len(raw_result.items)} items")
    if raw_result.items:
        print("\nFirst item (raw data):")
        print(json.dumps(raw_result.items[0], indent=2, default=str))
    print()
    
    # Example 4: Demonstrate item mapping
    print("Example 4: Item Mapping Example")
    print("-" * 80)
    if raw_result.items:
        mapping = provider.get_item_mapping()
        first_item = raw_result.items[0]
        mapped_item = mapping.map_item(first_item)
        print("Mapped OPDS fields:")
        print(json.dumps(mapped_item, indent=2, default=str))
    print()


if __name__ == "__main__":
    main()
