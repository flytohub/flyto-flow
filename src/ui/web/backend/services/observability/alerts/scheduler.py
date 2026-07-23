"""
Alert Scheduler

Background scheduler that periodically evaluates alert rules.
Addresses OBS-2 from security audit.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from services.observability.alerts.manager import AlertManager
from services.observability.metrics.collector import get_collector

logger = logging.getLogger(__name__)


class AlertScheduler:
    """
    Background scheduler for alert rule evaluation.

    Runs on a configurable interval to evaluate all enabled alert rules
    against current metrics.
    """

    def __init__(
        self,
        manager: Optional[AlertManager] = None,
        evaluation_interval_seconds: int = 60,
    ):
        """
        Initialize alert scheduler.

        Args:
            manager: AlertManager instance (created if not provided)
            evaluation_interval_seconds: How often to evaluate rules (default 60s)
        """
        self._manager = manager or AlertManager()
        self._interval = evaluation_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_evaluation: Optional[str] = None
        self._evaluation_count = 0
        self._error_count = 0

    async def start(self) -> None:
        """Start the background scheduler."""
        if self._running:
            logger.warning("Alert scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"Alert scheduler started (interval={self._interval}s)"
        )

    async def stop(self) -> None:
        """Stop the background scheduler."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Alert scheduler stopped")

    async def _run_loop(self) -> None:
        """Main evaluation loop."""
        while self._running:
            try:
                await self._evaluate()
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._error_count += 1
                logger.error(f"Alert evaluation failed: {e}", exc_info=True)
                # Back off on repeated errors
                await asyncio.sleep(min(self._interval * 2, 300))

    async def _evaluate(self) -> None:
        """Perform one evaluation cycle."""
        try:
            # Collect current metrics
            metrics = await self._collect_metrics()

            # Evaluate all rules
            results = self._manager.evaluate_all(metrics)

            # Update stats
            self._evaluation_count += 1
            self._last_evaluation = datetime.now(timezone.utc).isoformat()

            # Log summary
            firing = sum(1 for r in results if r.is_firing())
            logger.debug(
                f"Alert evaluation complete: "
                f"{len(results)} rules, {firing} firing"
            )

        except Exception as e:
            logger.error(f"Error during alert evaluation: {e}")
            raise

    async def _collect_metrics(self) -> Dict[str, float]:
        """
        Collect current metrics for evaluation.

        Returns:
            Dictionary of metric name -> value
        """
        metrics = {}

        try:
            # Get system metrics from MetricsCollector
            collector = get_collector()
            system_metrics = {
                m.name: m.samples[-1].value
                for m in collector.get_all_metrics()
                if m.samples
            }
            metrics.update(system_metrics)
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")

        # Add queue metrics if available
        try:
            from gateway.storage.queue_factory import get_queue
            queue = await get_queue()
            stats = await queue.get_stats()
            metrics["queue_pending"] = stats.pending
            metrics["queue_running"] = stats.running
            metrics["queue_failed"] = stats.failed
            metrics["queue_total"] = stats.total
        except Exception as e:
            logger.debug(f"Queue metrics not available: {e}")

        # Add execution metrics if available
        try:
            from services.runtime.execution.service import get_execution_service
            service = get_execution_service()
            exec_stats = service.get_stats()
            metrics["executions_active"] = exec_stats.get("active", 0)
            metrics["executions_total"] = exec_stats.get("total", 0)
        except Exception as e:
            logger.debug(f"Execution metrics not available: {e}")

        return metrics

    def get_stats(self) -> Dict:
        """Get scheduler statistics."""
        return {
            "running": self._running,
            "interval_seconds": self._interval,
            "evaluation_count": self._evaluation_count,
            "error_count": self._error_count,
            "last_evaluation": self._last_evaluation,
        }

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running


# Global singleton
_scheduler: Optional[AlertScheduler] = None


def get_alert_scheduler() -> AlertScheduler:
    """Get or create the global alert scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AlertScheduler()
    return _scheduler


async def start_alert_scheduler() -> None:
    """Start the global alert scheduler."""
    scheduler = get_alert_scheduler()
    await scheduler.start()


async def stop_alert_scheduler() -> None:
    """Stop the global alert scheduler."""
    global _scheduler
    if _scheduler:
        await _scheduler.stop()
