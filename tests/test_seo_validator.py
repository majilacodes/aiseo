import pytest
from app.models.schemas import Article, SEOInfo, InternalLinkSuggestion, ExternalReference
from app.services.seo_validator import SEOValidator
from pydantic import HttpUrl


def create_test_article(
    h1: str = "Test Article",
    body: str = "This is a test article body.",
    primary_keyword: str = "test",
    word_count: int = 1500,
    h2_count: int = 3,
    internal_links_count: int = 3,
    external_refs_count: int = 2
) -> Article:
    body_markdown = f"# {h1}\n\n"
    
    for i in range(h2_count):
        body_markdown += f"## Section {i+1}\n\n"
        body_markdown += "Some content here. " * 50 + "\n\n"
    
    current_words = len(body_markdown.split())
    if current_words < word_count:
        body_markdown += "Additional content. " * (word_count - current_words)
    elif current_words > word_count:
        words = body_markdown.split()[:word_count]
        body_markdown = " ".join(words)
    
    internal_links = [
        InternalLinkSuggestion(anchor_text=f"Link {i+1}", target_slug=f"link-{i+1}")
        for i in range(internal_links_count)
    ]
    
    external_refs = [
        ExternalReference(
            title=f"Ref {i+1}",
            url=HttpUrl("https://example.com"),
            suggested_section_slug="section-1",
            context_reason="Test reference"
        )
        for i in range(external_refs_count)
    ]
    
    return Article(
        h1=h1,
        body_markdown=body_markdown,
        seo=SEOInfo(
            title_tag="Test Title",
            meta_description="Test description",
            primary_keyword=primary_keyword,
            secondary_keywords=[],
            word_count_target=word_count
        ),
        internal_links=internal_links,
        external_references=external_refs,
        structured_data={}
    )


def test_validator_missing_primary_keyword_in_h1():
    validator = SEOValidator()
    article = create_test_article(
        h1="Different Title",
        primary_keyword="test"
    )
    errors = validator.validate(article)
    assert len(errors) > 0
    assert any("H1" in error for error in errors)


def test_validator_word_count_below_minimum():
    validator = SEOValidator()
    article = create_test_article(
        primary_keyword="test",
        word_count=1000,  # Below 80% of 1500 (1200)
        body="test " * 500  # Only 500 words
    )
    article.body_markdown = "test " * 500
    errors = validator.validate(article)
    assert len(errors) > 0
    assert any("Word count" in error and "below" in error.lower() for error in errors)


def test_validator_too_few_h2s():
    validator = SEOValidator()
    article = create_test_article(
        h1="Test Article",
        primary_keyword="test",
        h2_count=2  # Less than 3
    )
    errors = validator.validate(article)
    assert len(errors) > 0
    assert any("H2" in error for error in errors)


def test_validator_too_few_internal_links():
    validator = SEOValidator()
    article = create_test_article(
        h1="Test Article",
        primary_keyword="test",
        internal_links_count=2  # Less than 3
    )
    errors = validator.validate(article)
    assert len(errors) > 0
    assert any("internal links" in error.lower() for error in errors)


def test_validator_too_few_external_references():
    validator = SEOValidator()
    article = create_test_article(
        h1="Test Article",
        primary_keyword="test",
        external_refs_count=1  # Less than 2
    )
    errors = validator.validate(article)
    assert len(errors) > 0
    assert any("external references" in error.lower() for error in errors)


def test_validator_valid_article_passes():
    validator = SEOValidator()
    article = create_test_article(
        h1="Test Article About Testing",
        primary_keyword="test",
        word_count=1500,
        h2_count=3,
        internal_links_count=3,
        external_refs_count=2
    )

    words = article.body_markdown.split()
    words[:10] = ["test"] * 10
    article.body_markdown = " ".join(words)
    
    errors = validator.validate(article)
    assert len(errors) == 0

