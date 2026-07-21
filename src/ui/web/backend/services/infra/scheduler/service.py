"""
Scheduler Service

Main service for executing workflows on schedule.
Supports cron/interval schedules and polling triggers.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError
from uuid import uuid4

from services.infra.scheduler.models import Schedule, ScheduleStatus
from services.infra.scheduler.cron_parser import CronParser
from services.infra.scheduler.repository import SchedulerRepository

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Scheduler service for executing workflows on schedule.

    Runs as a background task, polling for due schedules and triggering executions.
    """

    def __init__(
        self,
        execute_workflow: Callable[[str, Dict], Any],
        poll_interval_seconds: float = 60.0,
    ):
        """
        Initialize scheduler.

        Args:
            execute_workflow: Function to execute a workflow by ID
            poll_interval_seconds: How often to check for due schedules
        """
        self.execute_workflow = execute_workflow
        self.poll_interval_seconds = poll_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the scheduler background task."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Scheduler stopped")

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._process_due_schedules()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            await asyncio.sleep(self.poll_interval_seconds)

    async def _process_due_schedules(self) -> None:
        """Process all due schedules."""
        due_schedules = SchedulerRepository.get_due_schedules()

        for schedule in due_schedules:
            try:
                await self._trigger_schedule(schedule)
            except Exception as e:
                logger.error(f"Failed to trigger schedule {schedule.id}: {e}")
                SchedulerRepository.record_run(schedule.id, False)

    async def _trigger_schedule(self, schedule: Schedule) -> None:
        """Trigger a scheduled execution (regular or polling)."""
        if schedule.poll_url:
            await self._trigger_polling_schedule(schedule)
        else:
            await self._trigger_regular_schedule(schedule)

    async def _trigger_regular_schedule(self, schedule: Schedule) -> None:
        """Trigger a regular (cron/interval) scheduled execution."""
        logger.info(f"Triggering schedule: {schedule.name} (id={schedule.id})")

        try:
            # Execute workflow
            await self.execute_workflow(schedule.workflow_id, schedule.inputs)

            # Calculate next run
            next_run = self._calculate_next_run(schedule)
            SchedulerRepository.record_run(
                schedule.id, True,
                next_run.isoformat() if next_run else None,
            )

        except Exception as e:
            logger.error(f"Schedule execution failed: {e}")
            next_run = self._calculate_next_run(schedule)
            SchedulerRepository.record_run(
                schedule.id, False,
                next_run.isoformat() if next_run else None,
            )
            raise

    async def _trigger_polling_schedule(self, schedule: Schedule) -> None:
        """Poll an API endpoint and trigger workflow if data changed."""
        logger.info(f"Polling: {schedule.name} → {schedule.poll_url}")

        # Parse poll config
        config = {}
        if schedule.poll_config:
            try:
                config = json.loads(schedule.poll_config)
            except json.JSONDecodeError:
                pass

        method = config.get("poll_method", "GET")
        headers = config.get("poll_headers", {})
        body = config.get("poll_body")
        dedup_key = config.get("dedup_key", "")

        try:
            # Fetch data from the polled URL
            response_data = await self._poll_url(
                schedule.poll_url, method, headers, body
            )

            # Compute hash for dedup
            if dedup_key:
                dedup_value = self._extract_json_path(response_data, dedup_key)
                current_hash = hashlib.sha256(
                    json.dumps(dedup_value, sort_keys=True).encode()
                ).hexdigest()
            else:
                current_hash = hashlib.sha256(
                    json.dumps(response_data, sort_keys=True).encode()
                ).hexdigest()

            # Compare with last poll hash
            if current_hash == schedule.last_poll_hash:
                logger.debug(f"Polling {schedule.name}: no changes detected")
                # No changes — just update next_run_at without recording a run
                next_run = self._calculate_next_run(schedule)
                SchedulerRepository.update(
                    schedule.id,
                    next_run_at=next_run.isoformat() if next_run else None,
                )
                return

            # Data changed — trigger workflow
            logger.info(f"Polling {schedule.name}: change detected, triggering workflow")
            inputs = dict(schedule.inputs)
            inputs["_poll_data"] = response_data
            inputs["_poll_url"] = schedule.poll_url

            await self.execute_workflow(schedule.workflow_id, inputs)

            # Update poll state
            next_run = self._calculate_next_run(schedule)
            SchedulerRepository.update(
                schedule.id,
                last_poll_hash=current_hash,
                last_poll_data=json.dumps(response_data)[:10000],  # Cap stored data
            )
            SchedulerRepository.record_run(
                schedule.id, True,
                next_run.isoformat() if next_run else None,
            )

        except Exception as e:
            logger.error(f"Polling failed for {schedule.name}: {e}")
            next_run = self._calculate_next_run(schedule)
            SchedulerRepository.record_run(
                schedule.id, False,
                next_run.isoformat() if next_run else None,
            )

    @staticmethod
    async def _poll_url(
        url: str,
        method: str = "GET",
        headers: dict = None,
        body: dict = None,
    ) -> Any:
        """Fetch data from a URL (non-blocking via thread executor)."""
        import asyncio

        def _fetch():
            req_headers = {"Accept": "application/json"}
            if headers:
                req_headers.update(headers)
            data = json.dumps(body).encode() if body else None
            req = Request(url, data=data, headers=req_headers, method=method)
            with urlopen(req, timeout=30) as resp:
                content = resp.read().decode()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"raw": content}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)

    @staticmethod
    def _extract_json_path(data: Any, path: str) -> Any:
        """Simple JSON path extraction (supports $.key.key[0] format)."""
        if not path:
            return data

        # Strip leading $.
        path = path.lstrip("$").lstrip(".")
        current = data

        for part in path.replace("[", ".[").split("."):
            if not part:
                continue
            if part.startswith("[") and part.endswith("]"):
                idx_str = part[1:-1]
                try:
                    idx = int(idx_str)
                    current = current[idx]
                except (ValueError, IndexError, TypeError):
                    return None
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            if current is None:
                return None
        return current

    @staticmethod
    def _calculate_next_run(schedule: Schedule) -> Optional[datetime]:
        """Calculate next run time for a schedule."""
        if schedule.cron_expression:
            return CronParser.get_next_run(
                schedule.cron_expression,
                timezone_str=schedule.timezone,
            )
        elif schedule.interval_seconds:
            return datetime.now(timezone.utc) + timedelta(
                seconds=schedule.interval_seconds
            )
        return None

    @staticmethod
    async def create_schedule(
        name: str,
        workflow_id: str,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        inputs: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> Schedule:
        """
        Create a new schedule.

        Args:
            name: Schedule name
            workflow_id: Workflow to execute
            cron_expression: Cron expression (e.g., "0 9 * * *")
            interval_seconds: Interval in seconds (alternative to cron)
            inputs: Workflow input parameters
            user_id: Owner user ID
            **kwargs: Additional schedule fields

        Returns:
            Created schedule
        """
        if not cron_expression and not interval_seconds:
            raise ValueError("Either cron_expression or interval_seconds required")

        schedule = Schedule(
            id=str(uuid4()),
            name=name,
            workflow_id=workflow_id,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            inputs=inputs or {},
            user_id=user_id,
            **kwargs,
        )

        return SchedulerRepository.create(schedule)

    @staticmethod
    async def pause_schedule(schedule_id: str) -> bool:
        """Pause a schedule."""
        return SchedulerRepository.update(
            schedule_id,
            status=ScheduleStatus.PAUSED,
        )

    @staticmethod
    async def resume_schedule(schedule_id: str) -> bool:
        """Resume a paused schedule."""
        schedule = SchedulerRepository.get(schedule_id)
        if not schedule:
            return False

        # Recalculate next run
        if schedule.cron_expression:
            next_run = CronParser.get_next_run(
                schedule.cron_expression,
                timezone_str=schedule.timezone,
            )
        elif schedule.interval_seconds:
            next_run = datetime.now(timezone.utc) + timedelta(
                seconds=schedule.interval_seconds
            )
        else:
            next_run = None

        return SchedulerRepository.update(
            schedule_id,
            status=ScheduleStatus.ACTIVE,
            next_run_at=next_run.isoformat() if next_run else None,
        )

    @staticmethod
    async def trigger_now(schedule_id: str) -> bool:
        """Manually trigger a schedule immediately."""
        schedule = SchedulerRepository.get(schedule_id)
        if not schedule:
            return False

        # Set next_run_at to now
        now = datetime.now(timezone.utc).isoformat()
        return SchedulerRepository.update(schedule_id, next_run_at=now)
