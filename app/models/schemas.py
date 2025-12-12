from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class Language(str, Enum):
    en = "en"


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class SERPResult(BaseModel):
    rank: int
    url: HttpUrl
    title: str
    snippet: str


class SERPAnalysis(BaseModel):
    primary_keyword: str
    secondary_keywords: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    faqs: List[str] = Field(default_factory=list)


class OutlineSection(BaseModel):
    heading_level: int = Field(ge=1, le=3)
    heading: str
    slug: str
    summary: str


class Outline(BaseModel):
    title: str  # H1
    sections: List[OutlineSection] = Field(default_factory=list)


class InternalLinkSuggestion(BaseModel):
    anchor_text: str
    target_slug: str


class ExternalReference(BaseModel):
    title: str
    url: HttpUrl
    suggested_section_slug: str
    context_reason: str


class SEOInfo(BaseModel):
    title_tag: str
    meta_description: str
    primary_keyword: str
    secondary_keywords: List[str] = Field(default_factory=list)
    word_count_target: int
    estimated_word_count: Optional[int] = None


class Article(BaseModel):
    h1: str
    body_markdown: str
    seo: SEOInfo
    internal_links: List[InternalLinkSuggestion] = Field(default_factory=list)
    external_references: List[ExternalReference] = Field(default_factory=list)
    structured_data: dict = Field(default_factory=dict)


class ArticleJobCreate(BaseModel):
    topic: str
    target_word_count: int = 1500
    language: Language = Language.en


class ArticleJob(BaseModel):
    id: str
    input: ArticleJobCreate
    status: JobStatus
    error: Optional[str] = None
    serp_results: Optional[List[SERPResult]] = None
    serp_analysis: Optional[SERPAnalysis] = None
    outline: Optional[Outline] = None
    article: Optional[Article] = None

