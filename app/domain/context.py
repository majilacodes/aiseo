from typing import List, Optional
from pydantic import BaseModel
from app.models.schemas import (
    ArticleJobCreate,
    SERPResult,
    SERPAnalysis,
    Outline,
    Article
)


class ArticleContext(BaseModel):
    job_id: str
    input: ArticleJobCreate
    serp_results: List[SERPResult] = []
    serp_analysis: Optional[SERPAnalysis] = None
    outline: Optional[Outline] = None
    article: Optional[Article] = None

