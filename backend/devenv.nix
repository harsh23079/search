{ pkgs, lib, config, ... }:

{
  # Python environment (using system Python since we use UV)
  languages.python = {
    enable = true;
    package = pkgs.python3;
  };

  # Packages to include
  packages = with pkgs; [
    # Python package manager
    uv
    
    # Development tools
    git
    curl
    jq
    
    # System dependencies for ML libraries
    zlib
    libjpeg
    libpng
    openblas
    gfortran
    docker
    docker-compose
  ];

  # Processes to run
  processes = {
    # Qdrant vector database (using Docker)
    qdrant = {
      exec = ''
        if ! command -v docker &> /dev/null; then
          echo "Docker not found. Please install Docker or start Docker service."
          exit 1
        fi
        
        if ! docker info &> /dev/null; then
          echo "Docker daemon not running. Please start Docker service: sudo systemctl start docker"
          exit 1
        fi
        
        if ! docker ps | grep -q qdrant; then
          docker run --rm -d \
            --name qdrant \
            -p 6333:6333 \
            -p 6334:6334 \
            -v qdrant_storage:/qdrant/storage \
            qdrant/qdrant:latest || exit 1
        else
          docker start qdrant 2>/dev/null || exit 1
        fi
        
        # Keep process running
        while docker ps | grep -q qdrant; do
          sleep 5
        done
      '';
    };
    
    # FastAPI server
    fastapi = {
      exec = ''
        set -e
        
        # Kill any existing process on port 8000
        if command -v lsof &> /dev/null; then
          lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        elif command -v fuser &> /dev/null; then
          fuser -k 8000/tcp 2>/dev/null || true
        fi
        
        # Wait a moment for port to be released
        sleep 1
        
        # Sync dependencies
        uv sync
        
        # Run FastAPI
        exec uv run uvicorn main:app \
          --host 0.0.0.0 \
          --port 8000 \
          --reload
      '';
    };
  };

  # Environment variables
  env = {
    QDRANT_HOST = "localhost";
    QDRANT_PORT = "6333";
    QDRANT_COLLECTION_NAME = "fashion_products";
    QDRANT_EMBEDDING_DIM = "512";
    API_HOST = "0.0.0.0";
    API_PORT = "8000";
    API_DEBUG = "true";
    DEVICE = "cpu";  # Change to "cuda" if you have GPU
    FASHIONCLIP_MODEL_NAME = "patrickjohncyh/fashion-clip";
    YOLO_MODEL_PATH = "./models/yolov8_fashion.pt";
    UPLOAD_DIR = "./uploads";
    MODELS_DIR = "./models";
    LOG_DIR = "./logs";
  };

  # Tasks for running commands
  tasks = {
    setup = {
      exec = ''
        echo "Setting up Fashion AI project..."
        mkdir -p uploads models logs
        touch uploads/.gitkeep models/.gitkeep
        echo "Setup complete!"
      '';
      description = "Setup project directories";
    };
    
    test = {
      exec = "uv run pytest";
      description = "Run tests";
    };
    
    format = {
      exec = "uv run black .";
      description = "Format code with black";
    };
    
    lint = {
      exec = "uv run flake8 .";
      description = "Lint code with flake8";
    };
    
    ingest = {
      exec = ''
        CSV_FILE="''${DEVENV_CSV_FILE:-examples/sample_data.csv}"
        if [ ! -f "$CSV_FILE" ]; then
          echo "Error: CSV file not found: $CSV_FILE"
          echo ""
          echo "Usage:"
          echo "  DEVENV_CSV_FILE=your_file.csv devenv tasks run ingest"
          echo "  Or: devenv tasks run ingest  # uses examples/sample_data.csv"
          echo ""
          echo "Alternative: Use direct command:"
          echo "  uv run python cli/ingest_custom.py examples/sample_data.csv"
          exit 1
        fi
        echo "Ingesting from: $CSV_FILE"
        uv run python cli/ingest_custom.py "$CSV_FILE"
      '';
      description = "Ingest CSV data (set DEVENV_CSV_FILE env var or uses examples/sample_data.csv)";
    };
    
    inspect = {
      exec = "uv run python cli/inspect_db.py $@";
      description = "Inspect ingested data in Qdrant";
    };
    
    clear-db = {
      exec = "uv run python cli/clear_db.py --confirm";
      description = "Clear all products from Qdrant database (WARNING: destructive)";
    };
  };

  # Enter shell hook
  enterShell = ''
    echo "🚀 Fashion AI Development Environment"
    echo ""
    echo "Available commands:"
    echo "  devenv up          - Start all services (Qdrant + FastAPI)"
    echo "  devenv shell       - Enter development shell"
    echo "  devenv tasks setup    - Setup project directories"
    echo "  devenv tasks test     - Run tests"
    echo "  devenv tasks format   - Format code"
    echo "  devenv tasks lint     - Lint code"
    echo "  devenv tasks run ingest   - Ingest CSV data"
    echo "  devenv tasks run inspect  - Inspect ingested data"
    echo ""
    echo "  Or use directly (recommended):"
    echo "  uv run python cli/ingest_custom.py examples/sample_data.csv"
    echo "  uv run python cli/inspect_db.py --count  # Check data"
    echo ""
    echo "API will be available at: http://localhost:8000"
    echo "API docs: http://localhost:8000/docs"
    echo "Qdrant dashboard: http://localhost:6333/dashboard"
    echo ""
  '';
}

