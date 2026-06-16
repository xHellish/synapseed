"""List available free models on OpenRouter."""
import httpx
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    for p in ["../.env", "../../.env", ".env"]:
        if os.path.exists(p):
            load_dotenv(p)
            break
except ImportError:
    pass

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY:
    print("No OPENROUTER_API_KEY set")
    sys.exit(1)

r = httpx.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {API_KEY}"},
    timeout=15,
)
data = r.json().get("data", [])
free = [m for m in data if ":free" in m["id"]]
print(f"\n{len(free)} modelos gratuitos disponibles:")
for m in free:
    print(f"  {m['id']}")