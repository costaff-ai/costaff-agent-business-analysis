import base64
from pathlib import Path
from string import Template

_DIR = Path(__file__).parent / "templates"


def _read(filename: str) -> str:
    return (_DIR / filename).read_text(encoding="utf-8")


_BASE_CSS = _read("base.css")
_HTML_TEMPLATE = Template(_read("report.html"))
_NOTO_SNIPPET = _read("noto_font.html")

MARKDOWN_CSS = _read("markdown.css")
SECTIONS_CSS = _read("sections.css")


def render_html(
    title: str,
    body_html: str,
    generated_at: str,
    extra_css: str,
    issuer: str = "CoStaff Business Analysis Agent",
    confidentiality: str = "",
) -> str:
    return _HTML_TEMPLATE.safe_substitute(
        title=title,
        base_css=_BASE_CSS,
        extra_css=extra_css,
        generated_at=generated_at,
        body_html=body_html,
        issuer=issuer,
        confidentiality=confidentiality,
    )


def inject_noto_font(html_content: str) -> str:
    """Inject Noto CJK font override into any HTML before PDF export."""
    if "Noto Sans CJK" in html_content:
        return html_content
    if "</head>" in html_content:
        return html_content.replace("</head>", _NOTO_SNIPPET + "</head>", 1)
    return _NOTO_SNIPPET + html_content


def img_to_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""
