"""Build the portfolio into dist/.

The page is plain HTML, CSS and a little JS. Content lives in src/data/content.json (also
what the Pages CMS edits); this script fills src/template.html with it and copies the
static files. Standard library only, so CI needs nothing but Python.

    python3 scripts/build.py            # writes dist/
    python3 -m http.server -d dist      # look at it on http://localhost:8000
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "dist"

# Lucide-style stroke icons, drawn inline so they inherit the text colour.
ICONS = {
    "arrow": '<path d="M7 17 17 7M8 7h9v9"/>',
    "down": '<path d="M12 5v14M18 13l-6 6-6-6"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
    "github": '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.1-1.2-.3-2.5-1-3.5.3-1.1.3-2.4 0-3.5 0 0-1 0-3 1.5a10.5 10.5 0 0 0-8 0C6 2 5 2 5 2c-.3 1.1-.3 2.4 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.4.5-.7 1-.9 1.6-.2.6-.2 1.3-.1 1.9v4"/><path d="M9 18c-4.5 2-5-2-7-2"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
    "pen": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8"/>',
    "gamepad": '<path d="M6 12h4M8 10v4M15 13h.01M18 11h.01"/><rect x="2" y="6" width="20" height="12" rx="4"/>',
    "forecasting": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 6-7"/><path d="M16 7h4v4"/>',
    "ml": '<path d="M12 3 13.9 8.6 19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    "cloud": '<path d="M17.5 19H9a7 7 0 1 1 6.7-9h1.8a4.5 4.5 0 1 1 0 9Z"/>',
    "leadership": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
}


def icon(name: str) -> str:
    return (
        '<svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'
    )


def chips(items: list[str]) -> str:
    return "".join(f"<span>{escape(t)}</span>" for t in items)


def external(url: str) -> str:
    return ' target="_blank" rel="noopener"' if url.startswith("http") else ""


def stats(rows: list[dict]) -> str:
    return "".join(
        f'<div><strong>{escape(r["value"])}</strong><span>{escape(r["label"])}</span></div>'
        for r in rows
    )


def capabilities(rows: list[dict]) -> str:
    return "".join(
        f'<article class="cap reveal"><span class="num">0{n}</span>{icon(r["icon"])}'
        f'<h3>{escape(r["title"])}</h3><p>{escape(r["text"])}</p></article>'
        for n, r in enumerate(rows, 1)
    )


def skills(rows: list[dict]) -> str:
    return "".join(
        f'<div><h4>{escape(r["group"])}</h4><div class="chips">{chips(r["items"])}</div></div>'
        for r in rows
    )


def project_links(p: dict) -> str:
    links = []
    if p.get("case_study"):
        links.append(
            f'<a class="button light small" href="{escape(p["case_study"])}">'
            f'{icon("doc")} Case study</a>'
        )
    links.append(
        f'<a class="button ghost small" href="{escape(p["repo"])}"{external(p["repo"])}>'
        f'{icon("github")} {"Code" if p.get("case_study") else "Roadmap"}</a>'
    )
    return f'<div class="links">{"".join(links)}</div>'


def featured(rows: list[dict]) -> str:
    out = []
    for p in rows:
        if not p.get("case_study"):
            continue
        shot = ""
        if p.get("image"):
            shot = (
                f'<a class="shot" href="{escape(p["case_study"])}" tabindex="-1" aria-hidden="true">'
                f'<img src="{escape(p["image"])}" alt="" loading="lazy" decoding="async"></a>'
            )
        out.append(
            f'<article class="project featured-card reveal">{shot}<div class="body">'
            f'<div class="row"><small>{escape(p["eyebrow"])}</small>'
            f'<span class="status live"><i></i>{escape(p["status"])}</span></div>'
            f'<h3>{escape(p["title"])}</h3><p>{escape(p["text"])}</p>'
            f'<div class="chips">{chips(p["stack"])}</div>{project_links(p)}</div></article>'
        )
    return "".join(out)


def planned(rows: list[dict]) -> str:
    return "".join(
        f'<article class="project reveal"><div class="row"><small>{escape(p["eyebrow"])}</small>'
        f'<span class="status"><i></i>{escape(p["status"])}</span></div>'
        f'<h3>{escape(p["title"])}</h3><p>{escape(p["text"])}</p>'
        f'<div class="chips">{chips(p["stack"])}</div>{project_links(p)}</article>'
        for p in rows
        if not p.get("case_study")
    )


def work(rows: list[dict]) -> str:
    out = []
    for n, w in enumerate(rows, 1):
        points = "".join(f"<li>{escape(x)}</li>" for x in w.get("points", []))
        more = (
            f'<details><summary>What I did</summary><ul>{points}</ul></details>' if points else ""
        )
        link = ""
        if w.get("link"):
            link = (
                f'<a class="text-link" href="{escape(w["link"])}"{external(w["link"])}>'
                f"See the code {icon('arrow')}</a>"
            )
        out.append(
            f'<article class="case reveal"><div class="row"><span class="num">{n:02d}</span>'
            f'<small>{escape(w["meta"])}</small></div><h3>{escape(w["title"])}</h3>'
            f'<p>{escape(w["text"])}</p>{more}<div class="chips">{chips(w.get("tags", []))}</div>'
            f"{link}</article>"
        )
    return "".join(out)


def roles(rows: list[dict]) -> str:
    return "".join(
        f'<li class="role reveal"><span class="num">{n:02d}</span>'
        f'<span class="period">{escape(r["period"])}</span><div>'
        f'<h3>{escape(r["role"])}</h3><h4>{escape(r["company"])}</h4><p>{escape(r["copy"])}</p>'
        f'<div class="chips">{chips(r["tags"])}</div></div></li>'
        for n, r in enumerate(rows, 1)
    )


def education(rows: list[dict]) -> str:
    return "".join(
        f'<li class="reveal"><span>{escape(e["year"])}</span><b>{escape(e["title"])}</b>'
        f'<em>{escape(e["where"])}</em></li>'
        for e in rows
    )


def render(content: dict, version: str) -> str:
    profile = content["profile"]
    about = content["about"]
    values = {
        **{k: escape(v) for k, v in profile.items()},
        "name_upper": escape(profile["name"].upper()),
        "about_lead": escape(about["lead"]),
        "about_body": "".join(f'<p class="copy">{escape(p)}</p>' for p in about["body"]),
        "stats": stats(content["stats"]),
        "capabilities": capabilities(content["capabilities"]),
        "skills": skills(content["skills"]),
        "featured": featured(content["projects"]),
        "planned": planned(content["projects"]),
        "work": work(content["work"]),
        "roles": roles(content["roles"]),
        "education": education(content["education"]),
        "year": str(dt.date.today().year),
        "version": version,
    }
    template = (SRC / "template.html").read_text()

    def fill(match: re.Match[str]) -> str:
        key = match.group(1)
        if key.startswith("i:"):
            return icon(key[2:])
        if key not in values:
            raise KeyError(f"template asks for {{{{{key}}}}} but content.json has no such value")
        return values[key]

    return re.sub(r"\{\{([a-z_:]+)\}\}", fill, template)


def main() -> None:
    content = json.loads((SRC / "data" / "content.json").read_text())
    css, js = (SRC / "site.css").read_bytes(), (SRC / "site.js").read_bytes()
    version = hashlib.sha1(css + js).hexdigest()[:8]  # cache-buster for the two assets

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "public", OUT)
    (OUT / "index.html").write_text(render(content, version))
    (OUT / "site.css").write_bytes(css)
    (OUT / "site.js").write_bytes(js)
    print(f"built {OUT.relative_to(ROOT)}/ ({len(content['projects'])} projects, "
          f"{len(content['work'])} case studies)")


if __name__ == "__main__":
    main()
