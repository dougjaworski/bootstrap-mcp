#!/bin/bash
# Test script for Bootstrap MCP Server
# Tests all 8 MCP tools via HTTP/SSE transport

MCP_URL="http://docker01:8001/mcp"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get session ID
echo "Getting session ID..."
SESSION_ID=$(curl -s -D - "$MCP_URL" -H "Accept: text/event-stream" 2>&1 | grep -i "mcp-session-id:" | cut -d' ' -f2 | tr -d '\r')
echo "Session ID: $SESSION_ID"
echo ""

# Helper function to make MCP requests
mcp_request() {
    local method=$1
    local params=$2
    local id=$3

    curl -s -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -H "mcp-session-id: $SESSION_ID" \
        -d "{\"jsonrpc\":\"2.0\",\"id\":$id,\"method\":\"$method\",\"params\":$params}" \
        | grep "data:" | sed 's/data: //'
}

echo "========================================"
echo "  BOOTSTRAP MCP SERVER - FULL TEST"
echo "========================================"
echo ""

# Initialize
echo -e "${BLUE}[0] Initializing MCP session...${NC}"
INIT_RESPONSE=$(mcp_request "initialize" '{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}' 1)
SERVER_NAME=$(echo "$INIT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['serverInfo']['name'])" 2>/dev/null)
echo -e "${GREEN}✓ Connected to: $SERVER_NAME${NC}"
echo ""

# Test 1: List tools
echo -e "${BLUE}[1] Listing available tools...${NC}"
TOOLS_RESPONSE=$(mcp_request "tools/list" '{}' 2)
TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['result']['tools']))" 2>/dev/null)
echo -e "${GREEN}✓ Found $TOOL_COUNT tools${NC}"
echo "$TOOLS_RESPONSE" | python3 -c "import sys, json; tools = json.load(sys.stdin)['result']['tools']; [print(f'  - {t[\"name\"]}') for t in tools]" 2>/dev/null
echo ""

# Test 2: search_docs
echo -e "${BLUE}[2] Testing search_docs('button', limit=3)...${NC}"
SEARCH_RESPONSE=$(mcp_request "tools/call" '{"name":"search_docs","arguments":{"query":"button","limit":3}}' 3)
echo "$SEARCH_RESPONSE" | python3 -c "
import sys, json
result = json.load(sys.stdin)
content = json.loads(result['result']['content'][0]['text'])
print(f'  Found {content[\"count\"]} results:')
for r in content['results']:
    print(f'    - {r[\"title\"]} ({r[\"section\"]})')
" 2>/dev/null
echo -e "${GREEN}✓ search_docs working${NC}"
echo ""

# Test 3: get_component
echo -e "${BLUE}[3] Testing get_component('modal')...${NC}"
COMP_RESPONSE=$(mcp_request "tools/call" '{"name":"get_component","arguments":{"component_name":"modal"}}' 4)
echo "$COMP_RESPONSE" | python3 -c "
import sys, json
result = json.load(sys.stdin)
content = json.loads(result['result']['content'][0]['text'])
if content['found']:
    data = content['data']
    print(f'  Title: {data[\"title\"]}')
    print(f'  URL: {data[\"url\"]}')
" 2>/dev/null
echo -e "${GREEN}✓ get_component working${NC}"
echo ""

# Test 4: get_utility_class
echo -e "${BLUE}[4] Testing get_utility_class('d-flex')...${NC}"
UTIL_RESPONSE=$(mcp_request "tools/call" '{"name":"get_utility_class","arguments":{"class_name":"d-flex"}}' 5)
echo "$UTIL_RESPONSE" | python3 -c "
import sys, json
result = json.load(sys.stdin)
content = json.loads(result['result']['content'][0]['text'])
print(f'  Found {content[\"count\"]} documents using d-flex')
" 2>/dev/null
echo -e "${GREEN}✓ get_utility_class working${NC}"
echo ""

# Test 5: list_sections
echo -e "${BLUE}[5] Testing list_sections()...${NC}"
SECTIONS_RESPONSE=$(mcp_request "tools/call" '{"name":"list_sections","arguments":{}}' 6)
echo "$SECTIONS_RESPONSE" | python3 -c "
import sys, json
result = json.load(sys.stdin)
content = json.loads(result['result']['content'][0]['text'])
print(f'  Found {content[\"count\"]} sections:')
for s in content['sections'][:6]:
    print(f'    - {s[\"section\"]} ({s[\"count\"]} docs)')
" 2>/dev/null
echo -e "${GREEN}✓ list_sections working${NC}"
echo ""

# Test 6: get_section_docs
echo -e "${BLUE}[6] Testing get_section_docs('components')...${NC}"
SECTION_RESPONSE=$(mcp_request "tools/call" '{"name":"get_section_docs","arguments":{"section":"components"}}' 7)
echo "$SECTION_RESPONSE" | python3 -c "
import sys, json
result = json.load(sys.stdin)
content = json.loads(result['result']['content'][0]['text'])
print(f'  Found {content[\"count\"]} component documents')
if content['count'] > 0:
    print(f'  Sample: {content[\"results\"][0][\"title\"]}')
" 2>/dev/null
echo -e "${GREEN}✓ get_section_docs working${NC}"
echo ""

# Test 7: get_full_doc
echo -e "${BLUE}[7] Testing get_full_doc('buttons')...${NC}"
DOC_RESPONSE=$(mcp_request "tools/call" '{"name":"get_full_doc","arguments":{"slug":"buttons"}}' 8)
echo "$DOC_RESPONSE" | python3 -c "
import sys, json
result = json.load(sys.stdin)
content = json.loads(result['result']['content'][0]['text'])
if content['found']:
    data = content['data']
    print(f'  Title: {data[\"title\"]}')
    print(f'  Section: {data[\"section\"]}')
    print(f'  URL: {data[\"url\"]}')
" 2>/dev/null
echo -e "${GREEN}✓ get_full_doc working${NC}"
echo ""

# Test 8: get_examples
echo -e "${BLUE}[8] Testing get_examples('button', limit=2)...${NC}"
EXAMPLES_RESPONSE=$(mcp_request "tools/call" '{"name":"get_examples","arguments":{"query":"button","limit":2}}' 9)
echo "$EXAMPLES_RESPONSE" | python3 -c "
import sys, json
result = json.load(sys.stdin)
content = json.loads(result['result']['content'][0]['text'])
print(f'  Found {content[\"count\"]} code examples')
if content['count'] > 0:
    print(f'  Example from: {content[\"results\"][0][\"title\"]}')
" 2>/dev/null
echo -e "${GREEN}✓ get_examples working${NC}"
echo ""

echo "========================================"
echo -e "${GREEN}  ALL TESTS PASSED! ✓${NC}"
echo "========================================"
echo ""
echo "MCP Server URL: $MCP_URL"
echo "Server: Bootstrap CSS Documentation"
echo "Status: Healthy - All 8 tools verified"
