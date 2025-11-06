# Troubleshooting Devenv Services

## Common Issues

### 1. Qdrant Process Failing

**Error:** Docker daemon not running

**Solution:**
```bash
# Start Docker service
sudo systemctl start docker

# Verify Docker is running
docker ps

# Then restart devenv
devenv up
```

### 2. FastAPI Process Failing

**Error:** Import errors or module not found

**Solution:**
```bash
# Check if dependencies are installed
uv sync

# Test imports
uv run python -c "from main import app; print('OK')"

# Check logs
tail -f logs/app.log
```

### 3. Both Processes Failing

**Check:**
1. Docker is running (for Qdrant)
2. Dependencies are installed: `uv sync`
3. Ports are available: `lsof -i :8000` and `lsof -i :6333`

### 4. Manual Start (If devenv doesn't work)

**Terminal 1 - Qdrant:**
```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
```

**Terminal 2 - FastAPI:**
```bash
cd /home/abhishek/dev/search
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Check Process Status

In the Process Compose UI (devenv up):
- Press `F3` to see process info
- Press `F4` to see logs
- Check the exit code to understand why it failed

### 6. View Logs

```bash
# FastAPI logs
tail -f logs/app.log

# Qdrant logs (if running in Docker)
docker logs qdrant

# Devenv process logs
# Check the Process Compose UI logs section
```

