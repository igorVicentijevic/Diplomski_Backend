from pydantic import BaseModel


class LlmToneAnalysisResponse(BaseModel):
    negative: float
    positive: float
    neutral: float
