#!/bin/bash

echo "🧪 Testing Elevator Ops Analyst Application"
echo "==========================================="

BASE_URL="http://localhost:5001"

echo ""
echo "1. Testing installations endpoint..."
INSTALLATIONS=$(curl -s "$BASE_URL/api/installations")
echo "Installations response: $INSTALLATIONS"

if echo "$INSTALLATIONS" | jq -e '.[] | select(.installationId)' > /dev/null 2>&1; then
    echo "✅ Installations endpoint working"
else
    echo "❌ Installations endpoint failed"
    exit 1
fi

echo ""
echo "2. Testing chat endpoint..."
CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello, test message", "installationId": "demo-installation-1"}')

echo "Chat response: $CHAT_RESPONSE"

if echo "$CHAT_RESPONSE" | jq -e '.answer' > /dev/null 2>&1; then
    echo "✅ Chat endpoint working"
else
    echo "❌ Chat endpoint failed"
    exit 1
fi

echo ""
echo "3. Testing main page..."
MAIN_PAGE=$(curl -s "$BASE_URL/")
if echo "$MAIN_PAGE" | grep -q "Elevator Operations Analyst"; then
    echo "✅ Main page loads"
else
    echo "❌ Main page failed"
    exit 1
fi

echo ""
echo "4. Testing static files..."
JS_FILE=$(curl -s "$BASE_URL/static/app.js")
if echo "$JS_FILE" | grep -q "ElevatorOpsApp"; then
    echo "✅ JavaScript file loads"
else
    echo "❌ JavaScript file failed"
    exit 1
fi

CSS_FILE=$(curl -s "$BASE_URL/static/styles.css")
if echo "$CSS_FILE" | grep -q "body"; then
    echo "✅ CSS file loads"
else
    echo "❌ CSS file failed"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Application is working correctly."
echo ""
echo "Demo URLs:"
echo "• Main Application: $BASE_URL"
echo "• Installations API: $BASE_URL/api/installations"
echo "• Chat API: $BASE_URL/api/chat"
echo ""
echo "Demo Installation IDs:"
echo "• demo-installation-1 (America/New_York)"
echo "• demo-installation-2 (America/Chicago)"  
echo "• demo-installation-3 (America/Los_Angeles)"
