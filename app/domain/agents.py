import json
from typing import Dict
from app.domain.context import ArticleContext
from app.models.schemas import SERPAnalysis, Outline, OutlineSection, Article, SEOInfo
from app.services.serp_client import SerpClient
from app.services.llm_client import LLMClient


class SERPAgent:
    
    def __init__(self, serp_client: SerpClient):
        self.serp_client = serp_client
    
    def run(self, ctx: ArticleContext) -> ArticleContext:
        if not ctx.serp_results:
            # Request 15 to ensure we get at least 10 results
            ctx.serp_results = self.serp_client.search(
                query=ctx.input.topic,
                limit=15
            )
            # Trim to 10 results if we got more
            ctx.serp_results = ctx.serp_results[:10]
        return ctx


class SERPAnalysisAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def run(self, ctx: ArticleContext) -> ArticleContext:
        if ctx.serp_analysis is None:
            serp_text = "\n\n".join([
                f"Rank {r.rank}: {r.title}\n{r.snippet}"
                for r in ctx.serp_results
            ])
            
            prompt = f"""Analyze the following search results for the topic "{ctx.input.topic}":

{serp_text}

Extract and return JSON with:
- primary_keyword: The main keyword (string)
- secondary_keywords: 10-20 related keywords (array of strings)
- topics: 8-12 key subtopics to cover (array of strings)
- faqs: 5-8 frequently asked questions (array of strings)

Return only valid JSON matching this structure:
{{
  "primary_keyword": "...",
  "secondary_keywords": ["...", "..."],
  "topics": ["...", "..."],
  "faqs": ["...", "..."]
}}"""
            
            schema_hint = '{"primary_keyword": "string", "secondary_keywords": ["string"], "topics": ["string"], "faqs": ["string"]}'
            result = self.llm_client.generate_json(prompt, schema_hint)
            
            ctx.serp_analysis = SERPAnalysis(**result)
        
        return ctx


class OutlineAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def run(self, ctx: ArticleContext) -> ArticleContext:
        if ctx.outline is None:
            if not ctx.serp_analysis:
                raise ValueError("SERP analysis required before generating outline")
            
            prompt = f"""Create a detailed SEO-optimized article outline for the topic: "{ctx.input.topic}"

Primary keyword: {ctx.serp_analysis.primary_keyword}
Secondary keywords: {', '.join(ctx.serp_analysis.secondary_keywords[:10])}
Key topics to cover: {', '.join(ctx.serp_analysis.topics)}
Target word count: {ctx.input.target_word_count}

Requirements:
- Exactly one H1 (provided as the title field)
- Multiple H2 sections (at least 3) with heading_level=2
- Optional H3 subsections with heading_level=3
- Each section should have:
  - heading_level: 2 or 3 (title is the H1)
  - heading: The heading text
  - slug: URL-friendly slug (lowercase, hyphens)
  - summary: Brief explanation of what this section covers

Return only valid JSON matching this structure:
{{
  "title": "H1 title here",
  "sections": [
    {{
      "heading_level": 2,
      "heading": "Section heading",
      "slug": "section-slug",
      "summary": "What this section covers"
    }}
  ]
}}"""
            
            schema_hint = '{"title": "string", "sections": [{"heading_level": 2, "heading": "string", "slug": "string", "summary": "string"}]}'
            result = self.llm_client.generate_json(prompt, schema_hint)
            
            outline = Outline(**result)
            
            h1_in_sections = sum(1 for s in outline.sections if s.heading_level == 1)
            h2_count = sum(1 for s in outline.sections if s.heading_level == 2)
            
            if h1_in_sections > 0:
                raise ValueError(f"Outline sections should not have heading_level=1 (title is the H1), found {h1_in_sections} H1 sections")
            
            if h2_count < 3:
                raise ValueError(f"Outline must have at least 3 H2 sections, found {h2_count}")
            
            ctx.outline = outline
        
        return ctx


class DraftAgent:
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def run(self, ctx: ArticleContext) -> ArticleContext:
        if ctx.article is None:
            if not ctx.outline or not ctx.serp_analysis:
                raise ValueError("Outline and SERP analysis required before generating draft")
            
            outline_text = ctx.outline.title + "\n\n"
            for section in ctx.outline.sections:
                prefix = "#" * section.heading_level
                outline_text += f"{prefix} {section.heading}\n"
                outline_text += f"{section.summary}\n\n"
            
            target = ctx.input.target_word_count
            min_words = int(target * 0.8)
            max_words = int(target * 1.2)
            num_sections = len(ctx.outline.sections)
            words_per_section = max(200, target // max(num_sections, 1))
            
            prompt = f"""Write a complete, SEO-optimized article in markdown format.

Topic: {ctx.input.topic}
Primary keyword: {ctx.serp_analysis.primary_keyword}
Secondary keywords: {', '.join(ctx.serp_analysis.secondary_keywords)}
Target word count: {target} words (CRITICAL: You must write between {min_words} and {max_words} words)

Use this exact outline structure:
{outline_text}

Requirements:
1. Use the exact headings from the outline above (same text, same heading levels)
2. Include the primary keyword in:
   - The H1 (title)
   - The introduction (first 100-150 words)
   - At least one H2 heading
3. Use secondary keywords naturally throughout (no keyword stuffing)
4. WORD COUNT REQUIREMENT: Write between {min_words} and {max_words} words total (target: {target} words). This is mandatory. Aim for approximately {words_per_section} words per section. DO NOT exceed {max_words} words.
5. Write in a human, conversational tone
6. Make it engaging and valuable for readers with detailed explanations, examples, and insights
7. Use proper markdown formatting
8. Expand on each section with substantial content - don't just write brief summaries

Generate the full article body in markdown. Start with the H1 heading. Remember: the article must be between {min_words} and {max_words} words long."""
            
            body_markdown = self.llm_client.generate_text(prompt)
            
            seo_prompt = f"""Generate SEO metadata for this article:

Topic: {ctx.input.topic}
Primary keyword: {ctx.serp_analysis.primary_keyword}
Article title: {ctx.outline.title}

Return JSON with:
- title_tag: SEO title (50-60 characters, includes primary keyword)
- meta_description: Meta description (150-160 characters, includes primary keyword once)

Return only valid JSON:
{{
  "title_tag": "...",
  "meta_description": "..."
}}"""
            
            seo_schema = '{"title_tag": "string", "meta_description": "string"}'
            seo_result = self.llm_client.generate_json(seo_prompt, seo_schema)
            
            structured_data = {
                "@context": "https://schema.org",
                "@type": "BlogPosting",
                "headline": ctx.outline.title,
                "description": seo_result.get("meta_description", ""),
                "keywords": ", ".join([ctx.serp_analysis.primary_keyword] + ctx.serp_analysis.secondary_keywords[:5])
            }
            
            word_count = len(body_markdown.split())
            
            seo_info = SEOInfo(
                title_tag=seo_result["title_tag"],
                meta_description=seo_result["meta_description"],
                primary_keyword=ctx.serp_analysis.primary_keyword,
                secondary_keywords=ctx.serp_analysis.secondary_keywords,
                word_count_target=ctx.input.target_word_count,
                estimated_word_count=word_count
            )
            
            ctx.article = Article(
                h1=ctx.outline.title,
                body_markdown=body_markdown,
                seo=seo_info,
                internal_links=[],  
                external_references=[],
                structured_data=structured_data
            )
        
        return ctx


class ValidationAgent:
    
    def __init__(self, seo_validator, link_planner):
        self.seo_validator = seo_validator
        self.link_planner = link_planner
    
    def run(self, ctx: ArticleContext) -> ArticleContext:
        if not ctx.article:
            raise ValueError("Article required for validation")
        
        if not ctx.serp_analysis:
            raise ValueError("SERP analysis required for link planning")
        
        ctx.article.internal_links = self.link_planner.plan_internal_links(
            ctx.article,
            ctx.serp_analysis
        )
        
        if ctx.outline and ctx.serp_results:
            ctx.article.external_references = self.link_planner.plan_external_references(
                ctx.serp_results,
                ctx.outline
            )
        else:
            ctx.article.external_references = []

        errors = self.seo_validator.validate(ctx.article)
        
        if errors:
            error_message = "SEO validation failed:\n" + "\n".join(f"- {e}" for e in errors)
            raise ValueError(error_message)
        
        return ctx

