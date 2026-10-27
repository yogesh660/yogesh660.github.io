# Yogesh Awate · portfolio

Source of [yogesh660.github.io](https://yogesh660.github.io/). Project case studies live in
their own repos and are served next to this site, for example
[/car-agent-harness/](https://yogesh660.github.io/car-agent-harness/) and
[/shelf-vlm/](https://yogesh660.github.io/shelf-vlm/).

## How it is built

Plain HTML, CSS and a little JavaScript, no framework and no npm install. All text lives in
`src/data/content.json`; `scripts/build.py` fills `src/template.html` with it and writes `dist/`.

```
src/data/content.json   every word on the page: profile, projects, case studies, roles
src/template.html       page structure
src/site.css            layout and theme (desktop, tablet, phone)
src/site.js             menu, scroll reveal, hero parallax; the page works without it
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
