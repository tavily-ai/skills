#!/bin/bash
# Tavily Research API script
# Usage: ./research.sh "your research query" [model] [output_file]
# Example: ./research.sh "quantum computing trends" pro results.md

set -e

QUERY="$1"
MODEL="${2:-mini}"
OUTPUT_FILE="$3"

if [ -z "$QUERY" ]; then
    echo "Usage: ./research.sh \"query\" [model] [output_file]"
    echo "  model: mini (default), pro, auto"
    echo "  output_file: optional file to save results"
    exit 1
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "Error: TAVILY_API_KEY environment variable not set"
    exit 1
fi

echo "Researching: $QUERY (model: $MODEL)"
echo "This may take 30-120 seconds..."

RESPONSE=$(curl -sN --request POST \
    --url https://api.tavily.com/research \
    --header "Authorization: Bearer $TAVILY_API_KEY" \
    --header 'Content-Type: application/json' \
    --header 'x-client-source: claude-code-skill' \
    --data "{
        \"input\": \"$QUERY\",
        \"model\": \"$MODEL\",
        \"stream\": true,
        \"citation_format\": \"numbered\"
    }" 2>&1)

if [ -n "$OUTPUT_FILE" ]; then
    echo "$RESPONSE" > "$OUTPUT_FILE"
    echo "Results saved to: $OUTPUT_FILE"
else
    echo "$RESPONSE"
fi
