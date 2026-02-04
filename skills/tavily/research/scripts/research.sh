#!/bin/bash
# Tavily Research API script
# Usage: ./research.sh '{"input": "your research query", ...}' [output_file]
# Example: ./research.sh '{"input": "quantum computing trends", "model": "pro"}' results.md

set -e

# Function to check if a JWT is expired
is_token_expired() {
    local token="$1"
    # Extract payload (second part of JWT)
    local payload=$(echo "$token" | cut -d'.' -f2)
    # Add padding if needed for base64 decode
    local padded_payload="$payload"
    case $((${#payload} % 4)) in
        2) padded_payload="${payload}==" ;;
        3) padded_payload="${payload}=" ;;
    esac
    # Decode and extract exp claim
    local exp=$(echo "$padded_payload" | base64 -d 2>/dev/null | jq -r '.exp // empty' 2>/dev/null)
    if [ -n "$exp" ] && [ "$exp" != "null" ]; then
        local current_time=$(date +%s)
        if [ "$current_time" -ge "$exp" ]; then
            return 0  # expired
        fi
    fi
    return 1  # not expired (or couldn't determine)
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
                    # Check if JWT is expired
                    if is_token_expired "$token"; then
                        continue  # Skip expired token
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
    echo "  model: \"mini\", \"pro\", \"auto\" (default)"
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

# If no token found, auto-run MCP OAuth flow
if [ -z "$TAVILY_API_KEY" ]; then
    echo "No Tavily token found. Initiating OAuth flow..."
    echo "Please complete authentication in your browser..."
    npx -y mcp-remote https://mcp.tavily.com/mcp --allow-http &
    MCP_PID=$!
    
    # Poll for token with timeout (120 seconds max)
    TIMEOUT=120
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        sleep 2
        ELAPSED=$((ELAPSED + 2))
        
        # Check for token using the function
        token=$(get_mcp_token)
        if [ -n "$token" ]; then
            export TAVILY_API_KEY="$token"
            echo "Authentication successful!"
            break
        fi
        
        echo "Waiting for authentication... (${ELAPSED}s/${TIMEOUT}s)"
    done
    
    # Cleanup MCP process
    kill $MCP_PID 2>/dev/null || true
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "Error: Failed to obtain Tavily API token"
    echo "Please run manually: npx -y mcp-remote https://mcp.tavily.com/mcp"
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
MODEL=$(echo "$JSON_INPUT" | jq -r '.model // "auto"')

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

# Call Tavily MCP server via HTTP (SSE response)
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
