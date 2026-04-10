# -*- coding: utf-8 -*-
"""Pydantic models for washed OpenAPI JSON structure."""

from pydantic import BaseModel, Field
from typing import Optional


class RequestSchema(BaseModel):
    """Request schema definition."""
    schema_ref: Optional[str] = Field(None, description="Original $ref reference")
    type: Optional[str] = Field(None, description="Field type, e.g. 'object', 'string'")
    required: Optional[list[str]] = Field(None, description="Required fields")


class ResponseSchema(BaseModel):
    """Response schema definition."""
    schema_ref: Optional[str] = Field(None, description="Original $ref reference")
    type: Optional[str] = Field(None, description="Field type")
    required: Optional[list[str]] = Field(None, description="Required fields")
    body: Optional[str] = Field(None, description="Body description like '*(无响应体)*'")


class Operation(BaseModel):
    """Single API operation."""
    operation_id: str = Field(..., description="Unique operation identifier")
    path: str = Field(..., description="API path, e.g. '/bcm/tools/execCmd/{hostName}/{port}'")
    method: str = Field(..., description="HTTP method: GET, POST, PUT, DELETE, PATCH")
    summary: str = Field("", description="Operation summary")
    description: str = Field("", description="Detailed description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    deprecated: bool = Field(False, description="Whether this operation is deprecated")
    request: Optional[RequestSchema] = Field(None, description="Request schema")
    response: Optional[ResponseSchema] = Field(None, description="Response schema")


class AppSpec(BaseModel):
    """Complete app specification from washed OpenAPI JSON."""
    app_name: str = Field(..., description="Application name")
    version: str = Field("", description="API version")
    description: str = Field("", description="App description/title")
    total_apis: int = Field(0, description="Total number of API operations")
    operations: list[Operation] = Field(default_factory=list, description="List of API operations")
