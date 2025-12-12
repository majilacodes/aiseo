import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.domain.context import ArticleContext
from app.domain.agents import (
    SERPAgent,
    SERPAnalysisAgent,
    OutlineAgent,
    DraftAgent,
    ValidationAgent
)
from app.models.orm import get_job, update_job_status_and_data
from app.models.schemas import JobStatus, SERPResult, SERPAnalysis, Outline, Article


def build_pipeline(serp_client, llm_client, seo_validator, link_planner) -> list:
    return [
        SERPAgent(serp_client),
        SERPAnalysisAgent(llm_client),
        OutlineAgent(llm_client),
        DraftAgent(llm_client),
        ValidationAgent(seo_validator, link_planner)
    ]


def process_job(job_id: str, db: Session, services: Dict[str, Any]) -> None:
    job = get_job(db, job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    if job.status == JobStatus.completed.value:
        return
    if job.status == JobStatus.failed.value:
        return
    
    update_job_status_and_data(db, job_id, JobStatus.running)
    
    try:
        from app.models.schemas import ArticleJobCreate, Language
        
        ctx = ArticleContext(
            job_id=job_id,
            input=ArticleJobCreate(
                topic=job.topic,
                target_word_count=job.target_word_count,
                language=Language(job.language)
            )
        )

        if job.serp_results_json:
            serp_data = json.loads(job.serp_results_json)
            ctx.serp_results = [SERPResult(**r) for r in serp_data]
        
        if job.serp_analysis_json:
            ctx.serp_analysis = SERPAnalysis.model_validate_json(job.serp_analysis_json)
        
        if job.outline_json:
            ctx.outline = Outline.model_validate_json(job.outline_json)
        
        if job.article_json:
            ctx.article = Article.model_validate_json(job.article_json)
    
        agents = build_pipeline(
            services["serp_client"],
            services["llm_client"],
            services["seo_validator"],
            services["link_planner"]
        )
        
        for agent in agents:
            ctx = agent.run(ctx)
            
            if isinstance(agent, SERPAgent) and ctx.serp_results:
                update_job_status_and_data(
                    db, job_id, JobStatus.running,
                    serp_results=ctx.serp_results
                )
            
            elif isinstance(agent, SERPAnalysisAgent) and ctx.serp_analysis:
                update_job_status_and_data(
                    db, job_id, JobStatus.running,
                    serp_analysis=ctx.serp_analysis
                )
            
            elif isinstance(agent, OutlineAgent) and ctx.outline:
                update_job_status_and_data(
                    db, job_id, JobStatus.running,
                    outline=ctx.outline
                )
            
            elif isinstance(agent, DraftAgent) and ctx.article:
                update_job_status_and_data(
                    db, job_id, JobStatus.running,
                    article=ctx.article
                )
            
            elif isinstance(agent, ValidationAgent) and ctx.article:
                update_job_status_and_data(
                    db, job_id, JobStatus.running,
                    article=ctx.article
                )
        
        update_job_status_and_data(db, job_id, JobStatus.completed, article=ctx.article)
        
    except Exception as e:
        error_message = str(e)
        update_job_status_and_data(
            db, job_id, JobStatus.failed,
            error_message=error_message
        )
        raise

