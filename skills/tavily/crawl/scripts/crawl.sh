#!/bin/bash
# Tavily Crawl API script
# Usage: ./crawl.sh '{"url": "https://example.com", ...}' [output_dir]
# Example: ./crawl.sh '{"url": "https://docs.example.com", "max_depth": 2, "limit": 20}' ./crawled

set -e

# Function to decode JWT payload
decode_jwt_payload() {
    local token="$1"
    local payload=$(echo "$token" | cut -d'.' -f2)
    local padded_payload="$payload"
    case $((${#payload} % 4)) in
        2) padded_payload="${payload}==" ;;
        3) padded_payload="${payload}=" ;;
    esac
    echo "$padded_payload" | base64 -d 2>/dev/null
}

# Function to check if a JWT is valid for Tavily (not expired and correct issuer)
is_valid_tavily_token() {
    local token="$1"
    local payload=$(decode_jwt_payload "$token")
    
    # Check if it's a Tavily token (exact issuer match for security)
    local iss=$(echo "$payload" | jq -r '.iss // empty' 2>/dev/null)
    if [ "$iss" != "https://mcp.tavily.com/" ]; then
        return 1  # Not a valid Tavily token
    fi
    
    # Check if expired
    local exp=$(echo "$payload" | jq -r '.exp // empty' 2>/dev/null)
    if [ -n "$exp" ] && [ "$exp" != "null" ]; then
        local current_time=$(date +%s)
        if [ "$current_time" -ge "$exp" ]; then
            return 1  # Expired
        fi
    fi
    
    return 0  # Valid Tavily token
}

# Function to find token from MCP auth cache
get_mcp_token() {
    MCP_AUTH_DIR="$HOME/.mcp-auth"
    if [ -d "$MCP_AUTH_DIR" ]; then
        # Search recursively for *_tokens.json files
        while IFS= read -r token_file; do
            if [ -f "$token_file" ]; then
                token=$(jq -r '.access_token // empty' "$token_file" 2>/dev/null)
                if [ -n "$token" ] && [ "$token" != "null" ]; then
                    # Check if valid Tavily token (correct issuer and not expired)
                    if ! is_valid_tavily_token "$token"; then
                        continue  # Skip invalid/non-Tavily/expired tokens
                    fi
                    echo "$token"
                    return 0
                fi
            fi
        done < <(find "$MCP_AUTH_DIR" -name "*_tokens.json" 2>/dev/null)
    fi
    return 1
}

# Try to load OAuth token from MCP if TAVILY_API_KEY is not set
if [ -z "$TAVILY_API_KEY" ]; then
    token=$(get_mcp_token) || true
    if [ -n "$token" ]; then
        export TAVILY_API_KEY="$token"
    fi
fi

JSON_INPUT="$1"
OUTPUT_DIR="$2"

if [ -z "$JSON_INPUT" ]; then
    echo "Usage: ./crawl.sh '<json>' [output_dir]"
    echo ""
    echo "Required:"
    echo "  url: string - Root URL to begin crawling"
    echo ""
    echo "Optional:"
    echo "  max_depth: 1-5 (default: 1) - Levels deep to crawl"
    echo "  max_breadth: integer (default: 20) - Links per page"
    echo "  limit: integer (default: 50) - Total pages cap"
    echo "  instructions: string - Natural language guidance for semantic focus"
    echo "  extract_depth: \"basic\" (default), \"advanced\""
    echo "  format: \"markdown\" (default), \"text\""
    echo "  select_paths: [\"regex1\", \"regex2\"] - Paths to include"
    echo "  select_domains: [\"regex1\"] - Domains to include"
    echo "  allow_external: true/false (default: true)"
    echo "  include_favicon: true/false"
    echo ""
    echo "Arguments:"
    echo "  output_dir: optional directory to save markdown files"
    echo ""
    echo "Example:"
    echo "  ./crawl.sh '{\"url\": \"https://docs.example.com\", \"max_depth\": 2, \"select_paths\": [\"/api/.*\"]}' ./output"
    exit 1
fi

# If no token found, run MCP OAuth flow
if [ -z "$TAVILY_API_KEY" ]; then
    set +e
    echo "No Tavily token found. Initiating OAuth flow..." >&2
    echo "Please complete authentication in your browser..." >&2
    npx -y mcp-remote https://mcp.tavily.com/mcp </dev/null >/dev/null 2>&1 &
    MCP_PID=$!

    TIMEOUT=120
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        sleep 3
        ELAPSED=$((ELAPSED + 3))

        token=$(get_mcp_token) || true
        if [ -n "$token" ]; then
            export TAVILY_API_KEY="$token"
            echo "Authentication successful!" >&2
            break
        fi
    done

    kill $MCP_PID 2>/dev/null || true
    wait $MCP_PID 2>/dev/null || true
    set -e
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "Error: Failed to obtain Tavily API token"
    echo "Note: The OAuth flow requires an existing Tavily account — account creation is not supported through this flow."
    echo "Please sign up at https://tavily.com first, then retry, or set TAVILY_API_KEY manually."
    exit 1
fi

# Validate JSON
if ! echo "$JSON_INPUT" | jq empty 2>/dev/null; then
    echo "Error: Invalid JSON input"
    exit 1
fi

# Check for required url field
if ! echo "$JSON_INPUT" | jq -e '.url' >/dev/null 2>&1; then
    echo "Error: 'url' field is required"
    exit 1
fi

# Ensure format is set to markdown for file output
if [ -n "$OUTPUT_DIR" ]; then
    JSON_INPUT=$(echo "$JSON_INPUT" | jq '. + {format: "markdown"}')
fi

URL=$(echo "$JSON_INPUT" | jq -r '.url')
echo "Crawling: $URL"

# Build MCP JSON-RPC request
MCP_REQUEST=$(jq -n --argjson args "$JSON_INPUT" '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "tavily_crawl",
        "arguments": $args
    }
}')

# Call Tavily MCP server via HTTPS (SSE response)
RESPONSE=$(curl -s --request POST \
    --url "https://mcp.tavily.com/mcp" \
    --header "Authorization: Bearer $TAVILY_API_KEY" \
    --header 'Content-Type: application/json' \
    --header 'Accept: application/json, text/event-stream' \
    --header 'x-client-source: claude-code-skill' \
    --data "$MCP_REQUEST")

# Parse SSE response and extract the JSON result
JSON_DATA=$(echo "$RESPONSE" | grep '^data:' | sed 's/^data://' | head -1)

if [ -z "$JSON_DATA" ]; then
    echo "$RESPONSE"
    exit 1
fi

# Extract structured content
RESULT=$(echo "$JSON_DATA" | jq '.result.structuredContent // .result.content[0].text // .error // .' 2>/dev/null)

if [ -n "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"

    # Save each result as a markdown file
    echo "$RESULT" | jq -r '.results[] | @base64' 2>/dev/null | while read -r item; do
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
    echo "$RESULT" | jq '.'
fi
