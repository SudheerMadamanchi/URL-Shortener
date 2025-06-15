from sqlmodel import Field
from datetime import datetime
from typing import Optional
from utils.common_models import BaseModel


class ShortenedUrl(BaseModel, table=True):
    id: int | None = Field(primary_key=True)
    main_url: str = Field()
    short_url: str = Field(index=True)
    custom_domain: Optional[str] = Field(default=None, index=True)
    active: bool = Field(default=True)
    expired: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Ensure datetime format
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = Field(default=None)  # Ensure datetime format