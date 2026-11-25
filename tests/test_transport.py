"""Tests for the live transport's off-VM fallback (stdlib unittest).

Regression: on a laptop (or fly.io) the VM-only dynamic_credentials
import fails, and the transport used to leave read_json_response
undefined, so every live call died with
    NameError: name 'read_json_response' is not defined
even when MODEL_API_KEY was set. The fallback must exist.
"""
import importlib
import io
import json
import sys
import unittest

import pileup.transport as transport


class OffVmFallbackTest(unittest.TestCase):
    def test_read_json_response_defined_when_import_fails(self):
        # Simulate off-VM: block the VM-only module, reload the transport.
        sys.modules["dynamic_credentials"] = None
        try:
            importlib.reload(transport)
        finally:
            del sys.modules["dynamic_credentials"]
        try:
            self.assertFalse(transport._HAVE_SURROGATE)
            self.assertTrue(callable(transport.read_json_response))
            body = json.dumps({"ok": True}).encode("utf-8")
            self.assertEqual(
                transport.read_json_response(io.BytesIO(body)),
                {"ok": True})
        finally:
            # Restore the VM's real import for the rest of the suite.
            importlib.reload(transport)


if __name__ == "__main__":
    unittest.main()
