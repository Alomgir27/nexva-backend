#!/bin/bash

echo "Starting local server on http://localhost:8080"
echo "Open http://localhost:8080/demo.html in your browser"
echo ""

# Try python3 first, then python, then php, then node
if command -v python3 &> /dev/null; then
    python3 -m http.server 8080
elif command -v python &> /dev/null; then
    python -m SimpleHTTPServer 8080
elif command -v php &> /dev/null; then
    php -S localhost:8080
else
    echo "Please install Python or PHP to run a local server"
    echo "Or use: npx http-server -p 8080"
fi

