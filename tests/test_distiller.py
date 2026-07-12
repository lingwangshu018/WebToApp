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

        def fake_fetch(url, timeout=8, use_cache=False):
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


class DistillerWriteAppFilesTests(unittest.TestCase):
    def test_write_app_files_parallel_builds_desktop_packages(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        distiller = Distiller()
        recipe = distiller.create_recipe(
            app_id="abcd1234",
            url="https://example.com",
            name="Example",
            color="#123456",
            display="fullscreen",
            orientation="any",
            options={},
        )
        stages = []

        def progress(stage, detail=None):
            stages.append(stage)

        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "abcd1234"
            with patch.object(distiller, "_fetch_icon", return_value=distiller._make_placeholder_png("#123456")):
                with patch.object(distiller, "_build_android", return_value={"apk": False, "fallback": True}) as android_mock:
                    with patch.object(distiller, "_build_ios", return_value={"signed": False, "dynamic_url": True}) as ios_mock:
                        meta = distiller.write_app_files(app_dir, recipe, base_url="https://service.test", progress_cb=progress)
            self.assertTrue((app_dir / "downloads" / "windows.zip").exists())
            self.assertTrue((app_dir / "downloads" / "macos.zip").exists())
            self.assertTrue((app_dir / "downloads" / "linux.tar.gz").exists())
            self.assertTrue((app_dir / "recipe.json").exists())
            self.assertEqual(meta["android"]["fallback"], True)
            self.assertEqual(meta["ios"]["dynamic_url"], True)
            self.assertIn("fetching_icon", stages)
            self.assertIn("building_platforms", stages)
            self.assertIn("done", stages)
            android_mock.assert_called_once()
            ios_mock.assert_called_once()
