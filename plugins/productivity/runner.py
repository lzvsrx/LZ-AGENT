import json
import sys

request = json.load(sys.stdin)
payload = request.get("input", {})
result = {"command": request.get("command"), "items": len(payload.get("items", []))}
print(json.dumps({"ok": True, "result": result}))
