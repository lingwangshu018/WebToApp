import socket
import unittest
from unittest.mock import patch

from server.net import UnsafeOutboundTarget, validate_public_http_url


class NetValidationTests(unittest.TestCase):
    def test_rejects_private_targets(self):
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]):
            with self.assertRaises(UnsafeOutboundTarget):
                validate_public_http_url("http://internal.test")

    def test_accepts_public_targets(self):
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]):
            self.assertEqual(validate_public_http_url("https://example.com"), "https://example.com")
