from pydantic import BaseModel

class RouteOutput(BaseModel):
    intent: str
    parameters: dict
    confidence: float