#!/bin/bash
# Automated build script for Tesla Sync
# Automatically captures git commit hash and passes it to Docker build

# Navigate to the repository root
cd "$(dirname "$0")/.." || exit 1

# Get current git commit hash
GIT_COMMIT=$(git rev-parse --short=7 HEAD 2>/dev/null || echo "unknown")

echo "Building Tesla Sync Docker image..."
echo "Git commit: $GIT_COMMIT"
echo ""

# Export GIT_COMMIT for docker-compose to use
export GIT_COMMIT

# Build using docker-compose
cd docker || exit 1
docker-compose build

echo ""
echo "Build complete! Version: $GIT_COMMIT"
echo ""
echo "To start the container, run:"
echo "  cd docker && docker-compose up -d"
