import asyncio

import pytest

from app.scheduling.PeriodicScheduler import PeriodicScheduler


def test_scheduler_rejects_non_positive_interval() -> None:
    async def task() -> None:
        return None

    with pytest.raises(ValueError):
        PeriodicScheduler(
            name="test",
            interval_seconds=0,
            task=task,
        )


def test_scheduler_runs_task_on_a_fixed_interval() -> None:
    async def run_test() -> None:
        run_times: list[float] = []
        loop = asyncio.get_running_loop()
        third_run = asyncio.Event()

        async def task() -> None:
            run_times.append(loop.time())
            if len(run_times) == 3:
                third_run.set()

        scheduler = PeriodicScheduler(
            name="test",
            interval_seconds=0.05,
            task=task,
        )

        scheduler.start()
        try:
            async with asyncio.timeout(5):
                await third_run.wait()
        finally:
            await scheduler.stop()

        assert len(run_times) >= 3
        for previous, current in zip(
            run_times,
            run_times[1:],
            strict=False,
        ):
            assert current - previous == pytest.approx(0.05, abs=0.04)

    asyncio.run(run_test())


def test_scheduler_keeps_the_grid_when_a_run_is_slow() -> None:
    """A slow run must not push the following runs further away."""

    async def run_test() -> None:
        run_times: list[float] = []
        loop = asyncio.get_running_loop()
        started = loop.time()
        third_run = asyncio.Event()

        async def task() -> None:
            run_times.append(loop.time())
            if len(run_times) == 1:
                #overruns a full interval
                await asyncio.sleep(0.15)
            if len(run_times) == 3:
                third_run.set()

        scheduler = PeriodicScheduler(
            name="test",
            interval_seconds=0.1,
            task=task,
        )

        scheduler.start()
        try:
            async with asyncio.timeout(5):
                await third_run.wait()
        finally:
            await scheduler.stop()

        #the slow run swallows the 0.1 tick, so the next ones are 0.2/0.3
        assert run_times[1] - started == pytest.approx(0.2, abs=0.06)
        assert run_times[2] - started == pytest.approx(0.3, abs=0.06)

    asyncio.run(run_test())


def test_scheduler_keeps_running_after_a_failing_task() -> None:
    async def run_test() -> None:
        run_count = 0
        second_run = asyncio.Event()

        async def task() -> None:
            nonlocal run_count
            run_count += 1
            if run_count == 1:
                raise RuntimeError("boom")
            second_run.set()

        scheduler = PeriodicScheduler(
            name="test",
            interval_seconds=0.05,
            task=task,
        )

        scheduler.start()
        try:
            async with asyncio.timeout(5):
                await second_run.wait()
        finally:
            await scheduler.stop()

        assert run_count >= 2

    asyncio.run(run_test())


def test_scheduler_can_defer_the_first_run() -> None:
    async def run_test() -> None:
        run_count = 0

        async def task() -> None:
            nonlocal run_count
            run_count += 1

        scheduler = PeriodicScheduler(
            name="test",
            interval_seconds=10,
            task=task,
            run_immediately=False,
        )

        scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()

        assert run_count == 0

    asyncio.run(run_test())


def test_scheduler_stop_is_idempotent() -> None:
    async def run_test() -> None:
        async def task() -> None:
            return None

        scheduler = PeriodicScheduler(
            name="test",
            interval_seconds=10,
            task=task,
        )

        await scheduler.stop()
        scheduler.start()
        scheduler.start()
        await scheduler.stop()
        await scheduler.stop()

    asyncio.run(run_test())
