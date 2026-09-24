from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToneAnalysisMetadata:
    input_hash: str
    provider: str
    model_name: str
    prompt_version: str
