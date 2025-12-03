"""
LLM Monitoring API Routes

Endpoints for tracking LLM usage, health, and cost monitoring.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any

# Import usage tracker and rate limiter
from agents.llm.usage import usage_tracker
from agents.llm.limiter import rate_limiter

router = APIRouter()


class LLMStats(BaseModel):
    """LLM usage statistics model."""
    total_calls: int = Field(..., description="Total successful LLM API calls")
    total_input_tokens: int = Field(..., description="Total input tokens processed")
    total_output_tokens: int = Field(..., description="Total output tokens generated")
    total_tokens: int = Field(..., description="Total tokens (input + output)")
    total_failures: int = Field(..., description="Total failed API calls")
    failure_rate: float = Field(..., description="Failure rate (0.0 to 1.0)")
    avg_latency_ms: float = Field(..., description="Average latency in milliseconds")
    cost_estimation_usd: float = Field(..., description="Estimated cost in USD")
    cost_per_1m_tokens_usd: float = Field(..., description="Cost per 1M tokens in USD")


class LLMHealth(BaseModel):
    """LLM health status model."""
    status: str = Field(..., description="Health status: healthy, degraded, or capped")
    total_calls: int = Field(..., description="Total successful calls")
    total_failures: int = Field(..., description="Total failed calls")
    failure_rate: float = Field(..., description="Current failure rate")
    remaining_calls: int = Field(..., description="Remaining calls in current rate limit window")
    message: str = Field(..., description="Human-readable status message")


@router.get(
    "/stats",
    response_model=LLMStats,
    summary="Get LLM Usage Statistics",
    description="Returns comprehensive LLM usage statistics including calls, tokens, failures, latency, and cost estimation.",
    tags=["LLM"]
)
async def get_llm_stats() -> LLMStats:
    """
    Get current LLM usage statistics.
    
    Returns detailed metrics about LLM API usage:
    - Total calls and tokens
    - Failure rate
    - Average latency
    - Cost estimation based on Gemini 2.5 Flash pricing
    
    **Example Response:**
    ```json
    {
      "total_calls": 150,
      "total_input_tokens": 45000,
      "total_output_tokens": 15000,
      "total_tokens": 60000,
      "total_failures": 2,
      "failure_rate": 0.0132,
      "avg_latency_ms": 342.15,
      "cost_estimation_usd": 0.012,
      "cost_per_1m_tokens_usd": 0.20
    }
    ```
    """
    try:
        stats = usage_tracker.get_stats()
        return LLMStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving LLM stats: {str(e)}")


@router.get(
    "/health",
    response_model=LLMHealth,
    summary="Check LLM Health Status",
    description="Returns LLM health status based on failure rate and rate limiting. Status can be 'healthy', 'degraded', or 'capped'.",
    tags=["LLM"]
)
async def get_llm_health() -> LLMHealth:
    """
    Check LLM service health.
    
    Health status determination:
    - **healthy**: Failure rate < 10% and rate limits OK
    - **degraded**: Failure rate ≥ 10% (quality issues)
    - **capped**: Rate limit nearly exhausted (< 10 calls remaining)
    
    **Example Response:**
    ```json
    {
      "status": "healthy",
      "total_calls": 150,
      "total_failures": 2,
      "failure_rate": 0.0132,
      "remaining_calls": 55,
      "message": "LLM service is operating normally"
    }
    ```
    """
    try:
        stats = usage_tracker.get_stats()
        remaining_calls = rate_limiter.get_remaining_calls()
        
        total_calls = stats["total_calls"]
        total_failures = stats["total_failures"]
        failure_rate = stats["failure_rate"]
        
        # Determine health status
        if failure_rate >= 0.10:
            status = "degraded"
            message = f"LLM service is degraded: {failure_rate*100:.1f}% failure rate exceeds 10% threshold"
        elif remaining_calls < 10:
            status = "capped"
            message = f"Rate limit nearly exhausted: Only {remaining_calls} calls remaining in current window"
        else:
            status = "healthy"
            message = "LLM service is operating normally"
        
        return LLMHealth(
            status=status,
            total_calls=total_calls,
            total_failures=total_failures,
            failure_rate=failure_rate,
            remaining_calls=remaining_calls,
            message=message
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking LLM health: {str(e)}")


@router.post(
    "/reset",
    summary="Reset LLM Usage Statistics",
    description="Resets all LLM usage statistics to zero. Use with caution.",
    tags=["LLM"]
)
async def reset_llm_stats() -> Dict[str, str]:
    """
    Reset LLM usage statistics.
    
    **Warning:** This will reset all tracked usage data including:
    - Call counts
    - Token counts
    - Failure counts
    - Latency tracking
    
    This does NOT reset rate limiting windows.
    
    **Example Response:**
    ```json
    {
      "status": "success",
      "message": "LLM usage statistics have been reset"
    }
    ```
    """
    try:
        usage_tracker.reset()
        return {
            "status": "success",
            "message": "LLM usage statistics have been reset"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting LLM stats: {str(e)}")
