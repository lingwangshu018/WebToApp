from server.main import DOWNLOAD_TYPES


def test_assetlinks_is_downloadable_from_app_page():
    assert DOWNLOAD_TYPES["assetlinks"] == ("assetlinks.json", "application/json")
