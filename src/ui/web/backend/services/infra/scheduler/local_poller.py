"""
Local Schedule Poller

Desktop-mode scheduler that polls the Cloud API for due schedules
and executes them locally via the execution engine.

Architecture:
  Desktop app → poll Cloud API /api/triggers/schedules/due → get due list
  Desktop app → execute locally via ExecutionManager
  Desktop app → report result back to Cloud API (record_run)

Offline fallback:
  When Cloud API is unreachable, falls back to local SQLite (SchedulerRepository)
  so schedules continue running even without internet.

This keeps CRUD data in Firestore (single source of truth) while letting
the desktop app execute workflows on the local machine.
"""

import asyncio
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class LocalSchedulePoller:
    """
    Polls Cloud API for due schedules and executes them locally.

    Replaces the old SchedulerService loop that polled SQLite directly.
    Now data lives in Firestore, so we query via the Cloud API proxy.
    When cloud is unreachable, falls back to local SQLite cache.
    """

    def __init__(
        self,
        cloud_api_url: str,
        execute_fn,
        poll_interval_seconds: float = 60.0,
    ):
        self._cloud_api_url = cloud_api_url.rstrip("/")
        self._exec_manager = execute_fn
        self._poll_interval = poll_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("LocalSchedulePoller started")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("LocalSchedulePoller stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._poll_and_execute()
            except Exception as e:
                logger.error(f"Schedule poll error: {e}")
            await asyncio.sleep(self._poll_interval)

    async def _fetch_due_from_cloud(self) -> Optional[List[dict]]:
        """Fetch due schedules from Cloud API. Returns None if cloud unavailable."""
        try:
            from services.cloud_client import cloud_get
            due_list = await cloud_get("triggers/schedules/due")
            if due_list and isinstance(due_list, list):
                return due_list
            return []
        except Exception as e:
            logger.warning(f"Cloud API unavailable for schedule poll: {e}")
            return None

    def _fetch_due_from_sqlite(self) -> List[dict]:
        """Fallback: fetch due schedules from local SQLite cache."""
        try:
            from services.infra.scheduler.repository import SchedulerRepository
            schedules = SchedulerRepository.get_due_schedules()
            return [s.to_dict() for s in schedules]
        except Exception as e:
            logger.error(f"SQLite fallback failed: {e}")
            return []

    def _sync_to_sqlite(self, cloud_schedules: List[dict]) -> None:
        """Write-through: sync cloud schedules to local SQLite cache."""
        try:
            from services.infra.scheduler.repository import SchedulerRepository
            from services.infra.scheduler.models import Schedule

            for sched_data in cloud_schedules:
                schedule = Schedule.from_dict(sched_data)
                existing = SchedulerRepository.get(schedule.id)
                if existing:
                    SchedulerRepository.update(
                        schedule.id,
                        status=schedule.status.value,
                        next_run_at=schedule.next_run_at,
                        inputs=schedule.inputs,
                        run_count=schedule.run_count,
                        failure_count=schedule.failure_count,
                    )
                else:
                    SchedulerRepository.create(schedule)
        except Exception as e:
            logger.debug(f"SQLite sync failed (non-critical): {e}")

    async def _record_run(self, schedule_id: str, success: bool) -> None:
        """Report run result to Cloud API, fallback to SQLite if unavailable."""
        try:
            from services.cloud_client import cloud_post
            await cloud_post(
                f"triggers/schedules/{schedule_id}/record-run",
                json={"success": success},
            )
        except Exception as e:
            logger.warning(f"Cloud record_run failed, using SQLite fallback: {e}")
            try:
                from services.infra.scheduler.repository import SchedulerRepository
                SchedulerRepository.record_run(schedule_id, success=success)
            except Exception as e2:
                logger.error(f"SQLite record_run also failed: {e2}")

    async def _poll_and_execute(self) -> None:
        """Fetch due schedules from Cloud API (or SQLite fallback) and execute locally."""
        # Try cloud first
        due_list = await self._fetch_due_from_cloud()

        if due_list is not None:
            # Cloud available — sync to SQLite cache for offline fallback
            if due_list:
                self._sync_to_sqlite(due_list)
        else:
            # Cloud unavailable — use SQLite fallback
            logger.info("Using SQLite fallback for schedule polling")
            due_list = self._fetch_due_from_sqlite()

        if not due_list:
            return

        for sched in due_list:
            schedule_id = sched.get("id")
            if not schedule_id:
                continue

            try:
                inputs = dict(sched.get("inputs", {}))
                workflow_yaml = inputs.pop("_workflow_yaml", None)
                user_id = inputs.pop("_user_id", sched.get("user_id"))
                workflow_id = sched.get("workflow_id")

                if not workflow_yaml:
                    logger.warning(f"Schedule {schedule_id} missing _workflow_yaml, skipping")
                    continue

                # Execute locally
                execution_id = await self._exec_manager.start(
                    workflow_yaml=workflow_yaml,
                    variables=inputs,
                    workflow_id=workflow_id,
                    user_id=user_id,
                )
                logger.info(f"Scheduled execution started: {execution_id} (schedule={schedule_id})")

                # Report success
                await self._record_run(schedule_id, success=True)

            except Exception as e:
                logger.error(f"Schedule {schedule_id} execution failed: {e}")
                await self._record_run(schedule_id, success=False)
