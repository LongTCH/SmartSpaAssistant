# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent))
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


# Create FastAPI app instance at module level for ASGI servers to import
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    allow_headers=["*"],  # Allow all headers
)
# Add middleware from the separate middleware module
app.middleware("http")(catch_exceptions_middleware)

# Include all routes
include_router(app)

# Set up static files
os.makedirs("static", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Only run the server directly when this script is executed as the main program
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=env_config.SERVER_PORT)
