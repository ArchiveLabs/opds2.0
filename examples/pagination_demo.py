"""Demonstration of the add_pagination function.

This example shows how to use the add_pagination function to add
pagination links and metadata to any OPDS catalog.
"""

from opds2 import Metadata, Link, Publication
from opds2.catalog import create_catalog, add_pagination


def demo_basic_pagination():
    """Demonstrate adding pagination to a basic catalog."""
    print("=" * 80)
    print("DEMO: Basic Pagination")
    print("=" * 80)
    
    # Create a catalog with some sample publications
    publications = [
        Publication(
            metadata=Metadata(title=f"Book {i}"),
            links=[Link(href=f"https://example.com/book{i}.epub", type="application/epub+zip")]
        )
        for i in range(1, 11)
    ]
    
    catalog = create_catalog(
        title="My Library Catalog",
        publications=publications,
        self_link="https://example.com/catalog"
    )
    
    # Add pagination (showing page 1 of 10)
    total_items = 100
    items_per_page = 10
    current_offset = 0
    base_url = "https://example.com/catalog"
    params = {"sort": "title"}
    
    paginated_catalog = add_pagination(
        catalog=catalog,
        total=total_items,
        limit=items_per_page,
        offset=current_offset,
        base_url=base_url,
        params=params
    )
    
    print(f"\nCatalog Title: {paginated_catalog.metadata.title}")
    print(f"Total Items: {paginated_catalog.metadata.numberOfItems}")
    print(f"Items Per Page: {paginated_catalog.metadata.itemsPerPage}")
    print(f"Current Page: {paginated_catalog.metadata.currentPage}")
    print(f"\nPagination Links:")
    for link in paginated_catalog.links:
        print(f"  {link.rel}: {link.href}")
    print()


def demo_middle_page():
    """Demonstrate pagination for a middle page."""
    print("=" * 80)
    print("DEMO: Middle Page Pagination")
    print("=" * 80)
    
    catalog = create_catalog(
        title="Search Results",
        publications=[]
    )
    
    # Page 5 of 10
    total_items = 100
    items_per_page = 10
    current_offset = 40  # Page 5
    base_url = "https://example.com/search"
    params = {"query": "python", "sort": "relevance"}
    
    paginated_catalog = add_pagination(
        catalog=catalog,
        total=total_items,
        limit=items_per_page,
        offset=current_offset,
        base_url=base_url,
        params=params
    )
    
    print(f"\nCatalog Title: {paginated_catalog.metadata.title}")
    print(f"Current Page: {paginated_catalog.metadata.currentPage} of 10")
    print(f"\nPagination Links:")
    for link in paginated_catalog.links:
        print(f"  {link.rel}: {link.href}")
    print()


def demo_last_page():
    """Demonstrate pagination for the last page."""
    print("=" * 80)
    print("DEMO: Last Page Pagination")
    print("=" * 80)
    
    catalog = create_catalog(
        title="Search Results",
        publications=[]
    )
    
    # Last page (page 10 of 10)
    total_items = 100
    items_per_page = 10
    current_offset = 90  # Page 10
    base_url = "https://example.com/search"
    params = {"query": "python"}
    
    paginated_catalog = add_pagination(
        catalog=catalog,
        total=total_items,
        limit=items_per_page,
        offset=current_offset,
        base_url=base_url,
        params=params
    )
    
    print(f"\nCatalog Title: {paginated_catalog.metadata.title}")
    print(f"Current Page: {paginated_catalog.metadata.currentPage} (last page)")
    print(f"\nPagination Links (note: no 'next' or 'last' links):")
    for link in paginated_catalog.links:
        print(f"  {link.rel}: {link.href}")
    print()


def demo_with_dataprovider():
    """Demonstrate how pagination could be used with a DataProvider."""
    print("=" * 80)
    print("DEMO: Using add_pagination with a DataProvider")
    print("=" * 80)
    
    # This demonstrates the pattern from the problem statement:
    # Instead of using DataProvider.search_catalog (which has built-in pagination),
    # you can use create_catalog + add_pagination for more control
    
    print("""
Example usage pattern:

from opds2.catalog import add_pagination

# Get search results from your data provider
records, num_found = MyDataProvider.search(query="python programming", limit=10)

# Create catalog with publications
catalog = MyDataProvider.create_catalog(
    publications=[record.to_publication() for record in records]
)

# Add pagination to the catalog
base_url = MyDataProvider.SEARCH_URL.replace("{?query}", "")
params = {"query": "python programming", "limit": "10"}

catalog_with_pagination = add_pagination(
    catalog=catalog,
    total=num_found,
    limit=10,
    offset=0,
    base_url=base_url,
    params=params
)

# Now catalog_with_pagination has all the pagination links and metadata
""")


if __name__ == "__main__":
    demo_basic_pagination()
    demo_middle_page()
    demo_last_page()
    demo_with_dataprovider()
    
    print("=" * 80)
    print("All demos completed successfully!")
    print("=" * 80)
