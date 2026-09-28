import asyncio
import logging
import math
from collections.abc import Awaitable, Callable
from contextlib import suppress

logger = logging.getLogger(__name__)


class PeriodicScheduler:


    def __init__(
        self,
        name: str,
        interval_seconds: float,
        task: Callable[[], Awaitable[object]],
        run_immediately: bool = True,
    ) -> None:
        
        if interval_seconds <= 0:
            raise ValueError(
                "Scheduler interval must be greater than zero."
            )

        self._name = name
        self._interval_seconds = interval_seconds
        self._task = task
        self._run_immediately = run_immediately
        self._loop_task: asyncio.Task[None] | None = None

    @property
    def name(self) -> str:
        return self._name

    def start(self) -> None:
        if self._loop_task is None:

            self._loop_task = asyncio.create_task(
                self._run_forever(),
                name=f"scheduler:{self._name}",
            )


    async def stop(self) -> None:
        if self._loop_task is None:
            return

        self._loop_task.cancel()

        with suppress(asyncio.CancelledError):
            await self._loop_task

        self._loop_task = None

    async def _run_forever(self) -> None:

        loop = asyncio.get_running_loop()

        next_run = loop.time()

        if not self._run_immediately:
            next_run += self._interval_seconds

        while True:
            delay = next_run - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)

            await self._run_once()
            next_run = self._calculate_next_run(next_run, loop.time())

    async def _run_once(self) -> None:
        try:
            await self._task()
        except Exception:
            logger.exception(
                "Scheduled task %s failed.",
                self._name,
            )

    def _calculate_next_run(
        self,
        previous_run: float,
        now: float,
    ) -> float:
        
        next_run = previous_run + self._interval_seconds
        
        if next_run > now:
            return next_run

        missed_ticks = (
            math.floor(
                (now - next_run) / self._interval_seconds
            )
            + 1
        )
        logger.warning(
            "Scheduled task %s overran its interval, skipping %s tick(s).",
            self._name,
            missed_ticks,
        )
        return next_run + missed_ticks * self._interval_seconds
