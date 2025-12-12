import re
from typing import List
from app.models.schemas import Article


class SEOValidator:
    
    def validate(self, article: Article) -> List[str]:
        errors = []
        
        # Calculate word count
        word_count = len(article.body_markdown.split())
        article.seo.estimated_word_count = word_count
        
        # Check primary keyword in H1
        primary_keyword_lower = article.seo.primary_keyword.lower()
        if primary_keyword_lower not in article.h1.lower():
            errors.append(f"Primary keyword '{article.seo.primary_keyword}' not found in H1")
        
        # Check primary keyword in first 150 words
        first_150_words = " ".join(article.body_markdown.split()[:150])
        if primary_keyword_lower not in first_150_words.lower():
            errors.append(f"Primary keyword '{article.seo.primary_keyword}' not found in first 150 words")
        
        # Check primary keyword in at least one H2 (allow near matches)
        h2_headings = self._extract_headings(article.body_markdown, level=2)
        h2_contains_keyword = self._check_keyword_match(primary_keyword_lower, h2_headings)
        if not h2_contains_keyword and len(h2_headings) > 0:
            errors.append(f"Primary keyword '{article.seo.primary_keyword}' not found in any H2 heading (or close match)")
        
        # Check word count (within ±20% of target)
        target = article.seo.word_count_target
        min_words = int(target * 0.8)
        max_words = int(target * 1.2)
        if word_count < min_words:
            errors.append(f"Word count {word_count} is below minimum {min_words} (80% of target {target})")
        elif word_count > max_words:
            errors.append(f"Word count {word_count} exceeds maximum {max_words} (120% of target {target})")
        
        # Check heading structure
        h1_count = len(self._extract_headings(article.body_markdown, level=1))
        if h1_count != 1:
            errors.append(f"Expected exactly 1 H1 heading, found {h1_count}")
        
        h2_count = len(h2_headings)
        if h2_count < 3:
            errors.append(f"Expected at least 3 H2 headings, found {h2_count}")
        
        # Check links
        if len(article.internal_links) < 3:
            errors.append(f"Expected at least 3 internal links, found {len(article.internal_links)}")
        
        if len(article.external_references) < 2:
            errors.append(f"Expected at least 2 external references, found {len(article.external_references)}")
        
        return errors
    
    def _extract_headings(self, markdown: str, level: int) -> List[str]:
        pattern = f"^#{{{level}}}\\s+(.+)$"
        matches = re.findall(pattern, markdown, re.MULTILINE)
        return matches
    
    def _check_keyword_match(self, keyword: str, headings: List[str]) -> bool:
        keyword_words = set(keyword.split())
        if not keyword_words:
            return False
        
        for heading in headings:
            heading_lower = heading.lower()
            if keyword in heading_lower:
                return True
        
            heading_words = set(heading_lower.split())
            matching_words = keyword_words & heading_words
            match_ratio = len(matching_words) / len(keyword_words)
            
            if match_ratio >= 0.5:
                return True
        
        return False

