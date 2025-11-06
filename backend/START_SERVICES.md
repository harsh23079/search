# Starting Services Guide

## Issue: Docker Required for Qdrant

The `devenv up` command requires Docker to be running for Qdrant. If Docker is not active, Qdrant won't start.

## Solution 1: Start Docker First

```bash
# Start Docker service
sudo systemctl start docker

# Or if using Docker Desktop
# Start Docker Desktop application

# Verify Docker is running
docker ps
```

Then run:
```bash
devenv up
```

## Solution 2: Manual Startup (Alternative)

If `devenv up` doesn't work, you can start services manually:

### Terminal 1: Start Qdrant
```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

### Terminal 2: Start FastAPI
```bash
cd /home/abhishek/dev/search
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Solution 3: Use Docker Compose

```bash
docker-compose up -d
```

This starts both Qdrant and optionally the FastAPI container.

## Verify Services

```bash
# Check Qdrant
curl http://localhost:6333/health

# Check FastAPI
curl http://localhost:8000/api/v1/health
```

## Troubleshooting

### Docker not accessible
- Check if Docker daemon is running: `systemctl status docker`
- Check user permissions: `groups` (should include docker)
- Try: `sudo usermod -aG docker $USER` then log out/in

### Ports already in use
- Check: `lsof -i :8000` or `lsof -i :6333`
- Kill process or change ports in `devenv.nix`

### Devenv processes not starting
- Check devenv logs: `ls -la .devenv/`
- Try: `devenv shell` to enter interactive shell
- Check for errors in terminal output

