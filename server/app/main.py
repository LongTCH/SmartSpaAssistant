import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import uvicorn
from app.configs import database, env_config
from app.middleware import catch_exceptions_middleware
from app.routes import v1_include_router, v2_include_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
app = FastAPI(
    title="Graduation Project API",
    description="""
## Graduation Project API Documentation

This API provides comprehensive endpoints for managing guests, interests, notifications, scripts, and sheets.

### Features:
- **Guest Management**: CRUD operations for guest data with filtering and pagination
- **Interest Management**: Handle interest categories with Excel import/export
- **Notification System**: Manage notifications with status tracking
- **Script Management**: Store and manage scripts with RAG integration
- **Sheet Management**: Dynamic sheet creation and management
- **File Operations**: Excel import/export capabilities
- **Real-time Updates**: WebSocket support for live updates

### Authentication:
Currently, the API does not require authentication for most endpoints.

### Response Format:
All endpoints return JSON responses with consistent error handling and proper HTTP status codes.
    """.strip(),
    version="1.0.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://example.com/contact/",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": f"http://localhost:{env_config.SERVER_PORT}",
            "description": "Development server (Local)",
        },
        {"url": "http://localhost/api", "description": "Local proxy server"},
        {"url": "https://farando.ddns.net/api", "description": "Production server"},
    ],
    lifespan=lifespan,
)

# CORS is handled by nginx proxy, but FastAPI still needs to handle OPTIONS
# Nginx hides FastAPI CORS headers, so no conflict
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
v1_include_router(app)
v2_include_router(app)

# Only run the server directly when this script is executed as the main program
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=env_config.SERVER_PORT)
