#!/bin/bash
# Quick start script for Fashion AI System

echo "Starting Fashion AI System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Run the application
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

