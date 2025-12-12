from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import Session
import uuid
import json

from app.core.db import Base
from app.models.schemas import ArticleJobCreate, JobStatus, SERPResult, SERPAnalysis, Outline, Article


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(String, nullable=False)
    target_word_count = Column(Integer, nullable=False)
    language = Column(String, nullable=False, default="en")
    status = Column(String, nullable=False, default=JobStatus.pending.value)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    serp_results_json = Column(Text, nullable=True)
    serp_analysis_json = Column(Text, nullable=True)
    outline_json = Column(Text, nullable=True)
    article_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)


def create_job(db: Session, job_input: ArticleJobCreate) -> Job:
    job = Job(
        id=str(uuid.uuid4()),
        topic=job_input.topic,
        target_word_count=job_input.target_word_count,
        language=job_input.language.value,
        status=JobStatus.pending.value
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Optional[Job]:
    return db.query(Job).filter(Job.id == job_id).first()


def update_job_status_and_data(
    db: Session,
    job_id: str,
    status: JobStatus,
    serp_results: Optional[List[SERPResult]] = None,
    serp_analysis: Optional[SERPAnalysis] = None,
    outline: Optional[Outline] = None,
    article: Optional[Article] = None,
    error_message: Optional[str] = None
) -> Job:
    job = get_job(db, job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    job.status = status.value
    job.updated_at = datetime.utcnow()
    
    if serp_results is not None:
        job.serp_results_json = json.dumps([r.model_dump() for r in serp_results], default=str)
    
    if serp_analysis is not None:
        job.serp_analysis_json = serp_analysis.model_dump_json()
    
    if outline is not None:
        job.outline_json = outline.model_dump_json()
    
    if article is not None:
        job.article_json = article.model_dump_json()
    
    if error_message is not None:
        job.error_message = error_message
    
    db.commit()
    db.refresh(job)
    return job

