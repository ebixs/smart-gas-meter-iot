import json
import unittest
from unittest.mock import patch

from simulator.push_to_api import send_readings


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class PushToApiTests(unittest.TestCase):
    @patch("simulator.push_to_api.urlopen")
    def test_posts_synthetic_readings_with_bearer_token(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({"accepted": True, "duplicate": False})
        sent = send_readings(
            "http://localhost:8000/",
            "test-token",
            "lab-send-test",
            2,
            100,
        )
        self.assertEqual(sent, 2)
        self.assertEqual(mock_urlopen.call_count, 2)
        request = mock_urlopen.call_args_list[0].args[0]
        self.assertEqual(request.full_url, "http://localhost:8000/api/v1/readings")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["input_mode"], "simulated")
        self.assertEqual(payload["sequence"], 1)

    def test_requires_token(self):
        with self.assertRaisesRegex(ValueError, "SGM_API_TOKEN"):
            send_readings("http://localhost:8000", "", "lab", 1, 100)


if __name__ == "__main__":
    unittest.main()
