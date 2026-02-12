#!/bin/bash
# Tavily Research API script
# Usage: ./research.sh '{"input": "your research query", ...}' [output_file]
# Example: ./research.sh '{"input": "quantum computing trends", "model": "pro"}' results.md

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
OUTPUT_FILE="$2"

if [ -z "$JSON_INPUT" ]; then
    echo "Usage: ./research.sh '<json>' [output_file]"
    echo ""
    echo "Required:"
    echo "  input: string - The research topic or question"
    echo ""
    echo "Optional:"
    echo "  model: \"mini\" (default), \"pro\", \"auto\""
    echo "    - mini: Targeted, efficient research for narrow questions"
    echo "    - pro: Comprehensive, multi-agent research for complex topics"
    echo "    - auto: Automatically selects based on query complexity"
    echo ""
    echo "Arguments:"
    echo "  output_file: optional file to save results"
    echo ""
    echo "Example:"
    echo "  ./research.sh '{\"input\": \"AI agent frameworks comparison\", \"model\": \"pro\"}' report.md"
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

# Check for required input field
if ! echo "$JSON_INPUT" | jq -e '.input' >/dev/null 2>&1; then
    echo "Error: 'input' field is required"
    exit 1
fi

INPUT=$(echo "$JSON_INPUT" | jq -r '.input')
MODEL=$(echo "$JSON_INPUT" | jq -r '.model // "mini"')

echo "Researching: $INPUT (model: $MODEL)"
echo "This may take 30-120 seconds..."

# Build MCP JSON-RPC request
MCP_REQUEST=$(jq -n --argjson args "$JSON_INPUT" '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "tavily_research",
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
    RESULT="$RESPONSE"
else
    RESULT=$(echo "$JSON_DATA" | jq '.result.structuredContent // .result.content[0].text // .error // .' 2>/dev/null || echo "$JSON_DATA")
fi

if [ -n "$OUTPUT_FILE" ]; then
    echo "$RESULT" > "$OUTPUT_FILE"
    echo "Results saved to: $OUTPUT_FILE"
else
    echo "$RESULT"
fi
