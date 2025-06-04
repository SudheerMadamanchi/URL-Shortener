from fastapi import FastAPI

from core import events
from core.router import initialize_routes

from middlewares.response_schema import response_schema_middleware

from core.config import redis_config 


app = FastAPI()


from core.config import database_config, redis_config

print("DB CONFIG:")
print("  username:", database_config.username)
print("  password:", database_config.password)
print("  database:", database_config.database)
print("  host:", database_config.host)
print("  port:", database_config.port)
print("REDIS CONFIG:")
print("  host:", redis_config.host)
print("  port:", redis_config.port)
print("  database:", redis_config.database)
print("  max_connections:", redis_config.max_connections)
print("  decode_responses:", redis_config.decode_responses)

@app.get("/")
def read_root():
    return {"Hello":"World"}

<<<<<<< HEAD
=======

>>>>>>> 2335dea925d6027c0d8620e56dede32ac8912028
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
