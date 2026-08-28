"""Fetch a web page and extract its substantive text, stripping navigation/boilerplate."""

from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

MAX_TEXT_CHARS = 6000
REQUEST_TIMEOUT = 10.0
USER_AGENT = "VibeGraph/0.2 (+https://github.com/mahewitt/conversational-rdf-designer)"

# Tags whose entire contents are UI chrome, not domain content: navigation, headers/footers,
# sidebars, scripts/styles, and interactive controls (forms, buttons, menus).
SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "button", "select", "template"}


class _MainContentExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        elif self._skip_depth == 0:
            self.text_parts.append(text)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    @property
    def text(self) -> str:
        return "\n".join(self.text_parts)


def fetch_page_text(url: str, max_chars: int = MAX_TEXT_CHARS) -> dict[str, str]:
    """Fetch `url` and return its title and substantive text, with nav/header/footer/script/style stripped.

    Raises ValueError for unsupported schemes, non-HTML responses, or failed requests.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: '{parsed.scheme or url}'. Only http/https URLs are supported.")

    try:
        response = httpx.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(f"Failed to fetch '{url}': {exc}") from exc

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        raise ValueError(f"'{url}' did not return HTML content (content-type: {content_type or 'unknown'}).")

    extractor = _MainContentExtractor()
    extractor.feed(response.text)

    text = extractor.text.strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "…"

    return {"url": url, "title": extractor.title, "text": text}
