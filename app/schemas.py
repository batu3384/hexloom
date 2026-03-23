"""Pydantic request/response models for Hexloom."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TransformRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: str = Field(..., examples=["Hexloom"])
    method: str = Field(..., examples=["rot13"])


class TransformResponse(BaseModel):
    status: str
    result: str | None = None
    message: str | None = None
    clipboard_ready: bool = False


class BulkTransformRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[str] = Field(..., min_length=1, examples=[["Hexloom", "Hello World"]])
    method: str = Field(..., examples=["base64"])


class BulkTransformItemResponse(BaseModel):
    index: int
    input: str
    status: str
    result: str | None = None
    message: str | None = None
    clipboard_ready: bool = False


class BulkSummaryResponse(BaseModel):
    total: int
    success_count: int
    error_count: int


class BulkTransformResponse(BaseModel):
    status: str
    method: str
    operation: str
    clipboard_ready: bool = False
    combined_result: str | None = None
    summary: BulkSummaryResponse
    results: list[BulkTransformItemResponse]
