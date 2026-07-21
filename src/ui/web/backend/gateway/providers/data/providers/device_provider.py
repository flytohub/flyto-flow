"""Device provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from services.device.job_models import ExecutionJob, JobStatus
    from services.device.models import Device


class DeviceProvider(ABC):
    """Provider interface for runner device, job, wake, and push operations."""

    @abstractmethod
    def create_device(self, device: Device) -> Device:
        """Register or update a runner device."""
        pass

    @abstractmethod
    def get_device(self, device_id: str) -> Optional[Device]:
        """Return a registered device by id."""
        pass

    @abstractmethod
    def list_devices_by_user(self, user_id: str) -> list[Device]:
        """List active devices for a user."""
        pass

    @abstractmethod
    def list_devices_by_workspace(self, workspace_id: str) -> list[Device]:
        """List active devices in a workspace."""
        pass

    @abstractmethod
    def update_device_heartbeat(
        self,
        device_id: str,
        local_url: str | None = None,
    ) -> bool:
        """Update device heartbeat and optional local URL."""
        pass

    @abstractmethod
    def mark_device_offline(self, device_id: str) -> bool:
        """Mark a device offline."""
        pass

    @abstractmethod
    def increment_device_processed(self, device_id: str) -> None:
        """Increment processed-event count for a device."""
        pass

    @abstractmethod
    def set_remote_wake(self, device_id: str, enabled: bool) -> bool:
        """Enable or disable remote wake for a device."""
        pass

    @abstractmethod
    def update_daemon_heartbeat(self, device_id: str) -> bool:
        """Update wake-daemon heartbeat for a device."""
        pass

    @abstractmethod
    def revoke_device(self, device_id: str, user_id: str) -> bool:
        """Revoke a device, verifying ownership."""
        pass

    @abstractmethod
    def delete_device(self, device_id: str, user_id: str) -> bool:
        """Delete a device, verifying ownership."""
        pass

    @abstractmethod
    def create_job(self, job: ExecutionJob) -> ExecutionJob:
        """Create an execution job."""
        pass

    @abstractmethod
    def get_job(self, job_id: str) -> Optional[ExecutionJob]:
        """Return an execution job by id."""
        pass

    @abstractmethod
    def list_jobs_by_user(self, user_id: str, limit: int = 20) -> list[ExecutionJob]:
        """List recent jobs for a user."""
        pass

    @abstractmethod
    def find_active_job_by_template_id(
        self,
        template_id: str,
        user_id: str,
    ) -> Optional[ExecutionJob]:
        """Return the most recent active job for a user/template pair."""
        pass

    @abstractmethod
    def poll_pending_jobs(self, device_id: str, limit: int = 1) -> list[ExecutionJob]:
        """Return pending jobs for a device."""
        pass

    @abstractmethod
    def claim_job(self, job_id: str, device_id: str) -> bool:
        """Atomically claim a pending job."""
        pass

    @abstractmethod
    def update_job_progress(
        self,
        job_id: str,
        current_step_index: int,
        total_steps: int,
        current_node_id: str | None = None,
        status: JobStatus | None = None,
        step_id: str | None = None,
        step_result: dict | None = None,
    ) -> bool:
        """Update execution job progress."""
        pass

    @abstractmethod
    def complete_job(
        self,
        job_id: str,
        status: JobStatus,
        error: str | None = None,
        variables: dict | None = None,
        node_outputs: dict | None = None,
    ) -> bool:
        """Mark an execution job terminal."""
        pass

    @abstractmethod
    def get_next_streaming_step(self, job_id: str, user_id: str) -> Optional[dict]:
        """Return the next streaming job step for the owner."""
        pass

    @abstractmethod
    def save_streaming_step_result(
        self,
        job_id: str,
        user_id: str,
        step_id: str,
        step_index: int,
        result: Any,
        status: str = "success",
        error: str | None = None,
    ) -> bool:
        """Save a streaming step result and advance the job."""
        pass

    @abstractmethod
    def stream_pending_jobs_for_devices(self, device_ids: list[str]) -> list[dict]:
        """Return pending job payloads across devices."""
        pass

    @abstractmethod
    def get_raw_template_steps(self, template_id: str) -> Optional[list]:
        """Return raw template steps for streaming execution."""
        pass

    @abstractmethod
    def cancel_job(self, job_id: str, user_id: str) -> bool:
        """Cancel a non-terminal execution job."""
        pass

    @abstractmethod
    async def register_fcm_token(self, user_id: str, token: str) -> None:
        """Store an FCM token for push notifications."""
        pass

    @abstractmethod
    async def notify_device_online(self, user_id: str, device_name: str) -> None:
        """Notify a user that a device came online."""
        pass

    @abstractmethod
    async def notify_device_offline(self, user_id: str, device_name: str) -> None:
        """Notify a user that a device went offline."""
        pass

    @abstractmethod
    async def notify_job_complete(
        self,
        user_id: str,
        job_id: str,
        status: str,
        template_name: str,
    ) -> None:
        """Notify a user that a job completed."""
        pass

    @abstractmethod
    async def notify_breakpoint_pending(
        self,
        user_id: str,
        breakpoint_id: str,
        execution_id: str,
        title: str,
        is_interact: bool = False,
    ) -> None:
        """Notify a user that a breakpoint needs action."""
        pass

    @abstractmethod
    def create_wake_command(self, device_id: str, user_id: str) -> None:
        """Create a remote wake command."""
        pass

    @abstractmethod
    def poll_wake_commands(self, device_id: str) -> tuple[bool, str | None]:
        """Poll and consume pending remote wake commands."""
        pass
