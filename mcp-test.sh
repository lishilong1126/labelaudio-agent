curl -X POST http://127.0.0.1:8000/mcp \
-H "Content-Type: application/json" \
-H 'Accept: application/json, text/event-stream' \
-d '{
  "tool": "get_server_status",
  "args": {}
}'

