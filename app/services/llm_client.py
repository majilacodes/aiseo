import json
from typing import Dict
from openai import OpenAI


class LLMClient:
    
    def __init__(self, api_key: str, model: str = "gpt-5-mini-2025-08-07"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_json(self, prompt: str, schema_hint: str = "") -> Dict:
        try:
            full_prompt = prompt
            if schema_hint:
                full_prompt += f"\n\nReturn only valid JSON matching this structure: {schema_hint}"
            else:
                full_prompt += "\n\nReturn only valid JSON, no other text."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that returns only valid JSON."},
                    {"role": "user", "content": full_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    def generate_text(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that writes high-quality, SEO-optimized content."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")

