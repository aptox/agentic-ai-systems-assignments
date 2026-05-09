from typing import Any

from pydantic import BaseModel, Field


class RouteOutput(BaseModel):
    """
    Structured classification output from the ClassifierAgent.

    Produced using SDK-native structured output (output_type parameter)
    and validated by Pydantic before use.
    """
    intent: str = Field(
        description="The classified intent: getWeather, calculateMath, getExchangeRate, or generalChat."
    )
    parameters: dict[str, Any] = Field(
        description="Extracted parameters relevant to the intent (e.g. city, expression, currency codes)."
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1 for the classification."
    )
