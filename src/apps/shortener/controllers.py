import random

import string

import pytz

from datetime import datetime, timedelta

from redis.asyncio import Redis

from fastapi import HTTPException, status

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from apps.shortener.schemas import ShortenUrlRequest, ShortenUrlResponse
from apps.shortener.models import ShortenedUrl


class ShortenerController:
    @staticmethod
    def generate_random_characters(length: int) -> str:
        char_set = string.ascii_letters + string.digits
        return "".join(random.choice(char_set) for _ in range(length))
    
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
        shortened_url = ShortenedUrl(
            main_url=payload.main_url,
            short_url=short_url,
            created_at=datetime.utcnow(),  # Set created_at explicitly
            updated_at=datetime.utcnow(),  # Set updated_at explicitly
            expires_at=datetime.utcnow() + timedelta(hours=payload.expiration_time_month.value * 730),
        )
        db.add(shortened_url)
        await db.commit()
        return ShortenUrlResponse(
            main_url=payload.main_url,
            short_url=short_url,
            created_at=self.utc_to_ist(shortened_url.created_at).strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=self.utc_to_ist(shortened_url.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
            expires_at=self.utc_to_ist(shortened_url.expires_at).strftime("%Y-%m-%d %H:%M:%S"),
        )

    @staticmethod
    async def redirect_to_main_url(
        db: AsyncSession, redis: Redis, short_url: str
    ) -> str:
        main_url = await redis.get(short_url)
        if main_url:
            return main_url

        statement = select(ShortenedUrl).where(
            ShortenedUrl.short_url == short_url,
            ShortenedUrl.expired == False,
            ShortenedUrl.active == True,
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
