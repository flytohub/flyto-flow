"""Request models for CE's local trigger utilities."""

from pydantic import BaseModel, Field


class CronValidateRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=100)
