"""Tests for web page fetching and boilerplate-stripping text extraction."""

import httpx
import pytest

from app.web_fetch import fetch_page_text

SAMPLE_HTML = """
<html>
<head><title>Solar Power Technologies</title></head>
<body>
    <nav><a href="/">Home</a><a href="/about">About</a><a href="/contact">Contact Us</a></nav>
    <header><div class="logo">Statkraft</div><button>Search</button></header>
    <main>
        <h1>Solar Power</h1>
        <p>A solar panel converts sunlight into electricity using photovoltaic cells.</p>
        <p>An inverter transforms the direct current produced by panels into alternating current.</p>
    </main>
    <aside><h2>Related links</h2><a href="/wind">Wind Power</a></aside>
    <footer><p>&copy; 2026 Statkraft. <a href="/privacy">Privacy Policy</a> | <a href="/cookies">Cookie Policy</a></p></footer>
    <script>trackPageView();</script>
    <style>.hidden { display: none; }</style>
</body>
</html>
"""


class _FakeResponse:
    def __init__(self, text: str, content_type: str = "text/html; charset=utf-8", status_code: int = 200):
        self.text = text
        self.headers = {"content-type": content_type}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)


def test_fetch_page_text_strips_navigation_header_footer_and_scripts(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: _FakeResponse(SAMPLE_HTML))

    result = fetch_page_text("https://www.statkraft.com/energy-technologies/solar-power/")

    assert result["title"] == "Solar Power Technologies"
    assert "solar panel converts sunlight" in result["text"]
    assert "inverter transforms" in result["text"]
    for boilerplate in ("Home", "About", "Contact Us", "Search", "Related links", "Wind Power", "Privacy Policy", "Cookie Policy", "trackPageView", "hidden"):
        assert boilerplate not in result["text"]


def test_fetch_page_text_rejects_non_http_scheme() -> None:
    with pytest.raises(ValueError, match="Unsupported URL scheme"):
        fetch_page_text("ftp://example.com/file.html")


def test_fetch_page_text_rejects_non_html_content(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: _FakeResponse("{}", content_type="application/json"))

    with pytest.raises(ValueError, match="did not return HTML content"):
        fetch_page_text("https://example.com/data.json")


def test_fetch_page_text_truncates_long_content(monkeypatch) -> None:
    long_html = f"<html><body><main><p>{'word ' * 3000}</p></main></body></html>"
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: _FakeResponse(long_html))

    result = fetch_page_text("https://example.com/long-page", max_chars=100)

    assert len(result["text"]) <= 101
    assert result["text"].endswith("…")
