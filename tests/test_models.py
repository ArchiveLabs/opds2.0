"""Tests for OPDS 2.0 models."""

import json
from datetime import datetime

from pyopds2.models import (
    Catalog,
    Contributor,
    Link,
    Metadata,
    Navigation,
    Publication,
)


def test_link_creation():
    """Test creating a Link object."""
    link = Link(href="https://example.com/book.epub", type="application/epub+zip", rel="http://opds-spec.org/acquisition")
    assert link.href == "https://example.com/book.epub"
    assert link.type == "application/epub+zip"
    assert link.rel == "http://opds-spec.org/acquisition"


def test_contributor_creation():
    """Test creating a Contributor object."""
    contributor = Contributor(name="Jane Doe", role="author")
    assert contributor.name == "Jane Doe"
    assert contributor.role == "author"


def test_metadata_creation():
    """Test creating Metadata object."""
    metadata = Metadata(
        title="Example Book",
        language=["en"],
        description="A great book"
    )
    assert metadata.title == "Example Book"
    assert metadata.language == ["en"]
    assert metadata.description == "A great book"


def test_metadata_with_contributors():
    """Test Metadata with contributors."""
    author = Contributor(name="John Smith", role="author")
    metadata = Metadata(
        title="Test Book",
        author=[author]
    )
    assert metadata.title == "Test Book"
    assert len(metadata.author) == 1
    assert metadata.author[0].name == "John Smith"


def test_publication_creation():
    """Test creating a Publication object."""
    metadata = Metadata(title="Sample Publication")
    links = [
        Link(href="https://example.com/book.epub", type="application/epub+zip")
    ]
    publication = Publication(metadata=metadata, links=links)

    assert publication.metadata.title == "Sample Publication"
    assert len(publication.links) == 1
    assert publication.links[0].href == "https://example.com/book.epub"


def test_publication_json_export():
    """Test exporting Publication to JSON."""
    metadata = Metadata(
        title="Test Book",
        language=["en"],
        published=datetime(2024, 1, 1)
    )
    links = [Link(href="https://example.com/book.epub", type="application/epub+zip")]
    publication = Publication(metadata=metadata, links=links)

    json_str = publication.model_dump_json()
    assert json_str is not None

    # Parse it back to verify it's valid JSON
    data = json.loads(json_str)
    assert data["metadata"]["title"] == "Test Book"
    assert data["links"][0]["href"] == "https://example.com/book.epub"


def test_catalog_creation():
    """Test creating a Catalog object."""
    metadata = Metadata(title="My Catalog")
    catalog = Catalog(metadata=metadata)

    assert catalog.metadata.title == "My Catalog"
    assert catalog.links == []


def test_catalog_with_publications():
    """Test Catalog with publications."""
    catalog_metadata = Metadata(title="Book Collection")

    pub1 = Publication(
        metadata=Metadata(title="Book 1"),
        links=[Link(href="https://example.com/book1.epub")]
    )
    pub2 = Publication(
        metadata=Metadata(title="Book 2"),
        links=[Link(href="https://example.com/book2.epub")]
    )

    catalog = Catalog(
        metadata=catalog_metadata,
        publications=[pub1, pub2]
    )

    assert len(catalog.publications) == 2
    assert catalog.publications[0].metadata.title == "Book 1"
    assert catalog.publications[1].metadata.title == "Book 2"


def test_catalog_json_export():
    """Test exporting Catalog to JSON."""
    metadata = Metadata(
        title="Test Catalog",
        modified=datetime(2024, 1, 1, 12, 0, 0)
    )
    links = [
        Link(href="https://example.com/catalog", rel="self", type="application/opds+json")
    ]

    publication = Publication(
        metadata=Metadata(title="Sample Book"),
        links=[Link(href="https://example.com/book.epub")]
    )

    catalog = Catalog(
        metadata=metadata,
        links=links,
        publications=[publication]
    )

    json_str = catalog.model_dump_json()
    assert json_str is not None

    # Parse and verify
    data = json.loads(json_str)
    assert "@context" in data
    assert data["metadata"]["title"] == "Test Catalog"
    assert len(data["links"]) == 1
    assert len(data["publications"]) == 1


def test_catalog_with_search_link():
    """Test Catalog with search link."""
    metadata = Metadata(title="Searchable Catalog")
    links = [
        Link(href="https://example.com/catalog", rel="self", type="application/opds+json"),
        Link(href="https://example.com/search?q={searchTerms}", rel="search", type="application/opds+json", templated=True)
    ]

    catalog = Catalog(metadata=metadata, links=links)

    assert len(catalog.links) == 2
    search_link = [link for link in catalog.links if link.rel == "search"][0]
    assert search_link.templated is True
    assert "{searchTerms}" in search_link.href


def test_navigation():
    """Test Navigation object."""
    nav = Navigation(
        href="https://example.com/fiction",
        title="Fiction",
        type="application/opds+json"
    )

    assert nav.href == "https://example.com/fiction"
    assert nav.title == "Fiction"
    assert nav.type == "application/opds+json"


def test_catalog_with_navigation():
    """Test Catalog with navigation."""
    metadata = Metadata(title="Catalog with Navigation")
    navigation = [
        Navigation(href="https://example.com/fiction", title="Fiction"),
        Navigation(href="https://example.com/non-fiction", title="Non-Fiction")
    ]

    catalog = Catalog(metadata=metadata, navigation=navigation)

    assert len(catalog.navigation) == 2
    assert catalog.navigation[0].title == "Fiction"
    assert catalog.navigation[1].title == "Non-Fiction"
