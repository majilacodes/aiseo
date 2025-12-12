from typing import List
from serpapi import GoogleSearch
from app.models.schemas import SERPResult


class SerpClient:
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search(self, query: str, limit: int = 10) -> List[SERPResult]:
        try:
            request_num = max(limit, 15)  # Request 15 to ensure we get at least 10
            
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google",
                "num": request_num
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            serp_results = []
            organic_results = results.get("organic_results", [])
            
            # Take up to the requested limit
            for idx, result in enumerate(organic_results[:limit], start=1):
                serp_results.append(
                    SERPResult(
                        rank=idx,
                        url=result.get("link", ""),
                        title=result.get("title", ""),
                        snippet=result.get("snippet", "")
                    )
                )
            
            return serp_results
            
        except Exception as e:
            raise Exception(f"SerpAPI search failed: {str(e)}")

