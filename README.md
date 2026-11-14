# goldenbooster.uz

Golden Booster motor moylarining Oʻzbekistondagi rasmiy sayti · Официальный сайт Golden Booster в Узбекистане.
Distributor: «MITAL» MChJ. Manufacturer: WORLD OIL KOREA Co., Ltd.

Static site: Uzbek at `/`, Russian at `/ru/`, 55 product pages per language.

## Edit
- Contacts (phones, address, Telegram): `src/data/config.json`
- Page texts UZ/RU: `src/data/i18n.json`
- Uzbek product texts: `src/data/uz.json`
- Templates: `src/templates/`, styles: `src/static/css/site.css`

## Build locally
```
pip install -r requirements.txt
python build.py        # -> dist/
python -m http.server 8000 --directory dist
```

## Deploy
Every push to `main` builds and publishes to GitHub Pages (`.github/workflows/pages.yml`).
Custom domain: Settings → Pages → Custom domain → `goldenbooster.uz`, then set DNS at the registrar.
