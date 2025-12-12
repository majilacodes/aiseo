import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from app.models.schemas import ArticleJobCreate, Language, JobStatus
from app.models.orm import create_job, get_job
from app.domain.pipeline import process_job, build_pipeline
from app.services.serp_client import SerpClient
from app.services.llm_client import LLMClient
from app.services.seo_validator import SEOValidator
from app.services.link_planner import LinkPlanner
from app.core.db import Base, engine, SessionLocal


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_services():
    serp_client = Mock(spec=SerpClient)
    llm_client = Mock(spec=LLMClient)
    seo_validator = Mock(spec=SEOValidator)
    link_planner = Mock(spec=LinkPlanner)
    
    from app.models.schemas import SERPResult
    from pydantic import HttpUrl
    serp_client.search.return_value = [
        SERPResult(
            rank=1,
            url=HttpUrl("https://example.com/1"),
            title="Example Result 1",
            snippet="This is a test snippet"
        ),
        SERPResult(
            rank=2,
            url=HttpUrl("https://example.com/2"),
            title="Example Result 2",
            snippet="Another test snippet"
        )
    ]
    
    llm_client.generate_json.side_effect = [
        {
            "primary_keyword": "test topic",
            "secondary_keywords": ["keyword1", "keyword2", "keyword3"],
            "topics": ["topic1", "topic2", "topic3"],
            "faqs": ["FAQ1?", "FAQ2?"]
        },
        {
            "title": "Test Article Title",
            "sections": [
                {"heading_level": 2, "heading": "Introduction", "slug": "introduction", "summary": "Intro section"},
                {"heading_level": 2, "heading": "Main Content", "slug": "main-content", "summary": "Main section"},
                {"heading_level": 2, "heading": "Conclusion", "slug": "conclusion", "summary": "Conclusion section"}
            ]
        },
        {
            "title_tag": "Test Article Title | SEO",
            "meta_description": "This is a test meta description for the article."
        }
    ]
    
    llm_client.generate_text.return_value = """# Test Article Title

## Introduction

This is the introduction section with test content.

## Main Content

This is the main content section.

## Conclusion

This is the conclusion section.
"""
    
    seo_validator.validate.return_value = []
    
    from app.models.schemas import InternalLinkSuggestion, ExternalReference
    link_planner.plan_internal_links.return_value = [
        InternalLinkSuggestion(anchor_text="Link 1", target_slug="link-1"),
        InternalLinkSuggestion(anchor_text="Link 2", target_slug="link-2"),
        InternalLinkSuggestion(anchor_text="Link 3", target_slug="link-3")
    ]
    link_planner.plan_external_references.return_value = [
        ExternalReference(
            title="Ref 1",
            url=HttpUrl("https://example.com"),
            suggested_section_slug="introduction",
            context_reason="Test reference"
        ),
        ExternalReference(
            title="Ref 2",
            url=HttpUrl("https://example2.com"),
            suggested_section_slug="main-content",
            context_reason="Another reference"
        )
    ]
    
    return {
        "serp_client": serp_client,
        "llm_client": llm_client,
        "seo_validator": seo_validator,
        "link_planner": link_planner
    }


def test_build_pipeline(mock_services):
    pipeline = build_pipeline(
        mock_services["serp_client"],
        mock_services["llm_client"],
        mock_services["seo_validator"],
        mock_services["link_planner"]
    )
    
    assert len(pipeline) == 5
    assert pipeline[0].__class__.__name__ == "SERPAgent"
    assert pipeline[1].__class__.__name__ == "SERPAnalysisAgent"
    assert pipeline[2].__class__.__name__ == "OutlineAgent"
    assert pipeline[3].__class__.__name__ == "DraftAgent"
    assert pipeline[4].__class__.__name__ == "ValidationAgent"


def test_process_job_completes_successfully(db_session, mock_services):
    job_input = ArticleJobCreate(
        topic="test topic",
        target_word_count=1500,
        language=Language.en
    )
    job = create_job(db_session, job_input)
    
    process_job(job.id, db_session, mock_services)
    
    job = get_job(db_session, job.id)
    assert job.status == JobStatus.completed.value
    assert job.article_json is not None
    
    import json
    article_data = json.loads(job.article_json)
    assert "h1" in article_data
    assert "body_markdown" in article_data
    assert "seo" in article_data
    assert len(article_data.get("internal_links", [])) >= 3
    assert len(article_data.get("external_references", [])) >= 2


def test_process_job_persists_intermediate_states(db_session, mock_services):
    job_input = ArticleJobCreate(
        topic="test topic",
        target_word_count=1500,
        language=Language.en
    )
    job = create_job(db_session, job_input)
    
    process_job(job.id, db_session, mock_services)
    
    job = get_job(db_session, job.id)
    assert job.serp_results_json is not None
    assert job.serp_analysis_json is not None
    assert job.outline_json is not None
    assert job.article_json is not None

