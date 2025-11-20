#!/bin/bash
# Script to open HTML coverage report in browser

# Get the absolute path to htmlcov directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HTMLCOV_DIR="$SCRIPT_DIR/htmlcov"
INDEX_FILE="$HTMLCOV_DIR/index.html"

# Check if HTML report exists
if [ ! -f "$INDEX_FILE" ]; then
    echo "❌ Coverage report not found!"
    echo "Run: pytest app/tests/ --cov=app --cov-report=html"
    exit 1
fi

# Open in default browser
echo "📊 Opening coverage report..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$INDEX_FILE"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$INDEX_FILE"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    start "$INDEX_FILE"
else
    echo "Please open manually: $INDEX_FILE"
fi

echo "✅ Coverage report opened in browser!"
echo "📁 Report location: $INDEX_FILE"

