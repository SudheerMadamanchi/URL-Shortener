from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from apps.shortener.enums import ExpirationTimeMonthEnum

import re
  

class ShortenUrlRequest(BaseModel):
    main_url: str
    expiration_time_month: ExpirationTimeMonthEnum = ExpirationTimeMonthEnum.six_months
    custom_domain: Optional[str] = None

    
    @field_validator("main_url", mode="before")
    def add_http_prefix_to_url(cls, value: str):
        if not re.match(r"^(http|https)://", value):
            value = "http://" + value
        return value

    @field_validator("main_url", mode="after")
    def validate_http_url(cls, value: str):
        url_regex = re.compile(
            r"^(https?://)"  # Protocol (http or https)
            r"((www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6})"  # Domain
            r"(/[^\s]*)?$"  # Path and query parameters
        )
        if not url_regex.match(value):
            raise ValueError("Invalid url")
        return value


class ShortenUrlResponse(BaseModel):
    main_url: str
    short_url: str
    custom_domain: Optional[str] = None
    created_at: str
    updated_at: str
    expires_at: str