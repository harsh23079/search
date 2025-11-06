# Devenv Setup Guide

This project uses [devenv](https://devenv.sh/) for managing the development environment. Devenv provides a reproducible development environment using Nix.

## Quick Start

1. **Initialize devenv** (if not already done):
   ```bash
   devenv init
   ```

2. **Allow direnv** (if using direnv for automatic activation):
   ```bash
   direnv allow
   ```

3. **Start all services**:
   ```bash
   devenv up
   ```

   This will start:
   - Qdrant vector database (port 6333)
   - FastAPI server (port 8000)

4. **Access the services**:
   - FastAPI API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Qdrant Dashboard: http://localhost:6333/dashboard

## Available Commands

### Start Services
```bash
devenv up              # Start all services and processes
devenv shell           # Enter development shell
```

### Project Scripts
```bash
devenv run setup       # Setup project directories
devenv run test        # Run tests
devenv run format      # Format code with black
devenv run lint        # Lint code with flake8
```

### Manual Service Management
```bash
# Start Qdrant manually (if not using devenv up)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Run FastAPI manually
uv run uvicorn main:app --reload
```

## Environment Variables

All environment variables are configured in `devenv.nix`. They are automatically loaded when you enter the devenv shell.

Key variables:
- `QDRANT_HOST=localhost`
- `QDRANT_PORT=6333`
- `API_PORT=8000`
- `DEVICE=cpu` (change to `cuda` if you have GPU)

## Troubleshooting

### Devenv not found
```bash
# Install devenv
nix profile install github:cachix/devenv
```

### Services not starting
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Check FastAPI logs
devenv logs fastapi
```

### Port conflicts
If ports 6333 or 8000 are already in use:
1. Stop conflicting services
2. Or modify ports in `devenv.nix`

## Alternative: Using Docker Compose

If you prefer Docker Compose:
```bash
docker-compose up -d
```

This will start both Qdrant and the FastAPI container.

## Development Workflow

1. **Start development environment**:
   ```bash
   devenv up
   ```

2. **Make code changes** - FastAPI auto-reloads

3. **Test API endpoints**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

4. **View logs**:
   ```bash
   devenv logs
   ```

5. **Stop services**:
   ```bash
   # Press Ctrl+C or
   devenv down  # if available
   ```

## Notes

- Devenv uses Nix for package management
- UV is used for Python dependency management
- Services are managed by devenv's process manager
- All dependencies are reproducible and isolated

