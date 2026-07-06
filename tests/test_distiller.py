import unittest
from unittest.mock import patch

from server.engine.distiller import Distiller


class DistillerIconCandidateTests(unittest.TestCase):
    def test_collect_icon_candidates_reads_links_and_manifest(self):
        page_html = b"""
        <html>
          <head>
            <link href="/apple-touch-icon.png" sizes="180x180" rel="apple-touch-icon">
            <link href="/favicon.png" sizes="64x64" rel="shortcut icon">
            <link href="/site.webmanifest" rel="manifest">
            <meta content="/tile.png" name="msapplication-TileImage">
          </head>
        </html>
        """
        manifest = b'{"icons":[{"src":"/manifest-icon.png","sizes":"512x512"}]}'
        distiller = Distiller()

        def fake_fetch(url, timeout=8):
            if url == "https://example.com":
                return page_html
            if url == "https://example.com/site.webmanifest":
                return manifest
            return None

        with patch.object(distiller, "_fetch_url_bytes", side_effect=fake_fetch):
            candidates = distiller._collect_icon_candidates("https://example.com")
        self.assertIn("https://example.com/apple-touch-icon.png", candidates)
        self.assertIn("https://example.com/favicon.png", candidates)
        self.assertIn("https://example.com/manifest-icon.png", candidates)
        self.assertIn("https://example.com/tile.png", candidates)
