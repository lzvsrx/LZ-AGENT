import json
import sys

request = json.load(sys.stdin)
payload = request.get("input", {})
result = {"command": request.get("command"), "metadata_only": True, "fields": sorted(payload)}
print(json.dumps({"ok": True, "result": result}))
