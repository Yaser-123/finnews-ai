"""
LLM Safety Guard

Implements content safety filters, citation enforcement, and hallucination prevention.
"""

import re
from typing import List


class SafetyViolationError(Exception):
    """Raised when content violates safety rules."""
    pass


class SafetyGuard:
    """Safety guard for LLM responses."""
    
    # Banned phrases that indicate financial advice
    BANNED_PHRASES = [
        "guaranteed returns",
        "sure profit",
        "risk-free investment",
        "buy now",
        "sell now",
        "certain gain",
        "no risk",
        "100% profit",
        "guaranteed profit",
        "can't lose",
        "definite returns"
    ]
    
    # Hallucination indicators
    HALLUCINATION_PATTERNS = [
        r"according to my analysis",
        r"in my opinion",
        r"i believe",
        r"i think",
        r"personally,",
        r"from my perspective"
    ]
    
    def normalize_response(self, text: str) -> str:
        """
        Normalize response text by removing extra whitespace and formatting.
        
        Args:
            text: Raw response text
        
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def block_financial_advice(self, text: str) -> str:
        """
        Block responses containing banned financial advice phrases.
        
        Args:
            text: Response text to check
        
        Returns:
            Original text if safe
        
        Raises:
            SafetyViolationError: If banned phrases detected
        """
        text_lower = text.lower()
        
        for phrase in self.BANNED_PHRASES:
            if phrase in text_lower:
                raise SafetyViolationError(
                    f"Response blocked: Contains financial advice phrase '{phrase}'. "
                    f"LLM should provide factual information only, not investment recommendations."
                )
        
        return text
    
    def remove_hallucinations(self, text: str) -> str:
        """
        Remove hallucination patterns like personal opinions.
        
        Args:
            text: Response text
        
        Returns:
            Text with hallucinations removed
        """
        for pattern in self.HALLUCINATION_PATTERNS:
            # Remove sentences containing hallucination patterns
            text = re.sub(
                pattern + r'[^.!?]*[.!?]',
                '',
                text,
                flags=re.IGNORECASE
            )
        
        return text.strip()
    
    def enforce_citations(self, text: str, sources: List[str] = None) -> str:
        """
        Ensure response includes citations to sources.
        
        Args:
            text: Response text
            sources: List of source identifiers
        
        Returns:
            Text with citations appended if missing
        """
        # Check if response already has citations
        has_citations = bool(re.search(r'sources?:', text, re.IGNORECASE))
        
        if not has_citations and sources:
            # Append sources
            sources_text = f"\n\nSources: {', '.join(sources)}"
            text = text + sources_text
        elif not has_citations:
            # Add generic citation reminder
            text = text + "\n\nNote: This summary is based on retrieved financial news articles."
        
        return text
    
    def sanitize(
        self,
        text: str,
        sources: List[str] = None,
        strict: bool = True
    ) -> str:
        """
        Apply all safety filters to response text.
        
        Args:
            text: Raw response text
            sources: Optional list of source identifiers
            strict: If True, raise errors on violations; if False, log warnings
        
        Returns:
            Sanitized text
        
        Raises:
            SafetyViolationError: If strict=True and violations detected
        """
        if not text:
            return ""
        
        # Step 1: Normalize
        text = self.normalize_response(text)
        
        # Step 2: Remove hallucinations
        text = self.remove_hallucinations(text)
        
        # Step 3: Block financial advice
        if strict:
            text = self.block_financial_advice(text)
        else:
            try:
                text = self.block_financial_advice(text)
            except SafetyViolationError:
                # In non-strict mode, just log and continue
                pass
        
        # Step 4: Enforce citations
        text = self.enforce_citations(text, sources)
        
        return text


# Global singleton instance
safety_guard = SafetyGuard()
