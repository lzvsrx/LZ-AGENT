import json
import sys

request = json.load(sys.stdin)
command = request.get("command")
if command == "tests.list":
    result = {"checks": ["ruff", "pytest", "android", "windows", "linux"]}
elif command == "project.inspect":
    result = {"accepted_fields": sorted(request.get("input", {}).keys())}
else:
    print(json.dumps({"ok": False, "error": "unknown command"}))
    raise SystemExit(0)
print(json.dumps({"ok": True, "result": result}))
