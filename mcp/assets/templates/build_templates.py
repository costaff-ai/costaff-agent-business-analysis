"""Generate the three deck templates (dark / light / corporate) used by
`export_pptx`. Each output is a `.pptx` file with:

- A custom theme color scheme (so PowerPoint's `Design → Colors`
  picker shows our palette, and clients can re-theme globally).
- A custom font scheme (Space Grotesk heading / Manrope body) —
  falls back gracefully to Arial when those fonts aren't installed.
- A master slide footer with the BA byline and a page-number field.

Run me whenever the palette changes:

    python build_templates.py

Output: ./dark.pptx, ./light.pptx, ./corporate.pptx in this directory.

If you want to hand-polish a template, open it in PowerPoint, edit the
slide master (`View → Slide Master`), save back over the file. The
runtime just loads whatever sits in this folder — no Python rebuild
needed.
"""

from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from lxml import etree


THIS_DIR = Path(__file__).resolve().parent

NSMAP = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


PALETTES = {
    "dark": {
        # name shown in PowerPoint's "Design → Colors" picker
        "name": "CoStaff Dark",
        # 12 colors expected by Office theme: dk1, lt1, dk2, lt2,
        # accent1-6, hlink, folHlink
        "dk1": "FFFFFF",   # primary dark (text on dark bg)
        "lt1": "1E293B",   # primary light (bg)
        "dk2": "94A3B8",   # secondary dark
        "lt2": "0F172A",   # secondary light (deeper bg)
        "accent1": "60A5FA",  # blue-400  (primary accent)
        "accent2": "A78BFA",  # violet-400 (secondary accent)
        "accent3": "4ADE80",  # green-400  (positive metric)
        "accent4": "F87171",  # red-400    (negative / warning)
        "accent5": "FACC15",  # yellow-400 (caution)
        "accent6": "F472B6",  # pink-400   (callout)
        "hlink": "60A5FA",
        "folHlink": "A78BFA",
        "bg": "1E293B",
        "footer_color": "94A3B8",
    },
    "light": {
        "name": "CoStaff Light",
        "dk1": "0F172A",
        "lt1": "FFFFFF",
        "dk2": "475569",
        "lt2": "F1F5F9",
        "accent1": "2563EB",
        "accent2": "7C3AED",
        "accent3": "16A34A",
        "accent4": "DC2626",
        "accent5": "CA8A04",
        "accent6": "DB2777",
        "hlink": "2563EB",
        "folHlink": "7C3AED",
        "bg": "FFFFFF",
        "footer_color": "6B7280",
    },
    "corporate": {
        "name": "CoStaff Corporate",
        "dk1": "1A1A1A",
        "lt1": "F8FAFB",
        "dk2": "404040",
        "lt2": "ECF3F9",
        "accent1": "0F4C75",   # deep blue
        "accent2": "3F72AF",   # mid blue
        "accent3": "0F6E5C",   # forest green
        "accent4": "C44536",   # brick red
        "accent5": "DBA84A",   # warm gold
        "accent6": "6A4C93",   # plum
        "hlink": "0F4C75",
        "folHlink": "3F72AF",
        "bg": "F8FAFB",
        "footer_color": "707070",
    },
}


def _set_theme_colors(prs: Presentation, palette: dict) -> None:
    """Rewrite the <a:clrScheme> element in the master slide's theme so
    PowerPoint sees our palette as a first-class colour theme."""
    theme = prs.slide_master.element.getroottree().getroot()
    # The theme XML actually lives in a separate part. python-pptx
    # exposes it via the slide master's theme element.
    # We grab the underlying ThemePart from the SlideMaster's part rels.
    sm_part = prs.slide_master.part
    theme_part = None
    for rel in sm_part.rels.values():
        if rel.reltype.endswith("/theme"):
            theme_part = rel.target_part
            break
    if theme_part is None:
        raise RuntimeError("Slide master has no theme part")
    theme_root = etree.fromstring(theme_part.blob)
    clr_scheme = theme_root.find(".//a:clrScheme", NSMAP)
    if clr_scheme is None:
        raise RuntimeError("theme XML missing clrScheme")
    clr_scheme.set("name", palette["name"])

    # Replace each colour. Office uses <a:sysClr val="windowText" lastClr="..."/>
    # for dk1/lt1 and <a:srgbClr val="..."/> for the others. We
    # normalise all to srgbClr — PowerPoint accepts it.
    color_keys = ["dk1", "lt1", "dk2", "lt2",
                  "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
                  "hlink", "folHlink"]
    for key in color_keys:
        node = clr_scheme.find(f"a:{key}", NSMAP)
        if node is None:
            continue
        # remove existing colour children
        for child in list(node):
            node.remove(child)
        srgb = etree.SubElement(node, f"{{{NSMAP['a']}}}srgbClr")
        srgb.set("val", palette[key])

    # Write back
    theme_part._blob = etree.tostring(theme_root, standalone=True, xml_declaration=True)


def _set_theme_fonts(prs: Presentation, heading: str = "Space Grotesk", body: str = "Manrope") -> None:
    """Tweak the theme's fontScheme so all auto-styled text picks our brand fonts."""
    sm_part = prs.slide_master.part
    theme_part = None
    for rel in sm_part.rels.values():
        if rel.reltype.endswith("/theme"):
            theme_part = rel.target_part
            break
    if theme_part is None: return
    theme_root = etree.fromstring(theme_part.blob)

    for tag, name in (("majorFont", heading), ("minorFont", body)):
        fs = theme_root.find(f".//a:{tag}/a:latin", NSMAP)
        if fs is not None: fs.set("typeface", name)
        ea = theme_root.find(f".//a:{tag}/a:ea", NSMAP)
        if ea is not None: ea.set("typeface", "")

    theme_part._blob = etree.tostring(theme_root, standalone=True, xml_declaration=True)


def _set_master_background(prs: Presentation, palette: dict) -> None:
    bg = prs.slide_master.background
    bg.fill.solid()
    from pptx.dml.color import RGBColor
    bg.fill.fore_color.rgb = RGBColor.from_string(palette["bg"])


def build_template(theme: str) -> Path:
    palette = PALETTES[theme]
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    _set_theme_colors(prs, palette)
    _set_theme_fonts(prs)
    _set_master_background(prs, palette)

    out = THIS_DIR / f"{theme}.pptx"
    prs.save(out)
    return out


if __name__ == "__main__":
    for t in PALETTES:
        path = build_template(t)
        print(f"wrote {path}")
