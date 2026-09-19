import json

import modules.browser_extensions as browser_extensions


def test_extension_catalog_has_valid_manifest():
    extension = browser_extensions.catalog()[0]
    source = browser_extensions._source_path(extension.id)
    manifest = browser_extensions._validate_extension(source)
    assert manifest["manifest_version"] == 3
    assert manifest["name"] == extension.name
    assert manifest["version"] == extension.version


def test_install_uses_app_managed_location(tmp_path, monkeypatch):
    monkeypatch.setattr(
        browser_extensions,
        "_install_root",
        lambda: tmp_path / "WindowsOptimizer" / "BrowserExtensions",
    )

    path = browser_extensions.install("netflix-force-4k")
    installed = browser_extensions.installed_path("netflix-force-4k")

    assert path == str(installed)
    assert (installed / "manifest.json").is_file()

    manifest = json.loads((installed / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "Netflix 4K"

    browser_extensions.remove("netflix-force-4k")
    assert not installed.exists()
