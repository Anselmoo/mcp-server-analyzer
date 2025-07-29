#!/bin/bash
set -e

echo "Building MCP Python Code Analyzer Docker image..."
docker build -t mcp-server-analyzer .

echo "Testing Docker image..."
echo 'print("Hello from Docker!")' | docker run -i --rm mcp-server-analyzer

echo "Docker build and test completed successfully!"
