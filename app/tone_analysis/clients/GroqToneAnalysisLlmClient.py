from groq import (
    AsyncGroq,
    AuthenticationError,
    GroqError,
    PermissionDeniedError,
    RateLimitError,
)
from groq.types.chat import ChatCompletion

from app.tone_analysis.clients.IToneAnalysisLlmClient import (
    IToneAnalysisLlmClient,
)
from app.tone_analysis.exceptions.ToneAnalysisUnavailableError import (
    ToneAnalysisUnavailableError,
)
from app.tone_analysis.models.LlmToneAnalysisResponse import (
    LlmToneAnalysisResponse,
)
from app.tone_analysis.models.ToneAnalysisAvailability import (
    ToneAnalysisAvailability,
)
from app.tone_analysis.prompts.ToneAnalysisPrompt import (
    ToneAnalysisPrompt,
)

#errors that exhaust the quota or reject the credentials apply to every
#article, unlike a malformed answer for a single one
UNAVAILABILITY_ERRORS = (
    RateLimitError,
    AuthenticationError,
    PermissionDeniedError,
)


class GroqToneAnalysisLlmClient(IToneAnalysisLlmClient):

    PROBE_MESSAGE = "ping"

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

    async def check_availability(self) -> ToneAnalysisAvailability:
        #one throwaway token is far cheaper than discovering an
        #exhausted quota once per article of the whole feed
        try:
            await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": self.PROBE_MESSAGE,
                    }
                ],
                max_completion_tokens=1,
            )
        except GroqError as error:
            return ToneAnalysisAvailability.unavailable(
                self._describe(error)
            )

        return ToneAnalysisAvailability.available()

    async def analyze_tone(
        self,
        *,
        title: str,
        summary: str,
    ) -> LlmToneAnalysisResponse:
        completion = await self._create_tone_completion(
            title=title,
            summary=summary,
        )
        content = completion.choices[0].message.content
        if content is None:
            raise ValueError("Groq returned an empty tone response.")

        return LlmToneAnalysisResponse.model_validate_json(content)

    async def _create_tone_completion(
        self,
        *,
        title: str,
        summary: str,
    ) -> ChatCompletion:
        try:
            return await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": ToneAnalysisPrompt.SYSTEM_MESSAGE,
                    },
                    {
                        "role": "user",
                        "content": (
                            ToneAnalysisPrompt.build_user_message(
                                title=title,
                                summary=summary,
                            )
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
        except UNAVAILABILITY_ERRORS as error:
            raise ToneAnalysisUnavailableError(
                self._describe(error)
            ) from error

    @staticmethod
    def _describe(error: GroqError) -> str:
        status_code = getattr(error, "status_code", None)
        if status_code is None:
            return f"Groq is unreachable ({type(error).__name__})."

        return (
            f"Groq rejected the request with status {status_code} "
            f"({type(error).__name__})."
        )

