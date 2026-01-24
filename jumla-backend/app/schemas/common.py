"""
# ========== app/schemas/common.py ==========
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class TimestampMixin(BaseModel):
    """Mixin for timestamps"""
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    """Standard paginated response"""
    items: List[Any]
    total: int
    skip: int
    limit: int
