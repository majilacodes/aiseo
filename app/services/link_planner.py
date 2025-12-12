from typing import List
from app.models.schemas import (
    Article, 
    SERPAnalysis, 
    SERPResult, 
    Outline,
    InternalLinkSuggestion,
    ExternalReference
)

class LinkPlanner:
    INTERNAL_PAGES = [
        {"slug": "seo-keyword-research-tools", "topic": "SEO keyword research tools"},
        {"slug": "content-optimization-checklist", "topic": "content optimization checklist"},
        {"slug": "remote-team-collaboration", "topic": "remote team collaboration tips"},
    ]
    
    def plan_internal_links(
        self, 
        article: Article, 
        serp_analysis: SERPAnalysis
    ) -> List[InternalLinkSuggestion]:
        suggestions = []
        article_text_lower = (article.h1 + " " + article.body_markdown).lower()
        
        for page in self.INTERNAL_PAGES:
            page_topic_lower = page["topic"].lower()
            page_keywords = set(page_topic_lower.split())
            
            matches_serp = any(
                any(keyword in topic.lower() for keyword in page_keywords)
                for topic in serp_analysis.topics
            )
            
            matches_article = any(
                keyword in article_text_lower 
                for keyword in page_keywords
            )
            
            if matches_serp or matches_article:
                suggestions.append(
                    InternalLinkSuggestion(
                        anchor_text=page["topic"],
                        target_slug=page["slug"]
                    )
                )
        
        while len(suggestions) < 3 and len(suggestions) < len(self.INTERNAL_PAGES):
            for page in self.INTERNAL_PAGES:
                if len(suggestions) >= 3:
                    break
                if not any(s.target_slug == page["slug"] for s in suggestions):
                    suggestions.append(
                        InternalLinkSuggestion(
                            anchor_text=page["topic"],
                            target_slug=page["slug"]
                        )
                    )
        
        return suggestions[:5]  

    def plan_external_references(
        self, 
        serp_results: List[SERPResult], 
        outline: Outline
    ) -> List[ExternalReference]:
        references = []
        
        if not serp_results or len(serp_results) == 0:
            return references
        
        authoritative_domains = [".com", ".org", ".edu"]
        authoritative_results = [
            r for r in serp_results
            if any(domain in str(r.url) for domain in authoritative_domains)
        ]
        
        selected_results = authoritative_results[:4] if authoritative_results else serp_results[:4]
        
        for result in selected_results:
            best_section = None
            best_match_score = 0
            
            result_keywords = set(result.title.lower().split())
            
            for section in outline.sections:
                section_keywords = set(section.heading.lower().split())
                section_summary_keywords = set(section.summary.lower().split())
                all_section_keywords = section_keywords | section_summary_keywords
                
                overlap = len(result_keywords & all_section_keywords)
                if overlap > best_match_score:
                    best_match_score = overlap
                    best_section = section
            
            if not best_section and outline.sections:
                best_section = outline.sections[0]
            
            section_slug = best_section.slug if best_section else "introduction"
            context_reason = f"Use this when discussing {best_section.heading.lower()}" if best_section else "Useful reference for the topic"
            
            references.append(
                ExternalReference(
                    title=result.title,
                    url=result.url,
                    suggested_section_slug=section_slug,
                    context_reason=context_reason
                )
            )
        
        if len(references) < 2 and len(serp_results) >= 2:
            used_urls = {ref.url for ref in references}
            remaining = [r for r in serp_results if r.url not in used_urls][:2]
            for result in remaining[:2 - len(references)]:
                section_slug = outline.sections[0].slug if outline.sections else "introduction"
                references.append(
                    ExternalReference(
                        title=result.title,
                        url=result.url,
                        suggested_section_slug=section_slug,
                        context_reason="Useful reference for the topic"
                    )
                )
        
        return references[:4] if len(references) >= 2 else references

