# SSA (Smart Selling Assistant)

## Quick Start

### Local Development

```bash
# Start all services for development
docker-compose up -d

# View all logs
docker-compose logs -f

# View logs for a specific service (e.g., server, client)
docker-compose logs -f <service_name>

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Deploy to production
docker-compose -f docker-compose.production.yml up -d

# View all logs
docker-compose -f docker-compose.production.yml logs -f

# View logs for a specific service (e.g., server, client)
docker-compose -f docker-compose.production.yml logs -f <service_name>

# Stop services
docker-compose -f docker-compose.production.yml down
```

### Reset Database (Optional)

To reset the database with sample data, execute the following command, which runs the reset script directly within the `server` container:

```bash
# Run the database reset script in the development server container
docker-compose exec server python sampling/reset_db.py
```

**Note**: This command is intended for a development environment where the server container is built with development dependencies (`Faker`, etc.). The production server does not include these dependencies.

## Architecture

### Local Development (`docker-compose.yml`)

- **Database**: PostgreSQL with PGroonga extension for full-text search
- **Vector DB**: Qdrant for embeddings and vector search
- **Backend**: FastAPI server using `Dockerfile.dev` with both production and development dependencies.
- **Frontend**: Next.js with development server and hot reload (Dockerfile.dev)
- **Proxy**: Nginx with HTTP-only configuration for localhost

### Production (`docker-compose.production.yml`)

- **Database**: PostgreSQL with PGroonga extension and persistent volumes
- **Vector DB**: Qdrant with persistent storage
- **Backend**: FastAPI server optimized for production (standard Dockerfile)
- **Frontend**: Next.js production build (standard Dockerfile)
- **Proxy**: Nginx with HTTPS/SSL configuration

## Docker Files

The project uses different Dockerfiles for different purposes:

### Server

- **`Dockerfile`**: Production build with only `requirements.txt` dependencies
- **`Dockerfile.dev`**: Development build with both `requirements.txt` and `dev.requirements.txt` dependencies

### Web

- **`Dockerfile`**: Production build for Next.js
- **`Dockerfile.dev`**: Development build with hot reload support

### Dependencies

- **`server/requirements.txt`**: Production dependencies (FastAPI, SQLAlchemy, etc.)
- **`server/dev.requirements.txt`**: Development dependencies (Faker, pytest, black, etc.)

## Environment Files

Make sure you have the appropriate environment files:

- `./server/.env.development` - For local development
- `./server/.env.production` - For production deployment

## Services Access

### Local Development

- **Application**: http://localhost
- **API Docs**: http://localhost/docs
- **Database**: localhost:5432
- **Qdrant**: localhost:6333

### Production

- **Application**: https://yourdomain.com
- **API Docs**: https://yourdomain.com/docs
- **Database**: Internal network only
- **Qdrant**: Internal network only

## Docker Commands

```bash
# Build and start services
docker-compose up -d --build

# Build specific services
docker-compose build server  # Uses Dockerfile
docker-compose build client  # Uses Dockerfile.dev

# Execute commands in containers
docker-compose exec server bash
docker-compose exec client sh

# Stop and remove everything
docker-compose down -v
```

## Cleanup and Remove Services

### Remove All Services and Volumes

**Development Environment:**

```bash
# Stop and remove all services, networks, and volumes
docker-compose down -v

# Remove all including built images
docker-compose down -v --rmi all

# Complete system cleanup (removes all unused containers, networks, volumes)
docker system prune -a --volumes
```

**Production Environment:**

```bash
# Stop and remove all services, networks, and volumes for production
docker-compose -f docker-compose.production.yml down -v

# Remove all including built images
docker-compose -f docker-compose.production.yml down -v --rmi all
```

### Additional Cleanup Commands

```bash
# List remaining volumes
docker volume ls

# Remove specific volumes if needed
docker volume rm ssa_postgres_data ssa_qdrant_data

# Remove all unused volumes
docker volume prune

# Complete system cleanup (use with caution)
docker system prune -a --volumes
```

**⚠️ Warning**: These commands will permanently delete all data in your databases and volumes. Make sure to backup important data before running cleanup commands.

## Troubleshooting

### Environment files not found in containers

- Check `.dockerignore` files to ensure environment files are not excluded
- For development, make sure `.env` and `.env.development` files exist
- For production, make sure `.env.production` exists
