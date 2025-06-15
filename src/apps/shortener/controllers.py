import random

import string

import pytz
from fastapi import Request
from datetime import datetime, timedelta

from redis.asyncio import Redis

from fastapi import HTTPException, status

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from apps.shortener.schemas import ShortenUrlRequest, ShortenUrlResponse
from apps.shortener.models import ShortenedUrl
from core.config import AppConfig


class ShortenerController:
    @staticmethod
    def generate_random_characters(length: int) -> str:
        if length < 2:
           raise ValueError("Length must be at least 2 to include both letter and digit.")
        letters = string.ascii_letters
        digits = string.digits
        char_set = letters + digits
        # Ensure at least one letter and one digit
        code = [
            random.choice(letters),
            random.choice(digits),
        ] + [random.choice(char_set) for _ in range(length - 2)]
        random.shuffle(code)
        return ''.join(code)
    
    @staticmethod
    def utc_to_ist(utc_dt):
        ist = pytz.timezone("Asia/Kolkata")
        if utc_dt.tzinfo is None:
            utc_dt = pytz.utc.localize(utc_dt)
        return utc_dt.astimezone(ist)

    async def shorten(
        self, db: AsyncSession, payload: ShortenUrlRequest
    ) -> ShortenUrlResponse:
        short_url = self.generate_random_characters(length=5)

        # Pick custom domain if provided, otherwise fallback
        domain = payload.custom_domain or AppConfig.default_domain
        domain = domain.rstrip('/')  # Remove trailing slash if present

        full_short_url = f"{domain}/{short_url}"

        shortened_url = ShortenedUrl(
            main_url=payload.main_url,
            short_url=short_url,
            custom_domain=domain,
            created_at=datetime.utcnow(),  # Set created_at explicitly
            updated_at=datetime.utcnow(),  # Set updated_at explicitly
            expires_at=datetime.utcnow() + timedelta(hours=payload.expiration_time_month.value * 730),
        )
        db.add(shortened_url)
        await db.commit()
        return ShortenUrlResponse(
            main_url=payload.main_url,
            short_url=short_url,
            custom_domain=domain,
            created_at=self.utc_to_ist(shortened_url.created_at).strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=self.utc_to_ist(shortened_url.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
            expires_at=self.utc_to_ist(shortened_url.expires_at).strftime("%Y-%m-%d %H:%M:%S"),
        )

    @staticmethod
    async def redirect_to_main_url(
        db: AsyncSession, redis: Redis, short_url: str, request: Request
    ) -> str:
        host = request.headers.get("host")
        domain = f"http://{host}"

        redis_key = f"{domain}/{short_url}"
        main_url = await redis.get(redis_key)
        if main_url:
            return main_url

        statement = select(ShortenedUrl).where(
            ShortenedUrl.short_url == short_url,
            ShortenedUrl.expired == False,
            ShortenedUrl.active == True,
            (ShortenedUrl.custom_domain == domain) | (ShortenedUrl.custom_domain == None) | (ShortenedUrl.custom_domain == "")
        )
        results = await db.exec(statement)
        shortened_url: ShortenedUrl = results.first()
        if not shortened_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="shortened url not found",
            )
        
        if shortened_url.expires_at and shortened_url.expires_at < datetime.utcnow():
            shortened_url.expired = True
            shortened_url.updated_at = datetime.utcnow()
            db.add(shortened_url)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shortened URL has expired",
            )
        
        main_url = shortened_url.main_url

        await redis.set(
            name=short_url,
            value=main_url,
            ex=2 * 60,
        )

        return main_url


shortener_controller = ShortenerController()
