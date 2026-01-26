#!/bin/bash
# Tavily Extract API script
# Usage: ./extract.sh "url1" ["url2" ...] [--query "focus query"]
# Example: ./extract.sh "https://example.com/page1" "https://example.com/page2" --query "API usage"

set -e

URLS=()
QUERY=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --query)
            QUERY="$2"
            shift 2
            ;;
        *)
            URLS+=("$1")
            shift
            ;;
    esac
done

if [ ${#URLS[@]} -eq 0 ]; then
    echo "Usage: ./extract.sh \"url1\" [\"url2\" ...] [--query \"focus query\"]"
    echo "  urls: one or more URLs to extract (max 20)"
    echo "  --query: optional query to focus extraction"
    exit 1
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "Error: TAVILY_API_KEY environment variable not set"
    exit 1
fi

# Build URLs JSON array
URLS_JSON=$(printf '%s\n' "${URLS[@]}" | jq -R . | jq -s .)

# Build request body
if [ -n "$QUERY" ]; then
    REQUEST_BODY=$(jq -n \
        --argjson urls "$URLS_JSON" \
        --arg query "$QUERY" \
        '{urls: $urls, query: $query, chunks_per_source: 3}')
else
    REQUEST_BODY=$(jq -n \
        --argjson urls "$URLS_JSON" \
        '{urls: $urls}')
fi

curl -s --request POST \
    --url https://api.tavily.com/extract \
    --header "Authorization: Bearer $TAVILY_API_KEY" \
    --header 'Content-Type: application/json' \
    --header 'x-client-source: claude-code-skill' \
    --data "$REQUEST_BODY" | jq '.'
