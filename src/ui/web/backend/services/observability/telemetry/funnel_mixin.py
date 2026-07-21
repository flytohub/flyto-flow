"""
Telemetry Funnel Mixin - get_funnel, get_predefined_funnels
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .constants import MAX_QUERY_DOCS

logger = logging.getLogger(__name__)


class TelemetryFunnelMixin:
    """Mixin for telemetry funnel analysis methods"""

    def get_funnel(
        self,
        steps: List[str],
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze conversion funnel

        Args:
            steps: List of event names in order (e.g., ["template.create", "template.save", "template.publish"])
            days: Time window in days

        Returns:
            Funnel analysis with conversion rates
        """
        if not self.collection:
            return {"ok": True, "steps": [], "overall_conversion": 0, "total_started": 0, "total_completed": 0, "days": days}
        try:
            if not steps or len(steps) < 2:
                return {"ok": False, "error": "At least 2 steps required"}

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_str = cutoff.isoformat() + "Z"

            # Get events for all steps
            query = self.collection.where("timestamp", ">=", cutoff_str).limit(MAX_QUERY_DOCS)
            docs = list(query.stream())

            # Group events by user and track which steps they completed
            user_steps: Dict[str, Dict[str, str]] = defaultdict(dict)  # user_id -> {step: timestamp}

            for doc in docs:
                data = doc.to_dict()
                event_name = data.get("event_name", "")
                user_id = data.get("user_id") or data.get("session_id")

                if not user_id or event_name not in steps:
                    continue

                timestamp = data.get("timestamp", "")

                # Only count if user hasn't done this step yet, or this is earlier
                if event_name not in user_steps[user_id]:
                    user_steps[user_id][event_name] = timestamp
                elif timestamp < user_steps[user_id][event_name]:
                    user_steps[user_id][event_name] = timestamp

            # Calculate funnel
            funnel_results = []
            prev_users = set()

            for i, step in enumerate(steps):
                # Users who completed this step
                step_users = set()
                for user_id, user_data in user_steps.items():
                    if step in user_data:
                        # Check if steps are in order (each step after previous)
                        if i == 0:
                            step_users.add(user_id)
                        elif user_id in prev_users:
                            # Verify this step happened after previous step
                            prev_step = steps[i - 1]
                            if prev_step in user_data and user_data[step] >= user_data[prev_step]:
                                step_users.add(user_id)

                count = len(step_users)
                first_step_count = len([u for u in user_steps if steps[0] in user_steps[u]]) if i == 0 else funnel_results[0]["count"]

                funnel_results.append({
                    "step": step,
                    "step_index": i,
                    "count": count,
                    "percentage": round(count / first_step_count * 100, 1) if first_step_count > 0 else 0,
                    "drop_off": len(prev_users) - count if i > 0 else 0,
                    "conversion_from_prev": round(count / len(prev_users) * 100, 1) if prev_users else 100
                })

                prev_users = step_users

            # Overall conversion
            first_count = funnel_results[0]["count"] if funnel_results else 0
            last_count = funnel_results[-1]["count"] if funnel_results else 0
            overall_conversion = round(last_count / first_count * 100, 1) if first_count > 0 else 0

            return {
                "ok": True,
                "steps": funnel_results,
                "overall_conversion": overall_conversion,
                "total_started": first_count,
                "total_completed": last_count,
                "days": days
            }

        except Exception as e:
            logger.error(f"Failed to get funnel: {e}")
            return {"ok": False, "error": str(e)}

    def get_predefined_funnels(self, days: int = 7) -> Dict[str, Any]:
        """
        Get predefined funnel analyses

        Returns:
            Multiple funnel analyses
        """
        if not self.collection:
            return {"ok": True, "funnels": {}, "days": days}
        try:
            funnels = {}

            # Template Publishing Funnel
            funnels["template_publish"] = self.get_funnel(
                ["template.create", "template.save", "template.publish"],
                days=days
            )

            # Workflow Execution Funnel
            funnels["workflow_execution"] = self.get_funnel(
                ["template.create", "workflow.execute_start", "workflow.execute_complete"],
                days=days
            )

            # Marketplace Funnel
            funnels["marketplace"] = self.get_funnel(
                ["page.view", "marketplace.search", "marketplace.install"],
                days=days
            )

            # Purchase Funnel
            funnels["purchase"] = self.get_funnel(
                ["marketplace.search", "marketplace.purchase_start", "marketplace.purchase_complete"],
                days=days
            )

            return {"ok": True, "funnels": funnels, "days": days}

        except Exception as e:
            logger.error(f"Failed to get predefined funnels: {e}")
            return {"ok": False, "error": str(e)}
