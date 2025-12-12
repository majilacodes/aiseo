from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
from app.core.db import get_db
from app.models.schemas import ArticleJobCreate, ArticleJob, JobStatus, Language, SERPResult, SERPAnalysis, Outline, Article
from app.models.orm import create_job, get_job
from app.domain.pipeline import process_job
from app.services.serp_client import SerpClient
from app.services.llm_client import LLMClient
from app.services.seo_validator import SEOValidator
from app.services.link_planner import LinkPlanner
from app.core.config import settings

router = APIRouter()

def get_serp_client() -> SerpClient:
    return SerpClient(api_key=settings.serpapi_api_key)


def get_llm_client() -> LLMClient:
    return LLMClient(api_key=settings.openai_api_key)


def get_seo_validator() -> SEOValidator:
    return SEOValidator()


def get_link_planner() -> LinkPlanner:
    return LinkPlanner()


def get_services() -> Dict[str, Any]:
    return {
        "serp_client": get_serp_client(),
        "llm_client": get_llm_client(),
        "seo_validator": get_seo_validator(),
        "link_planner": get_link_planner()
    }


@router.post("/jobs", response_model=ArticleJob, status_code=201)
def create_article_job(
    job_input: ArticleJobCreate,
    db: Session = Depends(get_db),
    services: Dict[str, Any] = Depends(get_services)) -> ArticleJob:

    job = create_job(db, job_input)
    
    try:
        process_job(job.id, db, services)
    except Exception as e:
        pass
    
    job = get_job(db, job.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _job_to_response(job)


@router.get("/jobs/{job_id}", response_model=ArticleJob)
def get_article_job(
    job_id: str,
    db: Session = Depends(get_db)) -> ArticleJob:
    job = get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _job_to_response(job)


def _job_to_response(job) -> ArticleJob:
    from app.models.schemas import ArticleJobCreate, Language
    
    serp_results = None
    if job.serp_results_json:
        serp_data = json.loads(job.serp_results_json)
        serp_results = [SERPResult(**r) for r in serp_data]
    
    serp_analysis = None
    if job.serp_analysis_json:
        serp_analysis = SERPAnalysis.model_validate_json(job.serp_analysis_json)
    
    outline = None
    if job.outline_json:
        outline = Outline.model_validate_json(job.outline_json)
    
    article = None
    if job.article_json:
        article = Article.model_validate_json(job.article_json)
    
    return ArticleJob(
        id=job.id,
        input=ArticleJobCreate(
            topic=job.topic,
            target_word_count=job.target_word_count,
            language=Language(job.language)
        ),
        status=JobStatus(job.status),
        error=job.error_message,
        serp_results=serp_results,
        serp_analysis=serp_analysis,
        outline=outline,
        article=article
    )

