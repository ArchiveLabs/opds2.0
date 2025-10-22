"""Tests for the types module."""

import pytest

from opds2.types import (
    OPDS_RESERVED_FIELDS,
    ItemMapping,
    SearchResult,
)


def test_search_result_creation():
    """Test creating a SearchResult."""
    result = SearchResult(
        items=[{"title": "Book 1"}, {"title": "Book 2"}],
        page=1,
        num_found=10,
        rows=2
    )
    
    assert len(result.items) == 2
    assert result.page == 1
    assert result.num_found == 10
    assert result.rows == 2


def test_search_result_defaults():
    """Test SearchResult with default values."""
    result = SearchResult()
    
    assert result.items == []
    assert result.page == 1
    assert result.num_found == 0
    assert result.rows == 50


def test_opds_reserved_fields():
    """Test that OPDS_RESERVED_FIELDS contains expected fields."""
    expected_fields = {
        "title", "identifier", "description", "language",
        "author", "publisher", "published", "modified",
        "cover_url", "thumbnail_url", "acquisition_link",
        "acquisition_type", "subject"
    }
    
    assert set(OPDS_RESERVED_FIELDS.keys()) == expected_fields


def test_item_mapping_basic():
    """Test basic ItemMapping functionality."""
    mapping = ItemMapping(
        title=lambda item: item.get("title"),
        author=lambda item: [item.get("author")]
    )
    
    item = {"title": "Test Book", "author": "Test Author"}
    result = mapping.map_item(item)
    
    assert result["title"] == "Test Book"
    assert result["author"] == ["Test Author"]


def test_item_mapping_none_values():
    """Test that None values are not included in mapping."""
    mapping = ItemMapping(
        title=lambda item: item.get("title"),
        author=lambda item: item.get("author"),  # Will return None
    )
    
    item = {"title": "Test Book"}  # No author field
    result = mapping.map_item(item)
    
    assert "title" in result
    assert "author" not in result  # None values should not be in result


def test_item_mapping_complex_transformation():
    """Test ItemMapping with complex transformations."""
    mapping = ItemMapping(
        title=lambda item: item.get("name", "").upper(),
        author=lambda item: [a.strip() for a in item.get("authors", "").split(",") if a.strip()],
        cover_url=lambda item: f"https://example.com/covers/{item.get('id')}.jpg" if item.get('id') else None,
    )
    
    item = {
        "name": "test book",
        "authors": "Author One, Author Two",
        "id": 123
    }
    
    result = mapping.map_item(item)
    
    assert result["title"] == "TEST BOOK"
    assert result["author"] == ["Author One", "Author Two"]
    assert result["cover_url"] == "https://example.com/covers/123.jpg"


def test_item_mapping_all_fields():
    """Test ItemMapping with all OPDS fields."""
    mapping = ItemMapping(
        title=lambda item: item["title"],
        identifier=lambda item: item.get("id"),
        description=lambda item: item.get("desc"),
        language=lambda item: [item.get("lang")],
        author=lambda item: item.get("authors", []),
        publisher=lambda item: item.get("publishers", []),
        published=lambda item: item.get("pub_date"),
        modified=lambda item: item.get("mod_date"),
        cover_url=lambda item: item.get("cover"),
        thumbnail_url=lambda item: item.get("thumb"),
        acquisition_link=lambda item: item.get("url"),
        acquisition_type=lambda item: item.get("type"),
        subject=lambda item: item.get("subjects", []),
    )
    
    item = {
        "title": "Complete Book",
        "id": "book-123",
        "desc": "A complete book",
        "lang": "en",
        "authors": ["Author One"],
        "publishers": ["Publisher One"],
        "pub_date": "2024-01-01",
        "mod_date": "2024-02-01",
        "cover": "https://example.com/cover.jpg",
        "thumb": "https://example.com/thumb.jpg",
        "url": "https://example.com/book.epub",
        "type": "application/epub+zip",
        "subjects": ["Fiction", "Drama"]
    }
    
    result = mapping.map_item(item)
    
    # Verify all fields are mapped
    assert result["title"] == "Complete Book"
    assert result["identifier"] == "book-123"
    assert result["description"] == "A complete book"
    assert result["language"] == ["en"]
    assert result["author"] == ["Author One"]
    assert result["publisher"] == ["Publisher One"]
    assert result["published"] == "2024-01-01"
    assert result["modified"] == "2024-02-01"
    assert result["cover_url"] == "https://example.com/cover.jpg"
    assert result["thumbnail_url"] == "https://example.com/thumb.jpg"
    assert result["acquisition_link"] == "https://example.com/book.epub"
    assert result["acquisition_type"] == "application/epub+zip"
    assert result["subject"] == ["Fiction", "Drama"]


def test_item_mapping_partial_fields():
    """Test ItemMapping with only some fields defined."""
    mapping = ItemMapping(
        title=lambda item: item.get("title"),
        cover_url=lambda item: item.get("cover"),
    )
    
    item = {
        "title": "Book",
        "author": "Author",  # This won't be mapped
        "cover": "https://example.com/cover.jpg"
    }
    
    result = mapping.map_item(item)
    
    assert len(result) == 2
    assert "title" in result
    assert "cover_url" in result
    assert "author" not in result  # Not mapped


def test_search_result_with_metadata():
    """Test SearchResult with realistic metadata."""
    items = [
        {"title": "Book 1", "author": "Author 1"},
        {"title": "Book 2", "author": "Author 2"},
    ]
    
    result = SearchResult(
        items=items,
        page=2,
        num_found=100,
        rows=2
    )
    
    # Verify pagination calculations would be correct
    assert result.page == 2
    assert result.rows == 2
    # For page 2 with 2 rows, we'd be at offset 2
    expected_offset = (result.page - 1) * result.rows
    assert expected_offset == 2
