#!/bin/bash
# Tavily Search API script
# Usage: ./search.sh "your search query" [max_results] [search_depth]
# Example: ./search.sh "python async patterns" 10 advanced

set -e

QUERY="$1"
MAX_RESULTS="${2:-5}"
SEARCH_DEPTH="${3:-basic}"

if [ -z "$QUERY" ]; then
    echo "Usage: ./search.sh \"query\" [max_results] [search_depth]"
    echo "  max_results: 1-20 (default: 5)"
    echo "  search_depth: ultra-fast, fast, basic (default), advanced"
    exit 1
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "Error: TAVILY_API_KEY environment variable not set"
    exit 1
fi

curl -s --request POST \
    --url https://api.tavily.com/search \
    --header "Authorization: Bearer $TAVILY_API_KEY" \
    --header 'Content-Type: application/json' \
    --header 'x-client-source: claude-code-skill' \
    --data "{
        \"query\": \"$QUERY\",
        \"max_results\": $MAX_RESULTS,
        \"search_depth\": \"$SEARCH_DEPTH\"
    }" | jq '.'
