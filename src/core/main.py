from fastapi import FastAPI

from core import events
from core.router import initialize_routes

from middlewares.response_schema import response_schema_middleware

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello":"World"}

# Example: in main.py or core/main.py
from core.config import database_config, redis_config

print("DB HOST:", database_config.host)
print("DB USER:", database_config.username)
print("REDIS HOST:", redis_config.host)


response_schema_middleware(app)


@app.on_event("startup")
async def startup() -> None:
    await events.startup_event_handler()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await events.shutdown_event_handler()


@app.get("/ping")
def ping():
    return "pong!"


initialize_routes(app=app)
