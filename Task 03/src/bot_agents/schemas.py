from typing import Any, List, Literal

from pydantic import BaseModel, Field


class RouteOutput(BaseModel):
    """
    Structured classification output from the ClassifierAgent.

    Produced using SDK-native structured output (output_type parameter)
    and validated by Pydantic before use.
    """
    intent: str = Field(
        description=(
            "The classified intent: getWeather, calculateMath, "
            "getExchangeRate, analyzeReview, or generalChat."
        )
    )
    parameters: dict[str, Any] = Field(
        description=(
            "Extracted parameters relevant to the intent "
            "(e.g. city, expression, currency codes, reviewText)."
        )
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1 for the classification."
    )


class ReviewAspect(BaseModel):
    """One aspect extracted from a review (e.g. Food, Service, Price)."""
    topic: str = Field(description="Aspect topic (e.g. Food, Service, Price, Atmosphere).")
    sentiment: Literal["Positive", "Negative", "Neutral"] = Field(
        description="Sentiment for this specific aspect."
    )
    detail: str = Field(description="Verbatim or paraphrased evidence from the review text.")


class ReviewOutput(BaseModel):
    """
    Structured ABSA output produced by ReviewAnalyzerAgent.

    Validated before display and before the self-correction sanity check.
    """
    summary: str = Field(description="One concise sentence summarising the whole review.")
    overall_sentiment: Literal["Positive", "Negative", "Neutral", "Mixed"] = Field(
        description="Overall sentiment label for the review."
    )
    score: int = Field(description="Overall score from 1 (worst) to 10 (best).", ge=1, le=10)
    aspects: List[ReviewAspect] = Field(
        description="List of aspect-level sentiment entries extracted from the review."
    )
