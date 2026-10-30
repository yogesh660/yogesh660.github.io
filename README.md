# Yogesh Awate · portfolio

Source of [yogesh660.github.io](https://yogesh660.github.io/). Project case studies live in
their own repos and are served next to this site, for example
[/car-agent-harness/](https://yogesh660.github.io/car-agent-harness/) and
[/shelf-vlm/](https://yogesh660.github.io/shelf-vlm/).

## How it is built

Plain HTML, CSS and a little JavaScript, no framework and no npm install. All text lives in
`src/data/content.json`; `scripts/build.py` fills the templates in `src/pages/` with it and writes `dist/`:
`/`, `/work/` (industry projects, then open source), `/work/<slug>/`, `/about/` and `404.html`, plus small
redirect pages for `/projects/` (→ `/work/#open-source`), `/learn/` and `/play/`.

## One site, three repos

The nav is the same everywhere: **Work · Learn · Play · About · Contact**.

| Section | Served at | Repo |
|---|---|---|
| Home, Work, About | `/`, `/work/`, `/about/` | this one |
| Learn | `/ml-model-zoo/` | [ml-model-zoo](https://github.com/yogesh660/ml-model-zoo) |
| Play | `/featured-games/` | [featured-games](https://github.com/yogesh660/featured-games) |

Learn and Play keep a verbatim copy of `src/site.css` and `src/site.js` in their `assets/` folder, so the
nav, buttons, reveals and page transitions are identical. After changing either file here, copy it there:

```bash
cp src/site.css src/site.js ../ml-model-zoo/assets/ && cp src/site.css src/site.js ../featured-games/assets/
```

All links between the three are root-relative (`/work/`, `/ml-model-zoo/`), so they stay same-origin and the
cross-page transitions work under any domain.

```
src/data/content.json   every word on the site: profile, work projects, open-source projects, Learn/Play cards, roles
src/pages/              layout.html wraps home, work, case (one per work project), about, 404
src/site.css            layout and theme (desktop, tablet, phone)
src/site.js             menu, reveals, counters, filters, parallax; pages work without it
public/                 copied as is: portrait, CMS page
scripts/build.py        content + template -> dist/ (Python standard library only)
```

## Run it locally

```bash
python3 scripts/build.py
python3 -m http.server -d dist 8000   # http://localhost:8000
```

## Editing content

Change `src/data/content.json`, either directly or through the Pages CMS editor (`/admin/`,
configured in `.pages.yml`). Adding a project or case study is a new entry in the list; the
page picks it up on the next build.

## Deploying

`.github/workflows/deploy-pages.yml` builds every push. Pushes to `main` also deploy to GitHub
Pages (Settings → Pages → Source: GitHub Actions). Work happens on `feature/` or `fix/`
branches and is merged into `main` once the build is green.
