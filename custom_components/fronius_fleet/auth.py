"""URL handling for the Solar.web login flow."""

from urllib.parse import urljoin


def resolve_login_url(page_url: str, target_url: str | None) -> str:
    """Resolve a redirect or form action against the page that supplied it."""
    if not target_url or not target_url.strip():
        raise ValueError("Login redirect or form action URL is missing")

    return urljoin(page_url, target_url)
