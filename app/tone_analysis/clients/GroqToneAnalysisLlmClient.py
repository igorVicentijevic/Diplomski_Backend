from groq import AsyncGroq

from app.tone_analysis.models.LlmToneAnalysisResponse import (
    LlmToneAnalysisResponse,
)
from app.tone_analysis.prompts.ToneAnalysisPrompt import (
    ToneAnalysisPrompt,
)


class GroqToneAnalysisLlmClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        groq_client: AsyncGroq | None = None,
    ) -> None:
        self._model = model
        self._client = groq_client or AsyncGroq(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )

    async def analyze_tone(
        self,
        *,
        title: str,
        summary: str,
    ) -> LlmToneAnalysisResponse:
        completion = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": ToneAnalysisPrompt.SYSTEM_MESSAGE,
                },
                {
                    "role": "user",
                    "content": ToneAnalysisPrompt.build_user_message(
                        title=title,
                        summary=summary,
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "tone_analysis",
                    "strict": True,
                    "schema": (
                        LlmToneAnalysisResponse.model_json_schema()
                    ),
                },
            },
            reasoning_effort="low",
            include_reasoning=False,
            max_completion_tokens=200,
        )
        content = completion.choices[0].message.content
        if content is None:
            raise ValueError("Groq returned an empty tone response.")

        return LlmToneAnalysisResponse.model_validate_json(content)
