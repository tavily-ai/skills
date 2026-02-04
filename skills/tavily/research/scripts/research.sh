#!/bin/bash
# Tavily Research API script with polling support
# Usage: ./research.sh '{"input": "your research query", ...}' [output_file]
# Example: ./research.sh '{"input": "quantum computing trends", "model": "pro"}' results.md

set -e
set -o pipefail

JSON_INPUT="$1"
OUTPUT_FILE="$2"

# Polling configuration
MAX_ATTEMPTS=120         # Maximum polling attempts (10 minutes of polling)
POLL_INTERVAL=5          # Seconds between polls
INITIAL_TIMEOUT=30       # Initial request timeout in seconds
MAX_CONSECUTIVE_FAILURES=5  # Max consecutive failures before aborting

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
echo "This may take 30 seconds to several minutes..."

# Create temp file for response
TEMP_RESPONSE=$(mktemp)
trap "rm -f $TEMP_RESPONSE" EXIT

# Initial research request with proper error handling
HTTP_CODE=$(curl -s -w "%{http_code}" --max-time "$INITIAL_TIMEOUT" \
    -o "$TEMP_RESPONSE" \
    --request POST \
    --url https://api.tavily.com/research \
    --header "Authorization: Bearer $TAVILY_API_KEY" \
    --header 'Content-Type: application/json' \
    --header 'x-client-source: claude-code-skill' \
    --data "$JSON_INPUT") || CURL_EXIT=$?

# Check curl exit code
if [ "${CURL_EXIT:-0}" -ne 0 ]; then
    echo "Error: Network request failed (curl exit code: $CURL_EXIT)"
    case "$CURL_EXIT" in
        6) echo "Could not resolve host. Check your internet connection." ;;
        7) echo "Failed to connect to api.tavily.com. The service may be down." ;;
        28) echo "Request timed out after ${INITIAL_TIMEOUT}s. Try again later." ;;
        60) echo "SSL certificate verification failed." ;;
        *) echo "Network error occurred." ;;
    esac
    exit 1
fi

# Check HTTP status code
if [ "$HTTP_CODE" -ge 400 ]; then
    echo "Error: API returned HTTP $HTTP_CODE"
    case "$HTTP_CODE" in
        401) echo "Unauthorized. Check your TAVILY_API_KEY." ;;
        403) echo "Forbidden. Your API key may not have access to this resource." ;;
        429) echo "Rate limited. Too many requests." ;;
        500|502|503) echo "Server error. The Tavily service may be experiencing issues." ;;
    esac
    cat "$TEMP_RESPONSE" 2>/dev/null || true
    exit 1
fi

RESPONSE=$(cat "$TEMP_RESPONSE")

# Check if response is valid JSON
if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
    echo "Error: Invalid response from API"
    echo "$RESPONSE"
    exit 1
fi

# Extract status and request_id
STATUS=$(echo "$RESPONSE" | jq -r '.status // empty')
REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id // empty')

# If already completed, output result
if [ "$STATUS" = "completed" ]; then
    if [ -n "$OUTPUT_FILE" ]; then
        echo "$RESPONSE" > "$OUTPUT_FILE"
        echo "Results saved to: $OUTPUT_FILE"
    else
        echo "$RESPONSE"
    fi
    exit 0
fi

# If failed, output error and exit with error code
if [ "$STATUS" = "failed" ]; then
    echo "Research failed!"
    ERROR=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"')
    echo "Error: $ERROR"
    if [ -n "$OUTPUT_FILE" ]; then
        echo "$RESPONSE" > "$OUTPUT_FILE"
    fi
    exit 1
fi

# If pending/processing/in_progress and we have a request_id, start polling
if [ -n "$REQUEST_ID" ] && [ "$STATUS" != "completed" ] && [ "$STATUS" != "failed" ]; then
    echo "Research task started (request_id: $REQUEST_ID)"
    echo "Status: $STATUS - polling for results..."

    ATTEMPT=0
    CONSECUTIVE_FAILURES=0
    UNKNOWN_STATUS_COUNT=0
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        ATTEMPT=$((ATTEMPT + 1))
        sleep "$POLL_INTERVAL"

        # Poll for status with proper error handling
        HTTP_CODE=$(curl -s -w "%{http_code}" --max-time 30 \
            -o "$TEMP_RESPONSE" \
            --request GET \
            --url "https://api.tavily.com/research/$REQUEST_ID" \
            --header "Authorization: Bearer $TAVILY_API_KEY" \
            --header 'x-client-source: claude-code-skill') || CURL_EXIT=$?

        # Check curl exit code
        if [ "${CURL_EXIT:-0}" -ne 0 ]; then
            CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
            echo "Warning: Network error during poll (attempt $ATTEMPT/$MAX_ATTEMPTS, failures: $CONSECUTIVE_FAILURES)"
            if [ $CONSECUTIVE_FAILURES -ge $MAX_CONSECUTIVE_FAILURES ]; then
                echo "Error: Too many consecutive network failures"
                exit 1
            fi
            CURL_EXIT=0
            continue
        fi

        # Check HTTP status code
        if [ "$HTTP_CODE" -ge 400 ]; then
            CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
            echo "Warning: API returned HTTP $HTTP_CODE (attempt $ATTEMPT/$MAX_ATTEMPTS, failures: $CONSECUTIVE_FAILURES)"
            if [ $CONSECUTIVE_FAILURES -ge $MAX_CONSECUTIVE_FAILURES ]; then
                echo "Error: Too many consecutive API errors"
                cat "$TEMP_RESPONSE" 2>/dev/null || true
                exit 1
            fi
            continue
        fi

        POLL_RESPONSE=$(cat "$TEMP_RESPONSE")

        # Check if response is valid JSON
        if ! echo "$POLL_RESPONSE" | jq empty 2>/dev/null; then
            CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
            echo "Warning: Invalid poll response (attempt $ATTEMPT/$MAX_ATTEMPTS, failures: $CONSECUTIVE_FAILURES)"
            echo "Response was: $POLL_RESPONSE"
            if [ $CONSECUTIVE_FAILURES -ge $MAX_CONSECUTIVE_FAILURES ]; then
                echo "Error: Too many consecutive invalid responses"
                exit 1
            fi
            continue
        fi

        # Reset failure counter on successful response
        CONSECUTIVE_FAILURES=0

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
                UNKNOWN_STATUS_COUNT=0
                echo "Status: $STATUS (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
                ;;
            *)
                UNKNOWN_STATUS_COUNT=$((UNKNOWN_STATUS_COUNT + 1))
                echo "Warning: Unknown status '$STATUS' (attempt $ATTEMPT/$MAX_ATTEMPTS)"
                if [ $UNKNOWN_STATUS_COUNT -ge $MAX_CONSECUTIVE_FAILURES ]; then
                    echo "Error: Received unknown status $UNKNOWN_STATUS_COUNT times. The API may have changed."
                    echo "Last response:"
                    echo "$POLL_RESPONSE"
                    exit 1
                fi
                ;;
        esac
    done

    echo "Error: Polling timeout after $MAX_ATTEMPTS attempts"
    echo "Last known status: ${STATUS:-unknown}"
    echo "Request ID: $REQUEST_ID"
    echo "Consider checking the Tavily dashboard for this request."
    echo "Last response:"
    echo "$POLL_RESPONSE"
    exit 1
fi

# Fallback: output original response when no request_id available
# This handles legacy API responses or unexpected formats
if [ -z "$REQUEST_ID" ] && [ "$STATUS" != "completed" ]; then
    echo "Warning: Unexpected API response (no request_id, status: ${STATUS:-none})"
    echo "Response:"
    echo "$RESPONSE"
    exit 1
fi

if [ -n "$OUTPUT_FILE" ]; then
    echo "$RESPONSE" > "$OUTPUT_FILE"
    echo "Results saved to: $OUTPUT_FILE"
else
    echo "$RESPONSE"
fi
