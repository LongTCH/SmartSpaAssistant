from fastapi import FastAPI
import uvicorn
from app.route import router
from app.configs import database
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# cors config
origins = [
    "http://localhost:3000",
]


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

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)