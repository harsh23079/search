# Fashion AI System

AI-powered fashion visual search, similarity matching, and outfit recommendation system.

## Features

- **Fashion Item Detection**: Detect clothing, shoes, bags, and accessories from images using YOLOv8
- **Visual Similarity Search**: Find visually similar products using FashionCLIP embeddings and Qdrant vector database
- **Outfit Recommendations**: Generate complete outfit recommendations based on anchor products
- **Style Compatibility Analysis**: Analyze compatibility between fashion items
- **Color Harmony Analysis**: Get color harmony recommendations and styling tips

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **YOLOv8**: Object detection for fashion items
- **FashionCLIP**: Vision-language model for fashion embeddings
- **Qdrant**: Vector database for similarity search
- **PyTorch**: Deep learning framework
- **UV**: Fast Python package manager

### Development
- **Devenv**: Reproducible development environment using Nix

## Quick Start

### Option 1: Using Devenv (Recommended)

1. **Start everything with one command**:
   ```bash
   devenv up
   ```

   This will automatically:
   - Start Qdrant vector database
   - Start FastAPI server with auto-reload
   - Set up all environment variables

2. **Access the services**:
   - **FastAPI API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Qdrant Dashboard**: http://localhost:6333/dashboard

### Option 2: Using Docker Compose

1. **Start services**:
   ```bash
   docker-compose up -d
   ```

2. **Run the application**:
   ```bash
   uv run uvicorn main:app --reload
   ```

### Option 3: Manual Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Start Qdrant**:
   ```bash
   docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

3. **Run the application**:
   ```bash
   uv run uvicorn main:app --reload
   ```

## API Endpoints

### Health Check
- `GET /api/v1/health` - Health check endpoint

### Detection
- `POST /api/v1/detect` - Detect fashion items in uploaded image

### Search
- `POST /api/v1/search/similar` - Search for visually similar products

### Outfit Recommendations
- `POST /api/v1/outfit/recommend` - Generate complete outfit recommendation

### Analysis
- `POST /api/v1/compatibility/analyze` - Analyze compatibility between items
- `POST /api/v1/color/harmony` - Analyze color harmony

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Using Devenv

```bash
# Enter development shell
devenv shell

# Run setup script
devenv run setup

# Run tests
devenv run test

# Format code
devenv run format

# Lint code
devenv run lint
```

### Manual Development Commands

```bash
# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run flake8 .
```

## Project Structure

```
search/
├── api/                   # FastAPI routes
│   ├── routes.py         # All API endpoints
│   └── __init__.py
├── config/                # Configuration
│   ├── settings.py       # Pydantic settings
│   └── __init__.py
├── models/                # Data models
│   ├── schemas.py        # Pydantic schemas
│   └── __init__.py
├── services/              # Business logic
│   ├── embedding_service.py      # FashionCLIP embeddings
│   ├── detection_service.py      # YOLOv8 detection
│   ├── vector_db_service.py      # Qdrant operations
│   ├── outfit_service.py         # Outfit recommendations
│   ├── color_service.py          # Color harmony analysis
│   └── __init__.py
├── devenv.nix            # Devenv configuration
├── docker-compose.yml    # Docker setup with Qdrant
├── Dockerfile            # Container definition
├── main.py               # FastAPI application entry point
├── pyproject.toml        # UV project config
└── README.md
```

## Configuration

Environment variables are configured in `devenv.nix` (for devenv) or `.env` file:

- **API Settings**: Host, port, debug mode
- **Qdrant**: Host, port, collection name
- **Models**: Model paths and device (CPU/CUDA)
- **Paths**: Upload, models, and log directories

## Notes

- The system uses FashionCLIP model for generating embeddings (512 dimensions)
- YOLOv8 model can be fine-tuned on fashion datasets for better detection
- Qdrant vector database is required for similarity search
- First model load may take time - models are cached after initial load
- Devenv provides a reproducible development environment using Nix

## Troubleshooting

### Devenv Issues

If `devenv up` doesn't work:
1. Check if Docker is running: `docker ps`
2. Check if ports 6333 and 8000 are available
3. Try manually: `docker-compose up -d` then `uv run uvicorn main:app`

### Model Loading

- First time loading models will download from HuggingFace
- Models are cached in `~/.cache/huggingface/`
- Set `DEVICE=cuda` in `devenv.nix` if you have GPU support

### Qdrant Connection

- Ensure Qdrant is running: `curl http://localhost:6333/health`
- Check Qdrant logs: `docker logs qdrant`

## License

MIT License
