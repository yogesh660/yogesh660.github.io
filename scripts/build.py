"""Build the portfolio into dist/.

Plain HTML, CSS and a little JS. Every word comes from src/data/content.json (also what the
Pages CMS edits). Each page in src/pages/ is filled with it and wrapped in layout.html.
Standard library only, so CI needs nothing but Python.

    python3 scripts/build.py            # writes dist/
    python3 -m http.server -d dist      # http://localhost:8000

Pages: / , /work/ (industry + open source), /work/<slug>/ , /about/ , /404.html
Redirects: /projects/ -> /work/#open-source, /learn/ -> /ml-model-zoo/, /play/ -> /featured-games/
Learn (/ml-model-zoo/) and Play (/featured-games/) are their own repos sharing this site's nav.
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
PAGES = SRC / "pages"
OUT = ROOT / "dist"

# Lucide-style stroke icons, inline so they take the text colour.
ICONS = {
    "arrow": '<path d="M7 17 17 7M8 7h9v9"/>',
    "back": '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    "next": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
    "github": '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.1-1.2-.3-2.5-1-3.5.3-1.1.3-2.4 0-3.5 0 0-1 0-3 1.5a10.5 10.5 0 0 0-8 0C6 2 5 2 5 2c-.3 1.1-.3 2.4 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.4.5-.7 1-.9 1.6-.2.6-.2 1.3-.1 1.9v4"/><path d="M9 18c-4.5 2-5-2-7-2"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
    "pen": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
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


def e(text: str) -> str:
    return escape(text, quote=True)


def chips(items: list[str]) -> str:
    return "".join(f"<span>{e(t)}</span>" for t in items)


def external(url: str) -> str:
    return ' target="_blank" rel="noopener"' if url.startswith("http") else ""


def area_key(area: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", area.lower()).strip("-")


# ---------- fragments ----------


def stats(rows: list[dict]) -> str:
    out = []
    for r in rows:
        # "9+" counts up to 9 and keeps the suffix; non-numeric values are shown as they are
        m = re.fullmatch(r"(\d+)(.*)", r["value"])
        attrs = f' data-count="{m.group(1)}" data-suffix="{e(m.group(2))}"' if m else ""
        out.append(
            f'<div><strong{attrs}>{e(r["value"])}</strong><span>{e(r["label"])}</span></div>'
        )
    return "".join(out)


def marquee(items: list[str]) -> str:
    row = "".join(f"<span>{e(t)}</span><i></i>" for t in items)
    return row + row  # two copies so the loop is seamless


def capabilities(rows: list[dict]) -> str:
    return "".join(
        f'<article class="cap spot reveal"><span class="num">0{n}</span>{icon(r["icon"])}'
        f'<h3>{e(r["title"])}</h3><p>{e(r["text"])}</p></article>'
        for n, r in enumerate(rows, 1)
    )


def skills(rows: list[dict]) -> str:
    return "".join(
        f'<div><h4>{e(r["group"])}</h4><div class="chips">{chips(r["items"])}</div></div>'
        for r in rows
    )


def standards(rows: list[dict]) -> str:
    return "".join(
        f'<div class="standard reveal">{icon("check")}<h3>{e(r["title"])}</h3>'
        f'<p>{e(r["text"])}</p></div>'
        for r in rows
    )


def project_links(p: dict) -> str:
    links = []
    if p.get("case_study"):
        links.append(
            f'<a class="button light small" href="{e(p["case_study"])}">{icon("doc")} Case study</a>'
        )
    label = "Roadmap" if p["status"] == "Planned" else "Code"
    links.append(
        f'<a class="button ghost small" href="{e(p["repo"])}"{external(p["repo"])}>'
        f'{icon("github")} {label}</a>'
    )
    return f'<div class="links">{"".join(links)}</div>'


def project_live(p: dict) -> str:
    shot = ""
    if p.get("image"):
        shot = (
            f'<a class="shot" href="{e(p["case_study"])}" tabindex="-1" aria-hidden="true">'
            f'<img src="{e(p["image"])}" alt="" loading="lazy" decoding="async"></a>'
        )
    return (
        f'<article class="project featured-card spot reveal">{shot}<div class="body">'
        f'<div class="row"><small>{e(p["eyebrow"])}</small>'
        f'<span class="status live"><i></i>{e(p["status"])}</span></div>'
        f'<h3>{e(p["title"])}</h3><p>{e(p["text"])}</p>'
        f'<div class="chips">{chips(p["stack"])}</div>{project_links(p)}</div></article>'
    )


def project_planned(p: dict) -> str:
    return (
        f'<article class="project spot reveal"><div class="row"><small>{e(p["eyebrow"])}</small>'
        f'<span class="status"><i></i>{e(p["status"])}</span></div>'
        f'<h3>{e(p["title"])}</h3><p>{e(p["text"])}</p>'
        f'<div class="chips">{chips(p["stack"])}</div>{project_links(p)}</article>'
    )


def case_card(w: dict, n: int) -> str:
    areas = " ".join(area_key(a) for a in w["areas"])
    return (
        f'<a class="case-card spot reveal" href="/work/{e(w["slug"])}/" data-areas="{areas}">'
        f'<div class="row"><span class="num">{n:02d}</span><small>{e(w["meta"])}</small></div>'
        f'<h3 style="view-transition-name: case-{e(w["slug"])}">{e(w["title"])}</h3>'
        f'<p>{e(w["text"])}</p><div class="chips">{chips(w["tags"][:4])}</div>'
        f'<span class="more">View project {icon("next")}</span></a>'
    )


def filters(work: list[dict]) -> str:
    areas: dict[str, int] = {}
    for w in work:
        for a in w["areas"]:
            areas[a] = areas.get(a, 0) + 1
    buttons = [f'<button type="button" class="filter on" data-area="all">All <b>{len(work)}</b></button>']
    for a, count in sorted(areas.items(), key=lambda kv: (-kv[1], kv[0])):
        buttons.append(
            f'<button type="button" class="filter" data-area="{area_key(a)}">{e(a)} <b>{count}</b></button>'
        )
    return "".join(buttons)


def journey(rows: list[dict]) -> str:
    return "".join(
        f'<li class="reveal"><span class="period">{e(r["period"])}</span>'
        f'<b>{e(r["role"])}</b><em>{e(r["company"])}</em></li>'
        for r in rows
    )


def roles(rows: list[dict]) -> str:
    return "".join(
        f'<li class="role reveal"><span class="num">{n:02d}</span>'
        f'<span class="period">{e(r["period"])}</span><div>'
        f'<h3>{e(r["role"])}</h3><h4>{e(r["company"])}</h4><p>{e(r["copy"])}</p>'
        f'<div class="chips">{chips(r["tags"])}</div></div></li>'
        for n, r in enumerate(rows, 1)
    )


def education(rows: list[dict]) -> str:
    return "".join(
        f'<li class="reveal"><span>{e(x["year"])}</span><b>{e(x["title"])}</b>'
        f'<em>{e(x["where"])}</em></li>'
        for x in rows
    )


def pager_link(w: dict | None, rel: str) -> str:
    if w is None:
        return "<span></span>"
    label = "Previous" if rel == "prev" else "Next"
    arrow = icon("back") if rel == "prev" else icon("next")
    return (
        f'<a class="pager-{rel} spot" href="/work/{e(w["slug"])}/" rel="{rel}">'
        f"<small>{arrow} {label}</small><b>{e(w['title'])}</b></a>"
    )


# ---------- Learn / Play cards (home) ----------


def learn_art() -> str:
    """A small network whose edges carry signals left to right, like a forward pass."""
    layers = [[60, 120, 180], [40, 95, 150, 205], [70, 130, 190], [100, 160]]
    xs = [70, 210, 350, 470]
    edges, nodes, k = [], [], 0
    for li in range(len(layers) - 1):
        for y1 in layers[li]:
            for y2 in layers[li + 1]:
                d = f"M{xs[li]} {y1} L{xs[li + 1]} {y2}"
                edges.append(f'<path class="edge" d="{d}"/>')
                if (k * 7) % 5 < 2:  # a few lit paths, not all of them
                    edges.append(
                        f'<path class="signal" d="{d}" pathLength="100" style="--k:{k % 9}"/>'
                    )
                k += 1
    for li, ys in enumerate(layers):
        for j, y in enumerate(ys):
            nodes.append(f'<circle cx="{xs[li]}" cy="{y}" r="7" style="--k:{li * 2 + j}"/>')
    return (
        '<svg class="net" viewBox="0 0 540 245" aria-hidden="true">'
        f'<g class="edges">{"".join(edges)}</g><g class="nodes">{"".join(nodes)}</g></svg>'
    )


def play_art() -> str:
    """A synthwave floor rolling towards you, a sun on the horizon and the pad floating."""
    return (
        '<div class="arcade" aria-hidden="true"><i class="sun"></i><i class="floor"></i>'
        f'<span class="pad">{icon("gamepad")}</span></div>'
    )


def hub_card(h: dict) -> str:
    art = learn_art() if h["key"] == "learn" else play_art()
    stats_html = "".join(
        f'<div><strong>{e(s["value"])}</strong><span>{e(s["label"])}</span></div>' for s in h["stats"]
    )
    return (
        f'<article class="hub hub-{e(h["key"])} spot reveal">'
        f'<a class="hub-art" href="{e(h["url"])}" tabindex="-1" aria-hidden="true">{art}'
        f'<span class="hub-word">{e(h["title"])}</span></a>'
        f'<div class="body"><small>{e(h["eyebrow"])}</small>'
        f'<h3><a href="{e(h["url"])}">{e(h["headline"])}</a></h3><p>{e(h["text"])}</p>'
        f'<div class="hub-stats">{stats_html}</div>'
        f'<div class="chips">{chips(h["chips"])}</div>'
        f'<div class="links"><a class="button light small" href="{e(h["url"])}">{e(h["cta"])} {icon("arrow")}</a>'
        f'<a class="button ghost small" href="{e(h["repo"])}"{external(h["repo"])}>{icon("github")} Code</a>'
        "</div></div></article>"
    )


def redirect(target: str, keep_hash: bool = False, fallback_hash: str = "") -> str:
    """GitHub Pages has no server redirects; this stub forwards old and short URLs."""
    js = (
        f"location.replace('{target}' + (location.hash || '{fallback_hash}'))"
        if keep_hash else f"location.replace('{target}{fallback_hash}')"
    )
    href = target + fallback_hash
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Moved</title><link rel="canonical" href="{href}">'
        f'<meta http-equiv="refresh" content="0; url={href}">'
        '<meta name="robots" content="noindex"><style>html{background:#070709;color:#9a9aa5;'
        'font:14px system-ui}a{color:#b3abff}body{padding:40px}</style>'
        f'<script>{js}</script></head><body><a href="{href}">This page moved: continue</a></body></html>\n'
    )


# ---------- pages ----------


def fill(template: str, values: dict[str, str]) -> str:
    def sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key.startswith("i:"):
            return icon(key[2:])
        if key not in values:
            raise KeyError(f"template asks for {{{{{key}}}}} but nothing provides it")
        return values[key]

    return re.sub(r"\{\{([a-z_:]+)\}\}", sub, template)


def build(content: dict, version: str) -> dict[str, str]:
    """Return {output path: html} for every page."""
    profile, about, work, projects = (
        content["profile"], content["about"], content["work"], content["projects"],
    )
    live = [p for p in projects if p.get("case_study")]
    planned = [p for p in projects if p["status"] == "Planned"]
    earlier = [p for p in projects if not p.get("case_study") and p["status"] != "Planned"]

    shared = {
        **{k: e(v) for k, v in profile.items()},
        "name_upper": e(profile["name"].upper()),
        "about_lead": e(about["lead"]),
        "about_body": "".join(f'<p class="copy">{e(p)}</p>' for p in about["body"]),
        "stats": stats(content["stats"]),
        "work_count": str(len(work)),
        "live_count": str(len(live)),
        "planned_count": str(len(planned)),
        "projects_live": "".join(project_live(p) for p in live),
        "projects_planned": "".join(project_planned(p) for p in planned),
        "projects_earlier": "".join(project_planned(p) for p in earlier),
        "year": str(dt.date.today().year),
        "version": version,
    }
    layout = (PAGES / "layout.html").read_text()
    name, title = profile["name"], profile["title"]

    def page(template: str, page_id: str, page_title: str, description: str, **extra: str) -> str:
        values = {**shared, **extra}
        body = fill((PAGES / template).read_text(), values)
        return fill(layout, {**values, "body": body, "page": page_id,
                             "page_title": e(page_title), "page_description": e(description)})

    numbered = list(enumerate(work, 1))
    out = {
        "index.html": page(
            "home.html", "home", f"{name} · {title}", f"{name}, {title}. {profile['summary']}",
            marquee=marquee(content["marquee"]),
            work_featured="".join(case_card(w, n) for n, w in numbered if w.get("featured")),
            hubs="".join(hub_card(h) for h in content["hubs"]),
            planned_names=e(", ".join(p["title"] for p in planned)),
            journey=journey(content["roles"]),
        ),
        "work/index.html": page(
            "work.html", "work", f"Work · {name}",
            f"{len(work)} projects {name} delivered in industry and research, "
            f"and the AI systems he builds in the open.",
            filters=filters(work), work_all="".join(case_card(w, n) for n, w in numbered),
            standards=standards(content["standards"]),
        ),
        "projects/index.html": redirect("/work/", keep_hash=True, fallback_hash="#open-source"),
        "learn/index.html": redirect("/ml-model-zoo/"),
        "play/index.html": redirect("/featured-games/"),
        "about/index.html": page(
            "about.html", "about", f"About · {name}", about["lead"],
            capabilities=capabilities(content["capabilities"]),
            skills=skills(content["skills"]), roles=roles(content["roles"]),
            education=education(content["education"]),
        ),
        "404.html": page("404.html", "missing", f"Not found · {name}", "Page not found."),
    }

    for i, w in numbered:
        prev_w = work[i - 2] if i > 1 else None
        next_w = work[i] if i < len(work) else None
        link = ""
        if w.get("link"):
            link = (
                f'<a class="button ghost small" href="{e(w["link"])}"{external(w["link"])}>'
                f'{icon("github")} See the code</a>'
            )
        approach = ""
        if w.get("approach"):
            approach = (
                '<section class="reveal"><h2 class="h3">How it was checked</h2>'
                f'<p class="checked">{e(w["approach"])}</p></section>'
            )
        out[f"work/{w['slug']}/index.html"] = page(
            "case.html", "work", f"{w['title']} · {name}", w["text"],
            slug=e(w["slug"]), num=f"{i:02d}", title=e(w["title"]), meta=e(w["meta"]),
            text=e(w["text"]), role=e(w["role"]), areas=e(" · ".join(w["areas"])),
            tags=chips(w["tags"]), link=link, approach=approach,
            points="".join(f"<li>{e(x)}</li>" for x in w["points"]),
            prev=pager_link(prev_w, "prev"), next=pager_link(next_w, "next"),
        )
    return out


def main() -> None:
    content = json.loads((SRC / "data" / "content.json").read_text())
    css, js = (SRC / "site.css").read_bytes(), (SRC / "site.js").read_bytes()
    version = hashlib.sha1(css + js).hexdigest()[:8]  # cache-buster for the two assets

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "public", OUT)
    pages = build(content, version)
    for rel, html in pages.items():
        target = OUT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html)
    (OUT / "site.css").write_bytes(css)
    (OUT / "site.js").write_bytes(js)
    print(f"built {len(pages)} pages into {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
