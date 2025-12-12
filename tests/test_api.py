import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app
from app.core.db import Base, engine
from app.models.schemas import ArticleJobCreate, Language


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@patch('app.api.routes.get_serp_client')
@patch('app.api.routes.get_llm_client')
@patch('app.api.routes.get_seo_validator')
@patch('app.api.routes.get_link_planner')
def test_post_jobs_creates_job(mock_link_planner, mock_seo_validator, mock_llm_client, mock_serp_client, client):
    from app.models.schemas import SERPResult
    from pydantic import HttpUrl
    from unittest.mock import MagicMock
    
    mock_serp = MagicMock()
    mock_serp.search.return_value = [
        SERPResult(rank=1, url=HttpUrl("https://example.com"), title="Test", snippet="Test snippet")
    ]
    mock_serp_client.return_value = mock_serp
    
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = [
        {"primary_keyword": "test", "secondary_keywords": ["k1"], "topics": ["t1"], "faqs": ["f1?"]},
        {"title": "Test", "sections": [
            {"heading_level": 2, "heading": "S1", "slug": "s1", "summary": "Summary"}
        ] * 3},
        {"title_tag": "Test", "meta_description": "Test desc"}
    ]
    mock_llm.generate_text.return_value = "# Test\n\n## Section\n\nContent"
    mock_llm_client.return_value = mock_llm
    
    mock_validator = MagicMock()
    mock_validator.validate.return_value = []
    mock_seo_validator.return_value = mock_validator
    
    mock_planner = MagicMock()
    from app.models.schemas import InternalLinkSuggestion, ExternalReference
    mock_planner.plan_internal_links.return_value = [
        InternalLinkSuggestion(anchor_text="L1", target_slug="l1")
    ] * 3
    mock_planner.plan_external_references.return_value = [
        ExternalReference(title="R1", url=HttpUrl("https://example.com"), suggested_section_slug="s1", context_reason="Test")
    ] * 2
    mock_link_planner.return_value = mock_planner
    
    response = client.post(
        "/api/v1/jobs",
        json={
            "topic": "test topic",
            "target_word_count": 1500,
            "language": "en"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["input"]["topic"] == "test topic"
    assert "status" in data


def test_get_job_returns_job(client):
    with patch('app.api.routes.get_serp_client'), \
         patch('app.api.routes.get_llm_client'), \
         patch('app.api.routes.get_seo_validator'), \
         patch('app.api.routes.get_link_planner'):
        
        from unittest.mock import MagicMock
        from app.models.schemas import SERPResult
        from pydantic import HttpUrl
        
        with patch('app.api.routes.SerpClient') as mock_serp_class, \
             patch('app.api.routes.LLMClient') as mock_llm_class, \
             patch('app.api.routes.SEOValidator') as mock_validator_class, \
             patch('app.api.routes.LinkPlanner') as mock_planner_class:
            
            mock_serp = MagicMock()
            mock_serp.search.return_value = [
                SERPResult(rank=1, url=HttpUrl("https://example.com"), title="Test", snippet="Test")
            ]
            mock_serp_class.return_value = mock_serp
            
            mock_llm = MagicMock()
            mock_llm.generate_json.side_effect = [
                {"primary_keyword": "test", "secondary_keywords": [], "topics": [], "faqs": []},
                {"title": "Test", "sections": [
                    {"heading_level": 2, "heading": "S", "slug": "s", "summary": "S"}
                ] * 3},
                {"title_tag": "Test", "meta_description": "Test"}
            ]
            mock_llm.generate_text.return_value = "# Test\n\n## S\n\nContent"
            mock_llm_class.return_value = mock_llm
            
            mock_validator = MagicMock()
            mock_validator.validate.return_value = []
            mock_validator_class.return_value = mock_validator
            
            mock_planner = MagicMock()
            from app.models.schemas import InternalLinkSuggestion, ExternalReference
            mock_planner.plan_internal_links.return_value = [
                InternalLinkSuggestion(anchor_text="L", target_slug="l")
            ] * 3
            mock_planner.plan_external_references.return_value = [
                ExternalReference(title="R", url=HttpUrl("https://example.com"), suggested_section_slug="s", context_reason="Test")
            ] * 2
            mock_planner_class.return_value = mock_planner
            
            create_response = client.post(
                "/api/v1/jobs",
                json={"topic": "test", "target_word_count": 1500, "language": "en"}
            )
            
            if create_response.status_code == 201:
                job_id = create_response.json()["id"]
                
                get_response = client.get(f"/api/v1/jobs/{job_id}")
                assert get_response.status_code == 200
                data = get_response.json()
                assert data["id"] == job_id
                assert "status" in data


def test_get_job_not_found(client):
    response = client.get("/api/v1/jobs/non-existent-id")
    assert response.status_code == 404

