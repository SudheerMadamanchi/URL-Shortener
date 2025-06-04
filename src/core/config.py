from typing import Optional
from pydantic_settings import BaseSettings as PydanticBaseConfig


class BaseConfig(PydanticBaseConfig):
    model_config = {
        "env_file": "src/.env"
    }

class AppConfig(BaseConfig):
    secret_key: str = "secret_key"
    debug: bool = True

    model_config = {
        "env_prefix": "APP_",
        "env_file": "src/.env"
    }

app_config = AppConfig()


class DatabaseConfig(BaseConfig):
    username: str = "postgres"
    password: str = "admin"
    database: str = "url_shortener"
    host: str = "localhost"
    port: int = 5432
    pool_size: int = 10
    max_overflow: int = 5
    echo: bool = (
        True  # True means write sql queries in std.out. Set False in production.
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    model_config = {
        "env_prefix": "DB_",
        "env_file": "src/.env"
    }


database_config = DatabaseConfig()


class RedisCpConfig(BaseConfig):
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    max_connections: int = 10
    decode_responses: bool = True
    password: Optional[str] = None 

    @property
    def redis_url(self) -> str:
        if self.password is None:
            return f"redis://{self.host}:{self.port}/{self.database}"
        else:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.database}"

    model_config = {
        "env_prefix": "REDIS_",
        "env_file": "src/.env"
    }

redis_config = RedisCpConfig()
