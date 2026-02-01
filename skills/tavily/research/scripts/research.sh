#!/bin/bash
# Tavily Research API script with polling support
# Usage: ./research.sh '{"input": "your research query", ...}' [output_file]
# Example: ./research.sh '{"input": "quantum computing trends", "model": "pro"}' results.md

set -e

JSON_INPUT="$1"
OUTPUT_FILE="$2"

# Polling configuration
MAX_ATTEMPTS=120         # Maximum polling attempts (10 minutes total)
POLL_INTERVAL=5          # Seconds between polls
INITIAL_TIMEOUT=30       # Initial request timeout in seconds

if [ -z "$JSON_INPUT" ]; then
    echo "Usage: ./research.sh '<json>' [output_file]"
    echo ""
    echo "Required:"
    echo "  input: string - The research topic or question"
    echo ""
    echo "Optional:"
    echo "  model: \"mini\", \"pro\", \"auto\" (default)"
    echo "    - mini: Targeted, efficient research for narrow questions"
    echo "    - pro: Comprehensive, multi-agent research for complex topics"
    echo "    - auto: Automatically selects based on query complexity"
    echo "  (streaming disabled for token management)"
    echo "  citation_format: \"numbered\" (default), \"mla\", \"apa\", \"chicago\""
    echo "  output_schema: JSON Schema object for structured output"
    echo ""
    echo "Arguments:"
    echo "  output_file: optional file to save results"
    echo ""
    echo "Example:"
    echo "  ./research.sh '{\"input\": \"AI agent frameworks comparison\", \"model\": \"pro\"}' report.md"
    exit 1
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "Error: TAVILY_API_KEY environment variable not set"
    exit 1
fi

# Validate JSON
if ! echo "$JSON_INPUT" | jq empty 2>/dev/null; then
    echo "Error: Invalid JSON input"
    exit 1
fi

# Check for required input field
if ! echo "$JSON_INPUT" | jq -e '.input' >/dev/null 2>&1; then
    echo "Error: 'input' field is required"
    exit 1
fi

# Add citation format default if not specified, disable streaming for token management
JSON_INPUT=$(echo "$JSON_INPUT" | jq '
    . + {stream: false} |
    if .citation_format == null then . + {citation_format: "numbered"} else . end
')

INPUT=$(echo "$JSON_INPUT" | jq -r '.input')
MODEL=$(echo "$JSON_INPUT" | jq -r '.model // "auto"')

echo "Researching: $INPUT (model: $MODEL)"
echo "This may take 30-120 seconds..."

# Initial research request
RESPONSE=$(curl -s --max-time "$INITIAL_TIMEOUT" --request POST \
    --url https://api.tavily.com/research \
    --header "Authorization: Bearer $TAVILY_API_KEY" \
    --header 'Content-Type: application/json' \
    --header 'x-client-source: claude-code-skill' \
    --data "$JSON_INPUT" 2>&1)

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
    echo "Error: Invalid response from API"
    echo "$RESPONSE"
    exit 1
fi

# Extract status and request_id
STATUS=$(echo "$RESPONSE" | jq -r '.status // empty')
REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id // empty')

# If already completed or failed, output result
if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    if [ -n "$OUTPUT_FILE" ]; then
        echo "$RESPONSE" > "$OUTPUT_FILE"
        echo "Results saved to: $OUTPUT_FILE"
    else
        echo "$RESPONSE"
    fi
    exit 0
fi

# If pending/processing and we have a request_id, start polling
if [ -n "$REQUEST_ID" ] && [ "$STATUS" != "completed" ] && [ "$STATUS" != "failed" ]; then
    echo "Research task started (request_id: $REQUEST_ID)"
    echo "Status: $STATUS - polling for results..."

    ATTEMPT=0
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        ATTEMPT=$((ATTEMPT + 1))
        sleep "$POLL_INTERVAL"

        # Poll for status
        POLL_RESPONSE=$(curl -s --max-time 30 --request GET \
            --url "https://api.tavily.com/research/$REQUEST_ID" \
            --header "Authorization: Bearer $TAVILY_API_KEY" \
            --header 'x-client-source: claude-code-skill' 2>&1)

        # Check if response is valid JSON
        if ! echo "$POLL_RESPONSE" | jq empty 2>/dev/null; then
            echo "Warning: Invalid poll response (attempt $ATTEMPT/$MAX_ATTEMPTS)"
            continue
        fi

        STATUS=$(echo "$POLL_RESPONSE" | jq -r '.status // empty')

        case "$STATUS" in
            completed)
                echo "Research completed!"
                if [ -n "$OUTPUT_FILE" ]; then
                    echo "$POLL_RESPONSE" > "$OUTPUT_FILE"
                    echo "Results saved to: $OUTPUT_FILE"
                else
                    echo "$POLL_RESPONSE"
                fi
                exit 0
                ;;
            failed)
                echo "Research failed!"
                ERROR=$(echo "$POLL_RESPONSE" | jq -r '.error // "Unknown error"')
                echo "Error: $ERROR"
                if [ -n "$OUTPUT_FILE" ]; then
                    echo "$POLL_RESPONSE" > "$OUTPUT_FILE"
                fi
                exit 1
                ;;
            pending|processing|in_progress)
                echo "Status: $STATUS (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
                ;;
            *)
                echo "Unknown status: $STATUS (attempt $ATTEMPT/$MAX_ATTEMPTS)"
                ;;
        esac
    done

    echo "Error: Polling timeout after $MAX_ATTEMPTS attempts"
    echo "Last response:"
    echo "$POLL_RESPONSE"
    exit 1
fi

# If no request_id, output the original response (might be an error or immediate result)
if [ -n "$OUTPUT_FILE" ]; then
    echo "$RESPONSE" > "$OUTPUT_FILE"
    echo "Results saved to: $OUTPUT_FILE"
else
    echo "$RESPONSE"
fi
