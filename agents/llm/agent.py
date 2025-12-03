import google.generativeai as genai
from google.generativeai import GenerativeModel
import os
import json
import time
from typing import Dict, Any, List

# Import usage tracking, rate limiting, and safety
from agents.llm.usage import usage_tracker
from agents.llm.limiter import rate_limiter, LLMRateLimitError
from agents.llm.safety import safety_guard, SafetyViolationError


class LLMAgent:
    def __init__(self, api_key: str = None):
        """
        Initialize the LLMAgent with Google Gemini 2.5 Flash.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        # Configure Gemini API
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it as an environment variable "
                "or pass it to the constructor."
            )
        
        genai.configure(api_key=api_key)
        self.model = GenerativeModel("gemini-2.5-flash")
        
        # System prompts for different tasks
        self.query_expansion_prompt = """Expand this financial query into a detailed, richer form without changing user intent. 
Add related financial context, synonyms, sector references, regulatory angles, and trader-relevant keywords. 
Output only the expanded query text without any additional formatting or explanation."""
        
        self.summarization_prompt = """Summarize this financial news article in 2 sentences for a trader.
Focus on stock impact, regulatory moves, risks, opportunities, and sentiment.
Be concise, accurate, and trader-centric."""
        
        self.regulation_prompt = """Explain the regulatory impact of this financial update.
List affected sectors and expected market reaction.
Return your response in JSON format with the following structure:
{
  "impact": "brief impact description",
  "affected_sectors": ["sector1", "sector2"],
  "risk_level": "Low/Medium/High",
  "explanation": "detailed explanation"
}"""
    
    def _safe_generate(self, prompt: str, max_retries: int = 3, sources: List[str] = None) -> str:
        """
        Safely generate content with rate limiting, usage tracking, and safety checks.
        
        Args:
            prompt: The prompt to send to the LLM
            max_retries: Maximum number of retries on rate limit errors
            sources: Optional list of source identifiers for citations
        
        Returns:
            Sanitized response text
        
        Raises:
            LLMRateLimitError: If rate limit exceeded after retries
            SafetyViolationError: If response violates safety rules
        """
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Check rate limiter
                rate_limiter.allow_call()
                
                # Track start time
                start_time = time.time()
                
                # Generate content
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Calculate latency
                latency = time.time() - start_time
                
                # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
                input_tokens = len(prompt) // 4
                output_tokens = len(response_text) // 4
                
                # Record successful call
                usage_tracker.record_call(input_tokens, output_tokens, latency)
                rate_limiter.register_call()
                
                # Apply safety sanitization
                sanitized_text = safety_guard.sanitize(response_text, sources=sources)
                
                return sanitized_text
            
            except LLMRateLimitError as e:
                usage_tracker.record_failure()
                last_error = e
                retry_count += 1
                
                if retry_count < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** (retry_count - 1)
                    time.sleep(wait_time)
                else:
                    raise
            
            except SafetyViolationError:
                usage_tracker.record_failure()
                raise
            
            except Exception as e:
                usage_tracker.record_failure()
                raise
        
        # If we exhausted retries
        if last_error:
            raise last_error
        
        raise Exception("Unexpected error in _safe_generate")
    
    def expand_query(self, query_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Expand a financial query to improve search relevance.
        
        Args:
            query_dict: Dict with "query" key containing the original query
            
        Returns:
            Dict with "original" and "expanded" keys
        """
        original_query = query_dict.get("query", "")
        
        if not original_query:
            return {"original": "", "expanded": ""}
        
        try:
            # Generate expanded query using safe wrapper
            prompt = f"{self.query_expansion_prompt}\n\nQuery: {original_query}"
            expanded_query = self._safe_generate(prompt)
            
            return {
                "original": original_query,
                "expanded": expanded_query
            }
        
        except (LLMRateLimitError, SafetyViolationError) as e:
            # Return original query on rate limit or safety errors
            return {
                "original": original_query,
                "expanded": original_query,
                "error": str(e)
            }
        
        except Exception as e:
            # Fallback to original query on error
            return {
                "original": original_query,
                "expanded": original_query,
                "error": str(e)
            }
    
    def summarize_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a concise, trader-focused summary of a financial article.
        
        Args:
            article: Article dict with "id", "text", and optionally "sentiment"
            
        Returns:
            Dict with "id", "summary", and "sentiment" keys
        """
        article_id = article.get("id")
        text = article.get("text", "")
        sentiment = article.get("sentiment", {})
        
        if not text:
            return {
                "id": article_id,
                "summary": "No text available for summarization.",
                "sentiment": sentiment
            }
        
        try:
            # Generate summary using safe wrapper
            prompt = f"{self.summarization_prompt}\n\nArticle: {text}"
            sources = [f"Article ID: {article_id}"]
            summary = self._safe_generate(prompt, sources=sources)
            
            return {
                "id": article_id,
                "summary": summary,
                "sentiment": sentiment
            }
        
        except (LLMRateLimitError, SafetyViolationError) as e:
            return {
                "id": article_id,
                "summary": f"Unable to generate summary: {str(e)}",
                "sentiment": sentiment
            }
        
        except Exception as e:
            return {
                "id": article_id,
                "summary": f"Error generating summary: {str(e)}",
                "sentiment": sentiment
            }
    
    def interpret_regulation(self, regulatory_text: str) -> Dict[str, Any]:
        """
        Analyze regulatory news and provide structured impact assessment.
        
        Args:
            regulatory_text: Text describing a regulatory update or policy change
            
        Returns:
            Dict with impact, affected_sectors, risk_level, and explanation
        """
        if not regulatory_text:
            return {
                "impact": "No text provided",
                "affected_sectors": [],
                "risk_level": "Unknown",
                "explanation": "Empty input"
            }
        
        try:
            # Generate regulatory interpretation using safe wrapper
            prompt = f"{self.regulation_prompt}\n\nRegulatory Update: {regulatory_text}"
            response_text = self._safe_generate(prompt)
            
            # Remove markdown code block if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["impact", "affected_sectors", "risk_level", "explanation"]
            if not all(field in result for field in required_fields):
                raise ValueError("Missing required fields in response")
            
            return result
        
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return {
                "impact": "Unable to parse structured response",
                "affected_sectors": ["Unknown"],
                "risk_level": "Unknown",
                "explanation": f"JSON parsing error: {str(e)}"
            }
        
        except (LLMRateLimitError, SafetyViolationError) as e:
            return {
                "impact": f"Safety/Rate limit error: {str(e)}",
                "affected_sectors": [],
                "risk_level": "Unknown",
                "explanation": ""
            }
        
        except Exception as e:
            return {
                "impact": f"Error analyzing regulation: {str(e)}",
                "affected_sectors": [],
                "risk_level": "Unknown",
                "explanation": ""
            }
    
    def run(self, articles: List[Dict[str, Any]], operation: str = "summarize") -> List[Dict[str, Any]]:
        """
        Process a batch of articles with the specified LLM operation.
        
        Args:
            articles: List of article dicts
            operation: Operation to perform ("summarize", "expand", "interpret")
            
        Returns:
            List of processed articles
        """
        if operation == "summarize":
            return [self.summarize_article(article) for article in articles]
        else:
            # For now, just return articles unchanged for other operations
            return articles
