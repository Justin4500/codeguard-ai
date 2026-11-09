import sys

from app.core.config import settings
from app.services.ai import provider

print("provider:", settings.ai_provider)
print("model:", settings.ai_model)
print("key_prefix:", settings.ai_api_key[:8] + "...")
cfg = provider.resolve_config(None)
try:
    reply = provider.test_provider(cfg)
    print("TEST_OK:", repr(reply))
except provider.AIError as exc:
    print("TEST_FAIL:", exc)
except Exception as exc:  # noqa: BLE001
    print("TEST_ERROR:", type(exc).__name__, exc)
sys.stdout.flush()
