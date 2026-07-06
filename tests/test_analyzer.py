import asyncio
import unittest
from unittest.mock import patch

from server.engine.analyzer import SiteAnalyzer


class AnalyzerParsingTests(unittest.TestCase):
    def test_analyze_html_uses_structured_parser(self):
        html = """
        <html>
          <head>
            <meta content="Structured Description" property="og:description">
            <meta content="Example Suite" property="og:site_name">
            <meta content="#112233" name="theme-color">
            <link href="/favicon-192.png" sizes="192x192" rel="shortcut icon">
            <script src="https://static.example.com/app.js"></script>
            <script src="https://www.googletagmanager.com/gtm.js"></script>
            <script>console.log("inline")</script>
            <style>body { color: red; }</style>
            <title>Example Suite | Portal</title>
          </head>
          <body>
            <div class="cookie-banner">cookie</div>
          </body>
        </html>
        """
        analyzer = SiteAnalyzer()
        with patch.object(analyzer, "_favicon_data_url", return_value=""):
            result = asyncio.run(analyzer._analyze_html("https://example.com/path", html, len(html.encode("utf-8"))))
        self.assertEqual(result["title"], "Example Suite | Portal")
        self.assertEqual(result["siteName"], "Example Suite")
        self.assertEqual(result["description"], "Structured Description")
        self.assertEqual(result["themeColor"], "#112233")
        self.assertEqual(result["favicon"], "https://example.com/favicon-192.png")
        self.assertEqual(result["totalScripts"], 2)
        self.assertEqual(result["trackers"], 1)
        self.assertEqual(result["popups"], 1)
