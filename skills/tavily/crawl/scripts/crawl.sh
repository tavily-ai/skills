#!/bin/bash
# Tavily Crawl API script
# Usage: ./crawl.sh "url" [max_depth] [limit] [output_dir]
# Example: ./crawl.sh "https://docs.example.com" 2 20 ./crawled

set -e

URL="$1"
MAX_DEPTH="${2:-1}"
LIMIT="${3:-20}"
OUTPUT_DIR="$4"

if [ -z "$URL" ]; then
    echo "Usage: ./crawl.sh \"url\" [max_depth] [limit] [output_dir]"
    echo "  max_depth: 1-5 (default: 1)"
    echo "  limit: max pages (default: 20)"
    echo "  output_dir: optional directory to save markdown files"
    exit 1
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "Error: TAVILY_API_KEY environment variable not set"
    exit 1
fi

echo "Crawling: $URL (depth: $MAX_DEPTH, limit: $LIMIT)"

RESPONSE=$(curl -s --request POST \
    --url https://api.tavily.com/crawl \
    --header "Authorization: Bearer $TAVILY_API_KEY" \
    --header 'Content-Type: application/json' \
    --data "{
        \"url\": \"$URL\",
        \"max_depth\": $MAX_DEPTH,
        \"limit\": $LIMIT,
        \"format\": \"markdown\"
    }")

if [ -n "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"

    # Save each result as a markdown file
    echo "$RESPONSE" | jq -r '.results[] | @base64' | while read -r item; do
        _jq() {
            echo "$item" | base64 --decode | jq -r "$1"
        }

        PAGE_URL=$(_jq '.url')
        CONTENT=$(_jq '.raw_content')

        # Create filename from URL
        FILENAME=$(echo "$PAGE_URL" | sed 's|https\?://||' | sed 's|[/:?&=]|_|g' | cut -c1-100)
        FILEPATH="$OUTPUT_DIR/${FILENAME}.md"

        echo "# $PAGE_URL" > "$FILEPATH"
        echo "" >> "$FILEPATH"
        echo "$CONTENT" >> "$FILEPATH"

        echo "Saved: $FILEPATH"
    done

    echo "Crawl complete. Files saved to: $OUTPUT_DIR"
else
    echo "$RESPONSE" | jq '.'
fi
