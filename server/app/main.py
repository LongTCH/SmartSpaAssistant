from fastapi import FastAPI
import uvicorn
from app.route import router
from app.configs import database
from contextlib import asynccontextmanager
from app.configs.env_config import PAGE_ACCESS_TOKEN


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    await database.init_models()
    yield
    # Shutdown: Dispose of the engine
    await database.shutdown_models()

app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
