import os
from contextlib import asynccontextmanager

import uvicorn
from app.configs import database, env_config
from app.middleware import catch_exceptions_middleware
from app.routes import include_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# cors config
origins = env_config.CLIENT_URLS.split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    await database.init_models()
    yield
    # Shutdown: Dispose of the engine
    await database.shutdown_models()


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)
# Add middleware from the separate middleware module
app.middleware("http")(catch_exceptions_middleware)

include_router(app)

os.makedirs("static", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=env_config.SERVER_PORT)
