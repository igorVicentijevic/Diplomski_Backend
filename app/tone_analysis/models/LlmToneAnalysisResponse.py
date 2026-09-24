from pydantic import BaseModel, ConfigDict, Field


class LlmToneAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    negative: float = Field(ge=0, le=100)
    positive: float = Field(ge=0, le=100)
    neutral: float = Field(ge=0, le=100)
