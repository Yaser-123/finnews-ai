"""
LLM Usage Tracker

Tracks API calls, tokens, latency, failures, and cost estimation for Gemini LLM.
"""

from typing import Dict
import time


class UsageTracker:
    """Global usage tracker for LLM API calls."""
    
    def __init__(self):
        self.total_calls: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_failures: int = 0
        self.total_latency: float = 0.0
        self.avg_latency: float = 0.0
        self.cost_per_1m_tokens: float = 0.20  # Gemini 2.5 Flash approx (USD)
    
    def record_call(self, input_tokens: int, output_tokens: int, latency: float):
        """Record a successful LLM API call."""
        self.total_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_latency += latency
        self.avg_latency = self.total_latency / self.total_calls
    
    def record_failure(self):
        """Record a failed LLM API call."""
        self.total_failures += 1
    
    def get_stats(self) -> Dict:
        """Get current usage statistics with cost estimation."""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        cost_estimation = (total_tokens / 1_000_000) * self.cost_per_1m_tokens
        
        failure_rate = 0.0
        if (self.total_calls + self.total_failures) > 0:
            failure_rate = self.total_failures / (self.total_calls + self.total_failures)
        
        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": total_tokens,
            "total_failures": self.total_failures,
            "failure_rate": round(failure_rate, 4),
            "avg_latency_ms": round(self.avg_latency * 1000, 2),
            "cost_estimation_usd": round(cost_estimation, 6),
            "cost_per_1m_tokens_usd": self.cost_per_1m_tokens
        }
    
    def reset(self):
        """Reset all usage statistics."""
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_failures = 0
        self.total_latency = 0.0
        self.avg_latency = 0.0


# Global singleton instance
usage_tracker = UsageTracker()
