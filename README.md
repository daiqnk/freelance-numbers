# Freelance Numbers

Static site: free freelance rate/quote calculators and guides. Deployed to https://daiqnk.github.io/freelance-numbers/ by `.github/workflows/deploy.yml`.
Regenerate from `/workspace/hustle/site/` with `python3 /workspace/hustle/build/fn_finalize.py` (box-only).

## Programmatic SEO pages
`python3 build/seo_pages.py` regenerates `etsy-fees/`, `freelance-rates/` and `landlord/` (hubs + pages) from `build/data/*.json` and merges their URLs into `sitemap.xml`.
Add a price point to `etsy_prices.json`, an occupation (BLS OEWS figures) to `occupations.json`, or a topic to `landlord.json`, re-run, commit, push.
Calculators: `assets/seo.js`.
