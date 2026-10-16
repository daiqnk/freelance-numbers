#!/usr/bin/env python3
"""Generate programmatic SEO pages for Freelance Numbers.

Data lives in build/data/*.json. Run from anywhere:
    python3 build/seo_pages.py
It writes:
  etsy-fees/                      hub + one page per price point (data/etsy_prices.json)
  freelance-rates/                hub + one page per occupation (data/occupations.json, BLS OEWS)
  landlord/                       hub + one page per topic (data/landlord.json)
and rewrites sitemap.xml (keeps every existing URL, adds/updates generated ones).
To add pages weekly: append an entry to the right data file and re-run.
"""
import json, os, re, html, datetime
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "build", "data")
BASE = "https://daiqnk.github.io/freelance-numbers"
P = "/freelance-numbers"
TODAY = datetime.date.today().isoformat()
STORE = "https://hustlemaniac23.gumroad.com/l/"

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)

def money(x):
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def usd(x, dp=2):
    x = Decimal(str(x))
    neg = x < 0
    s = f"{abs(x):,.{dp}f}"
    return ("−" if neg else "") + "$" + s

def esc(s):
    return html.escape(s, quote=True)

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", html.unescape(s))

# ---------------------------------------------------------------- layout
NAV = [("tools/freelance-hourly-rate-calculator/", "Rate calculator"), ("tools/project-quote-calculator/", "Quote calculator"),
       ("guides/", "Guides"), ("templates/", "Templates"), ("about/", "About")]
LOGO = '<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#0f9d74"/><rect x="7" y="17" width="4" height="8" rx="1" fill="#fff"/><rect x="14" y="12" width="4" height="13" rx="1" fill="#fff"/><rect x="21" y="7" width="4" height="18" rx="1" fill="#fff"/></svg>'

def page(path, title, desc, h1, body, crumbs, schema_extra=(), og_type="article", calc=False):
    url = f"{BASE}/{path}"
    nav = "".join(f'<a href="{P}/{h}"{" aria-current=\"page\"" if h == "guides/" else ""}>{t}</a>' for h, t in NAV)
    bc_items = [{"@type": "ListItem", "position": i + 1, "name": strip_tags(n), "item": f"{BASE}/{u}"} for i, (u, n) in enumerate(crumbs)]
    crumbs_html = " › ".join(f'<a href="{P}/{u}">{n}</a>' for u, n in crumbs[:-1]) + " › " + crumbs[-1][1]
    schemas = [{"@context": "https://schema.org", "@type": "Article" if og_type == "article" else "CollectionPage",
                "headline": strip_tags(h1), "description": desc, "datePublished": "2026-10-16", "dateModified": TODAY,
                "mainEntityOfPage": url, "author": {"@type": "Organization", "name": "Freelance Numbers", "url": f"{BASE}/about/"},
                "publisher": {"@type": "Organization", "name": "Freelance Numbers"}, "image": f"{BASE}/assets/og.png"},
               {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": bc_items}]
    schemas += list(schema_extra)
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schemas)
    t = esc(strip_tags(title))
    suffix = " | Freelance Numbers" if len(strip_tags(title)) <= 50 else ""
    d = esc(desc)
    out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}{suffix}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow">
<meta property="og:type" content="{'article' if og_type == 'article' else 'website'}">
<meta property="og:site_name" content="Freelance Numbers">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0f9d74">
<link rel="icon" href="{P}/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{P}/assets/style.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap">
<a class="brand" href="{P}/">{LOGO}<span>Freelance Numbers</span></a>
<nav class="main" aria-label="Main">{nav}</nav>
</div></header>
<main id="main"><div class="wrap">
<div class="crumbs">{crumbs_html}</div>
{body}
</div></main>
<footer class="site"><div class="wrap">
<div class="cols">
<div><p><strong>Freelance Numbers</strong>: free calculators and plain-English guides for freelancers, small sellers and landlords.</p>
<p class="disclaimer">General information only, not tax, legal or financial advice. <a href="{P}/about/">How this site is made</a>.</p></div>
<div><p><a href="{P}/about/">About</a><a href="{P}/privacy/">Privacy</a><a href="{P}/extensions/">Extensions</a><a href="{P}/disclosure/">Disclosure</a><a href="{P}/sitemap.xml">Sitemap</a></p>
<p>© 2026 Freelance Numbers</p></div>
</div></div></footer>
{'<script src="' + P + '/assets/seo.js" defer></script>' if calc else ''}
</body>
</html>
"""
    dest = os.path.join(ROOT, path, "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(out)
    return path

def promo(kind, icon, name, text, slug, price_note, extra=""):
    tag = "Our product · Free" if kind == "free" else "Our product"
    btn = "Get the free version →" if kind == "free" else "See the full template →"
    earn = "" if kind == "free" else " We make this product and earn money if you buy it."
    return f"""<aside class="promo" aria-label="{'Free product' if kind == 'free' else 'Recommended product'}">
<div class="ico" aria-hidden="true">{icon}</div>
<div><span class="tag own">{tag}</span><h3>{name}</h3>
<p>{text}</p>
<a class="btn" href="{STORE}{slug}" rel="noopener">{btn}</a>
<small>{price_note} Sold through Gumroad.{earn}{extra} <a href="{P}/disclosure/">Disclosure</a></small></div></aside>"""

def faq_block(faqs):
    if not faqs:
        return "", []
    h = '<h2 id="faq">Quick answers</h2>' + "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in faqs)
    schema = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    return h, [schema]

def sources_block(items):
    return '<h2 id="sources">Sources</h2><ul class="sources">' + "".join(f'<li><a href="{u}" rel="noopener">{esc(n)}</a></li>' for n, u in items) + "</ul>"

def related(cards):
    return '<section class="block"><h2>Related pages</h2><div class="grid g3">' + "".join(
        f'<a class="card" href="{P}/{u}"><h3>{t}</h3><p>{d}</p></a>' for u, t, d in cards) + "</div></section>"

def field(id_, label, value, hint="", typ="number", step="any"):
    h = f'<span class="hint">{hint}</span>' if hint else ""
    return f'<div class="field"><label for="{id_}">{label}{h}</label><input id="{id_}" type="{typ}" inputmode="decimal" step="{step}" value="{value}"></div>'

def out_dl(rows):
    return '<dl class="out">' + "".join('<dd class="sep"></dd>' if r is None else f'<dt>{r[0]}</dt><dd id="{r[1]}">–</dd>' for r in rows) + "</dl>"

# ---------------------------------------------------------------- Etsy
def etsy_fees(price, ship=0, qty=1, ads=0, fees=None):
    g = money(Decimal(str(price)) * qty + Decimal(str(ship)))
    listing = money(Decimal("0.20") * qty)
    trans = money(g * Decimal("0.065"))
    proc = money(g * Decimal("0.03") + Decimal("0.25"))
    off = min(money(g * Decimal(ads) / 100), Decimal("100")) if ads else Decimal("0")
    total = listing + trans + proc + off
    return dict(gross=g, listing=listing, trans=trans, proc=proc, off=off, total=total, net=g - total)

def price_for_net(net):
    # P - 0.065P - 0.03P - 0.25 - 0.20 = net  ->  P = (net + 0.45) / 0.905  (no shipping, no ads)
    return money((Decimal(str(net)) + Decimal("0.45")) / Decimal("0.905"))

def build_etsy():
    d = load("etsy_prices.json")
    checked = d["checked"]
    prices = d["prices"]
    made = []
    src = [["Etsy Help: What are the Fees and Taxes for Selling on Etsy?", "https://help.etsy.com/hc/en-us/articles/115014483627-What-are-the-Fees-and-Taxes-for-Selling-on-Etsy"],
           ["Etsy Help: Payment processing fees by country", "https://help.etsy.com/hc/en-us/articles/115015628847-What-are-Payment-Processing-Fees-for-Selling-on-Etsy"],
           ["Etsy Help: How Etsy's Offsite Ads work", "https://help.etsy.com/hc/en-us/articles/360000338367-How-Etsy-s-Offsite-Ads-Work"],
           ["Etsy Fees & Payments Policy", "https://www.etsy.com/legal/fees/"]]
    def slug(p): return f"etsy-fees/{p}-dollar-item/"
    for i, p in enumerate(prices):
        base = etsy_fees(p)
        s5 = etsy_fees(p, ship=5)
        a15 = etsy_fees(p, ads=15); a12 = etsy_fees(p, ads=12)
        q2 = etsy_fees(p, qty=2)
        share = base["total"] / base["gross"] * 100
        flat_share = Decimal("0.45") / Decimal(p) * 100
        per_unit_q2 = money(q2["total"] / 2)
        targets = [money(base["net"]), money(base["net"] + Decimal(p) * Decimal("0.10")), money(base["net"] + Decimal(p) * Decimal("0.25"))]
        title = f"Etsy Fees on a ${p} Item (2026): Breakdown & Calculator"
        h1 = f"Etsy fees on a ${p} item"
        desc = (f"A ${p} Etsy sale with free shipping costs a US seller {usd(base['total'])} in fees ({share:.1f}%), leaving {usd(base['net'])}. "
                f"Breakdown, Offsite Ads, shipping and a calculator.")
        neighbours = [x for x in prices if x != p]
        near = sorted(neighbours, key=lambda x: abs(x - p))[:3]
        cmp_rows = "".join(
            f"<tr{' style=\"font-weight:700\"' if x == p else ''}><td>${x}</td><td>{usd(etsy_fees(x)['total'])}</td><td>{etsy_fees(x)['total'] / etsy_fees(x)['gross'] * 100:.1f}%</td><td>{usd(etsy_fees(x)['net'])}</td></tr>"
            for x in sorted(set([p] + near)))
        ad_note = ("" if a15["off"] < 100 else " (the $100 cap applies)")
        faqs = [[f"How much does Etsy take from a ${p} sale?",
                 f"For a US seller using Etsy Payments with free shipping and no Offsite Ads, fees are {usd(base['total'])}: $0.20 listing, {usd(base['trans'])} transaction (6.5%) and {usd(base['proc'])} processing (3% + $0.25). You receive {usd(base['net'])} before your own costs."],
                [f"What if a ${p} sale comes from Offsite Ads?",
                 f"Add {usd(a15['off'])} at the 15% rate (shops under $10,000 in yearly sales) or {usd(a12['off'])} at 12%, bringing total fees to {usd(a15['total'])} or {usd(a12['total'])}."]]
        fq, fschema = faq_block(faqs)
        body = f"""<article class="guide narrow">
<h1>{h1}</h1>
<div class="meta">Fee rates checked {checked} against Etsy's Help Center (US sellers, Etsy Payments). Not affiliated with or endorsed by Etsy, Inc. <a href="{P}/about/">How we make content</a></div>
<p class="lead">On a <strong>${p}</strong> item with free shipping, a US seller pays <strong>{usd(base['total'])}</strong> in Etsy fees, or {share:.1f}% of the sale, and receives <strong>{usd(base['net'])}</strong> before materials, packaging, postage and time. Here is the line-by-line math, what changes with shipping or Offsite Ads, and a calculator for your own numbers.</p>
<h2 id="breakdown">Fee breakdown: ${p} item, free shipping</h2>
<table><tr><th>Fee</th><th>How it's calculated</th><th>Amount</th></tr>
<tr><td>Listing fee</td><td>$0.20 per listing</td><td>{usd(base['listing'])}</td></tr>
<tr><td>Transaction fee</td><td>6.5% × {usd(base['gross'])}</td><td>{usd(base['trans'])}</td></tr>
<tr><td>Payment processing</td><td>3% × {usd(base['gross'])} + $0.25</td><td>{usd(base['proc'])}</td></tr>
<tr><td><strong>Total Etsy fees</strong></td><td>{share:.1f}% of the sale</td><td><strong>{usd(base['total'])}</strong></td></tr>
<tr><td>You receive</td><td>{usd(base['gross'])} − {usd(base['total'])}</td><td><strong>{usd(base['net'])}</strong></td></tr></table>
<p>Each fee is rounded to the cent. The two flat parts ($0.20 listing + $0.25 processing) are {flat_share:.1f}% of a ${p} price, which is why fees bite {'much harder on cheap items' if p <= 15 else 'less as the price rises'}.</p>

<h2 id="scenarios">Same item, different situations</h2>
<table><tr><th>Scenario</th><th>Buyer pays you</th><th>Etsy fees</th><th>You receive</th></tr>
<tr><td>Free shipping (above)</td><td>{usd(base['gross'])}</td><td>{usd(base['total'])}</td><td>{usd(base['net'])}</td></tr>
<tr><td>Buyer pays $5 shipping</td><td>{usd(s5['gross'])}</td><td>{usd(s5['total'])}</td><td>{usd(s5['net'])}</td></tr>
<tr><td>Sale from Offsite Ads, 15% rate</td><td>{usd(a15['gross'])}</td><td>{usd(a15['total'])}</td><td>{usd(a15['net'])}</td></tr>
<tr><td>Sale from Offsite Ads, 12% rate</td><td>{usd(a12['gross'])}</td><td>{usd(a12['total'])}</td><td>{usd(a12['net'])}</td></tr>
<tr><td>Two of this item in one order</td><td>{usd(q2['gross'])}</td><td>{usd(q2['total'])} ({usd(per_unit_q2)} per item)</td><td>{usd(q2['net'])}</td></tr></table>
<ul>
<li><strong>Shipping</strong>: the 6.5% transaction fee and processing fee also apply to what the buyer pays for shipping, so the $5 adds {usd(s5['total'] - base['total'])} in fees. The postage you buy is a separate cost.</li>
<li><strong>Offsite Ads</strong>: the 15% rate applies to shops that have always made less than $10,000 in any 365 days; shops above that pay 12% and can't opt out. The fee never exceeds $100 per order{ad_note}.</li>
<li><strong>Two in one order</strong>: you pay $0.20 for each additional quantity sold, but the $0.25 processing flat fee only once per order.</li>
<li><strong>Sales tax</strong>: Etsy says processing fees are taken from the total sale price including applicable sales tax, so a taxed order costs a little more (3% of the tax amount). Enter the tax in the calculator to include it.</li></ul>

<h2 id="calculator">Calculator: your price, shipping and costs</h2>
<div class="tool"><form class="panel" data-calc="etsy" novalidate>
{field('e_price', 'Item price ($)', p)}
<div class="row2">{field('e_ship', 'Shipping charged to buyer ($)', 0)}{field('e_qty', 'Quantity in order', 1, step='1')}</div>
<div class="row2">{field('e_tax', 'Sales tax on order ($)', 0, 'Only affects processing fee')}{field('e_cost', 'Your costs ($)', 0, 'Materials, packaging, postage')}</div>
<div class="field"><label for="e_ads">Offsite Ads</label><select id="e_ads"><option value="0">Not from Offsite Ads</option><option value="15">Offsite Ads, 15%</option><option value="12">Offsite Ads, 12%</option></select></div>
</form>
<div class="panel results"><div class="big"><div class="lbl">Etsy fees</div><div class="val" id="e_o_fees">–</div><div class="sub" id="e_o_share"></div></div>
{out_dl([('Listing', 'e_o_listing'), ('Transaction (6.5%)', 'e_o_trans'), ('Processing (3% + $0.25)', 'e_o_proc'), ('Offsite Ads', 'e_o_off'), None, ('You receive', 'e_o_net'), ('Profit after your costs', 'e_o_profit'), ('Profit margin', 'e_o_margin')])}
</div></div>

<h2 id="target">What to charge to keep more</h2>
<p>With free shipping and no Offsite Ads, Etsy fees work out to 9.5% of the price plus $0.45. So the price you need for a target payout is <code>(payout + $0.45) ÷ 0.905</code>:</p>
<table><tr><th>Payout you want (before your costs)</th><th>Price to list at</th></tr>
{''.join(f'<tr><td>{usd(t)}</td><td>{usd(price_for_net(t))}</td></tr>' for t in targets)}</table>
<p>Then add your materials, packaging and postage on top of the payout figure, not on top of the price.</p>

<h2 id="compare">Nearby price points</h2>
<table><tr><th>Item price</th><th>Etsy fees</th><th>Fee share</th><th>You receive</th></tr>{cmp_rows}</table>
<p>See every price point on the <a href="{P}/etsy-fees/">Etsy fees by price hub</a>.</p>

{fq}

<h2 id="templates">Track every sale's real profit</h2>
<p>The figures above stop at Etsy's cut. To see profit after materials, packaging and your time across your whole shop, use a spreadsheet with editable fee rates:</p>
{promo('free', '🆓', 'FREE Etsy Pricing Calculator', 'Type a price and your costs to see every fee, real profit, margin, target-margin price and break-even. Excel and Google Sheets.', 'ebwcbx', 'Free ($0+).', ' Not affiliated with Etsy.')}
{promo('paid', '🛍️', 'Etsy Seller Inventory &amp; Profit Sheet', 'Materials and bill of materials, cost per item, stock with reorder flags, sales and expense logs, a monthly profit dashboard and the pricing calculator.', 'yunsmm', 'Excel / Google Sheets · $12.', ' Not affiliated with Etsy.')}
<p>Prefer it in the browser? We also make a <a href="{P}/extensions/">fee calculator extension</a>.</p>
<div class="note warn">Rates are for US sellers whose bank account is in the US, as published on Etsy's Help Center on {checked}. Sellers in other countries pay different processing rates and some pay a regulatory operating fee. Etsy can change fees at any time; check your own Payment account.</div>
{sources_block(src)}
</article>
{related([(slug(x), f'Etsy fees on a ${x} item', f'Fees {usd(etsy_fees(x)["total"])}, you receive {usd(etsy_fees(x)["net"])}.') for x in near] )}"""
        made.append(page(slug(p), title, desc, h1, body, [("", "Home"), ("etsy-fees/", "Etsy fees by price"), (slug(p), f"${p} item")], fschema, calc=True))
    # hub
    rows = "".join(f'<tr><td><a href="{P}/{slug(x)}">${x} item</a></td><td>{usd(etsy_fees(x)["total"])}</td><td>{etsy_fees(x)["total"] / etsy_fees(x)["gross"] * 100:.1f}%</td><td>{usd(etsy_fees(x)["net"])}</td><td>{usd(etsy_fees(x, ads=15)["net"])}</td></tr>' for x in prices)
    body = f"""<article class="guide">
<h1>Etsy fees by item price</h1>
<div class="meta">US seller rates checked {checked} on Etsy's Help Center. Not affiliated with Etsy, Inc.</div>
<p class="lead">How much Etsy keeps at common price points, assuming free shipping, a US bank account and Etsy Payments. Each page has the line-by-line math, shipping and Offsite Ads scenarios, two-item orders and a calculator.</p>
<table><tr><th>Item price</th><th>Etsy fees</th><th>Fee share</th><th>You receive</th><th>You receive if from Offsite Ads (15%)</th></tr>{rows}</table>
<h2>The fees used</h2>
<ul><li>Listing: $0.20 per listing (and per additional quantity sold)</li><li>Transaction: 6.5% of item price plus shipping and gift wrap</li><li>Payment processing (US): 3% + $0.25 per order, on the total including shipping and applicable sales tax</li><li>Offsite Ads (only on attributed orders): 15%, or 12% for shops at $10,000+ in 365 days, capped at $100 per order</li></ul>
<p>For how these fees fit into full profit per item, read the <a href="{P}/guides/etsy-fee-profit-calculator/">Etsy fee and profit guide</a>.</p>
{promo('free', '🆓', 'FREE Etsy Pricing Calculator', 'Every fee, real profit, margin and break-even for your own prices. Excel and Google Sheets.', 'ebwcbx', 'Free ($0+).', ' Not affiliated with Etsy.')}
{promo('paid', '🛍️', 'Etsy Seller Inventory &amp; Profit Sheet', 'Inventory, bill of materials, sales log and monthly profit dashboard with editable fee rates.', 'yunsmm', 'Excel / Google Sheets · $12.', ' Not affiliated with Etsy.')}
{sources_block(src)}
</article>"""
    made.insert(0, page("etsy-fees/", "Etsy Fees by Item Price: $5 to $100 Breakdown (2026)", f"Etsy fees at {len(prices)} common price points from ${prices[0]} to ${prices[-1]} for US sellers: listing, transaction, processing and Offsite Ads, with what you actually receive.", "Etsy fees by item price", body, [("", "Home"), ("etsy-fees/", "Etsy fees by price")], og_type="hub"))
    return made

# ---------------------------------------------------------------- Freelance rates
SE_TOPUP = Decimal("0.0648")   # 15.3% x 92.35% = 14.13% minus the 7.65% an employee pays
COSTS = 6000
HOURS = [1000, 1250, 1500]

def rate_for(annual, hours, costs=COSTS):
    return money((Decimal(str(annual)) * (1 + SE_TOPUP) + costs) / hours)

def build_rates():
    d = load("occupations.json")
    occ = d["occupations"]
    made = []
    def slug(o): return f"freelance-rates/{o['slug']}/"
    src_common = [["BLS: OEWS frequently asked questions (who is covered, 2,080-hour year, benefits excluded)", "https://www.bls.gov/oes/oes_ques.htm"],
                  ["IRS: Self-employment tax (Social Security and Medicare taxes)", "https://www.irs.gov/businesses/small-businesses-self-employed/self-employment-tax-social-security-and-medicare-taxes"]]
    for i, o in enumerate(occ):
        soc = o["soc"].replace("-", "")
        a25 = round(o["p25"] * 2080); a75 = round(o["p75"] * 2080); amed = o["med_annual"]
        tbl = "".join(f"<tr><td>{lbl}</td><td>{usd(w, 0)}</td>" + "".join(f"<td>{usd(rate_for(w, h))}</td>" for h in HOURS) + "</tr>"
                      for lbl, w in [("25th percentile", a25), ("Median", amed), ("75th percentile", a75)])
        med_rate = rate_for(amed, 1250)
        mult = med_rate / Decimal(str(o["med"]))
        title = f"Freelance {o['short']} Rate: How Much to Charge (2026)"
        h1 = f"How much to charge as a freelance {o['title'].lower()}"
        desc = (f"BLS: employed {o['short'].lower()}s earn a median ${o['med']:.2f}/hour (May 2025). Matching that as a freelancer takes about {usd(med_rate)}/hour. Formula and calculator.")
        others = [x for x in occ if x is not o]
        rel = (others[i % len(others):] + others)[:3]
        body = f"""<article class="guide narrow">
<h1>{h1}</h1>
<div class="meta">Wage data: U.S. Bureau of Labor Statistics, OEWS May 2025 (SOC {o['soc']}), retrieved {TODAY}. Our calculations and assumptions are labelled. <a href="{P}/about/">How we make content</a></div>
<p class="lead">Employed {o['plural']} in the US earn a median <strong>${o['med']:.2f} an hour</strong> ({usd(amed, 0)} a year), according to the BLS. A freelancer who wants the same pay has to cover unbilled hours, business costs and the employer half of payroll taxes, which with the assumptions below works out to roughly <strong>{usd(med_rate)} an hour</strong>, about {mult:.1f}× the employee median.</p>

<h2 id="data">What employed {o['plural']} earn (BLS)</h2>
<table><tr><th>Measure (US, May 2025)</th><th>Hourly</th><th>Annual</th></tr>
<tr><td>25th percentile</td><td>${o['p25']:.2f}</td><td>{usd(a25, 0)}*</td></tr>
<tr><td>Median</td><td>${o['med']:.2f}</td><td>{usd(amed, 0)}</td></tr>
<tr><td>75th percentile</td><td>${o['p75']:.2f}</td><td>{usd(a75, 0)}*</td></tr>
<tr><td>Employment</td><td colspan="2">{o['emp']:,} jobs</td></tr></table>
<p><small>* Hourly × 2,080, the full-time year the BLS uses for annual figures. The category covers {o['covers']}. OEWS counts wage and salary employees only; it does not survey the self-employed, and its wages exclude benefits. So this is a benchmark for what an employer would pay, not a survey of freelance rates.</small></p>

<h2 id="math">From employee wage to freelance rate</h2>
<p>An employee is paid for about 2,080 hours a year. A freelancer only bills some of their hours; the rest goes to finding clients, admin, invoicing and unpaid gaps. Our formula:</p>
<pre>hourly rate = (target income × 1.0648 + business costs + benefits you fund)
              ÷ billable hours ÷ (1 − payment fee %)</pre>
<ul><li><strong>1.0648</strong>: self-employment tax is 15.3% (IRS), applied to 92.35% of net earnings, which is 14.13%; an employee pays 7.65% themselves, so the extra is about 6.48%. This is an approximation; it ignores the Social Security wage cap and the income-tax deduction for half of SE tax.</li>
<li><strong>Business costs</strong>: we use <strong>$6,000/year</strong> as an example (software, equipment, insurance, accounting). This is our assumption, not a statistic. Use your own.</li>
<li><strong>Billable hours</strong>: we show 1,000, 1,250 and 1,500 hours a year as scenarios. Again, assumptions: count your own.</li></ul>
<table><tr><th>Target income</th><th>Annual</th><th>1,000 h</th><th>1,250 h</th><th>1,500 h</th></tr>{tbl}</table>
<p>Hourly rates needed, before payment-processor fees and before any health insurance or retirement contributions you add.</p>

<h2 id="calculator">Your rate calculator</h2>
<div class="tool"><form class="panel" data-calc="rate" novalidate>
{field('r_income', 'Target income ($/year)', amed, 'Pre-filled with the BLS median for this job')}
<div class="row2">{field('r_costs', 'Business costs ($/year)', COSTS)}{field('r_benefits', 'Benefits you fund ($/year)', 0, 'Health cover, retirement')}</div>
<div class="row2">{field('r_hours', 'Billable hours per year', 1250, step='1')}{field('r_fee', 'Payment fees (%)', 0, 'Card/platform fees, e.g. 3')}</div>
<div class="row2">{field('r_day', 'Billable hours in a day rate', 6)}<div class="field"><label class="check" for="r_se"><input type="checkbox" id="r_se" checked> Add US self-employment tax top-up (≈6.48%)</label></div></div>
</form>
<div class="panel results"><div class="big"><div class="lbl">Minimum hourly rate</div><div class="val" id="r_o_rate">–</div><div class="sub" id="r_o_week"></div></div>
{out_dl([('Day rate', 'r_o_day'), ('Revenue needed per year', 'r_o_year'), ('Revenue needed per month', 'r_o_month'), ('Of which SE tax top-up', 'r_o_se')])}
</div></div>

<h2 id="pricing">Turning the hourly floor into quotes</h2>
<p>Many freelance {o['plural']} price {o['units']}. Whatever the unit, estimate the hours behind it and check the quote against your floor with the <a href="{P}/tools/project-quote-calculator/">project quote calculator</a>.</p>
<p><strong>Tip:</strong> {o['tip']}</p>
<p>For the full method (time off, non-billable share, tax set-aside) see <a href="{P}/guides/how-to-calculate-freelance-hourly-rate/">how to calculate your freelance hourly rate</a> and <a href="{P}/guides/how-much-to-set-aside-for-taxes-freelancer/">how much to set aside for taxes</a>.</p>

<h2 id="tools">Free tool and invoice kit</h2>
<p>Run your full numbers in the free <a href="{P}/tools/freelance-hourly-rate-calculator/">freelance hourly rate calculator</a> (no sign-up, runs in your browser). To quote, invoice and chase payment from one spreadsheet:</p>
{promo('paid', '📊', 'Freelance Take-Home &amp; Invoice Kit', 'Rate calculator, quote builder with a floor check, printable invoice, 200-row invoice log with overdue flags, per-client totals and a monthly cash dashboard.', 'ulujfl', 'Excel / Google Sheets · $12.')}
<div class="note">Not tax or financial advice. Local rates vary a lot by city, niche and experience; BLS also publishes state and metro data for this occupation (link below).</div>
{sources_block([[f"BLS OEWS May 2025: {strip_tags(o['title'])}s ({o['soc']})", f"https://www.bls.gov/oes/2025/may/oes{soc}.htm"]] + src_common)}
</article>
{related([(slug(x), f"Freelance {x['title'].lower()} rates", f"BLS median ${x['med']:.2f}/h → about {usd(rate_for(x['med_annual'], 1250))}/h freelance.") for x in rel])}"""
        made.append(page(slug(o), title, desc, h1, body, [("", "Home"), ("freelance-rates/", "Freelance rates by job"), (slug(o), strip_tags(o['title']))], calc=True))
    rows = "".join(f'<tr><td><a href="{P}/{slug(o)}">{o["title"]}</a></td><td>${o["med"]:.2f}</td><td>{usd(o["med_annual"], 0)}</td><td>{usd(rate_for(o["med_annual"], 1250))}</td></tr>' for o in sorted(occ, key=lambda x: -x["med"]))
    body = f"""<article class="guide">
<h1>Freelance rates by job: from BLS wages to a rate floor</h1>
<div class="meta">Wage data: BLS OEWS May 2025, retrieved {TODAY}. Freelance figures are our calculation with stated assumptions.</div>
<p class="lead">What employed people in each job earn, and the hourly rate a freelancer would need to match that median after unbilled time, business costs and self-employment tax. Each page has percentiles, scenarios and a calculator pre-filled for that job.</p>
<table><tr><th>Job</th><th>BLS median hourly</th><th>BLS median annual</th><th>Freelance rate to match (1,250 billable h)</th></tr>{rows}</table>
<p><small>Freelance rate = (median annual × 1.0648 + $6,000 costs) ÷ 1,250 hours. The 1.0648 is the self-employment tax top-up explained on each page; $6,000 and 1,250 hours are example assumptions. OEWS covers employees only, not freelancers.</small></p>
<p>Work out your own number with the <a href="{P}/tools/freelance-hourly-rate-calculator/">freelance hourly rate calculator</a> or read <a href="{P}/guides/how-to-calculate-freelance-hourly-rate/">how to calculate your freelance hourly rate</a>.</p>
{promo('paid', '📊', 'Freelance Take-Home &amp; Invoice Kit', 'Rate calculator, quote builder, invoice template and invoice log with overdue flags in one spreadsheet.', 'ulujfl', 'Excel / Google Sheets · $12.')}
{sources_block([["BLS Occupational Employment and Wage Statistics", "https://www.bls.gov/oes/"]] + src_common)}
</article>"""
    made.insert(0, page("freelance-rates/", "Freelance Rates by Job (2026): BLS Wages to Hourly Rate", f"Hourly rates freelancers in {len(occ)} jobs would need to match employee median pay (BLS May 2025), with the formula and assumptions shown.", "Freelance rates by job", body, [("", "Home"), ("freelance-rates/", "Freelance rates by job")], og_type="hub"))
    return made

# ---------------------------------------------------------------- Landlord
CALC_FORMS = {
 "exp": lambda: f"""<div class="tool"><form class="panel" data-calc="exp" novalidate>
{field('x_rent', 'Rent received this year ($)', 18000)}
<div class="row2">{field('x5','5 Advertising',150)}{field('x6','6 Auto and travel',300)}</div>
<div class="row2">{field('x7','7 Cleaning and maintenance',600)}{field('x8','8 Commissions',0)}</div>
<div class="row2">{field('x9','9 Insurance',1100)}{field('x10','10 Legal and professional fees',250)}</div>
<div class="row2">{field('x11','11 Management fees',0)}{field('x12','12 Mortgage interest',6500)}</div>
<div class="row2">{field('x13','13 Other interest',0)}{field('x14','14 Repairs',900)}</div>
<div class="row2">{field('x15','15 Supplies',120)}{field('x16','16 Taxes',2400)}</div>
<div class="row2">{field('x17','17 Utilities',480)}{field('x19','19 Other',0)}</div>
{field('x18','18 Depreciation',5818, 'From the depreciation calculator')}
</form>
<div class="panel results"><div class="big"><div class="lbl">Net rental income (loss)</div><div class="val" id="x_o_net">–</div><div class="sub">Rent minus all lines 5–19</div></div>
{out_dl([('Cash expenses (excl. depreciation)', 'x_o_cash'), ('All expenses incl. depreciation', 'x_o_all'), ('Rent minus cash expenses', 'x_o_before')])}
<p class="sub"><small>Example figures are made up for illustration. Loss limits (passive activity, at-risk) can apply; see Pub. 527 chapter 3.</small></p></div></div>""",
 "rep": lambda: f"""<div class="tool"><form class="panel" data-calc="rep" novalidate>
{field('p_cost','Cost of the work ($)',4000)}
<div class="row2">{field('p_month','Month placed in service (1–12)',6,step='1')}{field('p_tax','Your marginal tax rate (%)',22,'Your own rate; for the timing estimate')}</div>
</form>
<div class="panel results"><div class="big"><div class="lbl">Year-one deduction if it's a repair</div><div class="val" id="p_o_rep">–</div></div>
{out_dl([('Year-one depreciation if a 27.5-yr improvement', 'p_o_imp'), ('Each full year after that', 'p_o_full'), ('Tax deferred in year one (approx.)', 'p_o_diff')])}
<p class="sub"><small>Improvement figures assume it's added to a residential rental building (27.5 years, mid-month). Appliances and carpet are 5-year property instead.</small></p></div></div>""",
 "dep": lambda: f"""<div class="tool"><form class="panel" data-calc="dep" novalidate>
{field('d_price','Purchase price incl. land ($)',250000)}
<div class="row2">{field('d_land','Land value ($)',50000,'Not depreciable')}{field('d_add','Closing costs added to basis ($)',3500,'Title, recording, transfer tax…')}</div>
{field('d_month','Month placed in service (1–12)',4,step='1')}
</form>
<div class="panel results"><div class="big"><div class="lbl">First-year depreciation</div><div class="val" id="d_o_y1">–</div><div class="sub" id="d_o_y1pct"></div></div>
{out_dl([('Depreciable basis (building)', 'd_o_basis'), ('Each full year (÷ 27.5)', 'd_o_full'), ('Per month', 'd_o_month')])}
</div></div>""",
 "cf": lambda: f"""<div class="tool"><form class="panel" data-calc="cf" novalidate>
<div class="row2">{field('c_rent','Monthly rent ($)',1800)}{field('c_vac','Vacancy (%)',5)}</div>
<div class="row2">{field('c_mort','Mortgage P&amp;I ($/mo)',1050)}{field('c_tax','Property tax ($/mo)',200)}</div>
<div class="row2">{field('c_ins','Insurance ($/mo)',90)}{field('c_hoa','HOA ($/mo)',0)}</div>
<div class="row2">{field('c_util','Utilities you pay ($/mo)',40)}{field('c_mgmt','Management (% of rent)',0)}</div>
<div class="row2">{field('c_maint','Maintenance reserve (% of rent)',5)}{field('c_capex','Capital reserve (% of rent)',5)}</div>
</form>
<div class="panel results"><div class="big"><div class="lbl">Monthly cash flow</div><div class="val" id="c_o_cash">–</div></div>
{out_dl([('Effective rent after vacancy', 'c_o_eff'), ('Operating costs and reserves', 'c_o_opex'), ('Net operating income', 'c_o_noi'), None, ('Cash flow per year', 'c_o_year'), ('Break-even rent', 'c_o_be')])}
<p class="sub"><small>Default inputs are an illustration, not market data.</small></p></div></div>""",
 "dpst": lambda: f"""<div class="tool"><form class="panel" data-calc="dpst" novalidate>
{field('s_rec','Deposits received and held ($)',2000)}
<div class="row2">{field('s_kept','Kept for damage/breach this year ($)',350)}{field('s_last','Applied as final rent ($)',0,'Advance rent')}</div>
</form>
<div class="panel results"><div class="big"><div class="lbl">Deposit amount that is income</div><div class="val" id="s_o_inc">–</div></div>
{out_dl([('To return to tenant', 's_o_ret'), ('Total received', 's_o_hold')])}
<p class="sub"><small>A "deposit" agreed as final rent is income when received, per Pub. 527.</small></p></div></div>""",
 "inc": lambda: f"""<div class="tool"><form class="panel" data-calc="inc" novalidate>
<div class="row2">{field('i_rent','Normal rent received ($)',18000)}{field('i_adv','Advance rent received ($)',0)}</div>
<div class="row2">{field('i_paid','Your expenses paid by tenant ($)',0)}{field('i_svc','Services/property instead of rent, FMV ($)',0)}</div>
<div class="row2">{field('i_cancel','Lease cancellation payments ($)',0)}{field('i_dep','Deposits kept or used as rent ($)',0)}</div>
</form>
<div class="panel results"><div class="big"><div class="lbl">Total rental income</div><div class="val" id="i_o_total">–</div></div>
{out_dl([('Of which also deductible as expenses (if deductible)', 'i_o_offset')])}
</div></div>""",
 "mil": lambda: f"""<div class="tool"><form class="panel" data-calc="mil" novalidate>
<div class="row2">{field('m_a','Miles Jan–Jun',180)}{field('m_ra','Rate (¢/mile)',72.5)}</div>
<div class="row2">{field('m_b','Miles Jul–Dec',220)}{field('m_rb','Rate (¢/mile)',76)}</div>
</form>
<div class="panel results"><div class="big"><div class="lbl">Standard mileage amount</div><div class="val" id="m_o_tot">–</div></div>
{out_dl([('Jan–Jun', 'm_o_a'), ('Jul–Dec', 'm_o_b')])}
<p class="sub"><small>Pre-filled with 2026 rates. For 2025 use 70¢ in both rows.</small></p></div></div>""",
}

def dep_table():
    rows = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for m in range(1, 13):
        frac = Decimal(12 - m) + Decimal("0.5")
        pc = frac / 12 / Decimal("27.5") * 100
        amt = money(Decimal(200000) * frac / 12 / Decimal("27.5"))
        rows.append(f"<tr><td>{months[m-1]}</td><td>{pc:.3f}%</td><td>{usd(amt)}</td></tr>")
    return ("<p>Year-one share of a full year's depreciation by the month the building is placed in service, and the dollar amount for an example $200,000 building basis. Full years are 3.636% ($7,272.73 on $200,000).</p>"
            "<table><tr><th>Placed in service</th><th>Year-one %</th><th>On $200,000 basis</th></tr>" + "".join(rows) + "</table>"
            "<p><small>Computed as (12 − month + 0.5) ÷ 12 ÷ 27.5. IRS Table 2-2d shows the same percentages rounded to three decimals.</small></p>")

def build_landlord():
    d = load("landlord.json")
    pages = d["pages"]
    made = []
    for i, pg in enumerate(pages):
        path = f"landlord/{pg['slug']}/"
        secs = "".join(f'<h2 id="s{j}">{h}</h2>' + (dep_table() if c == "%%DEP_TABLE%%" else c) for j, (h, c) in enumerate(pg["sections"]))
        fq, fschema = faq_block(pg["faq"])
        rel = [p for p in pages if p is not pg]
        rel = (rel[i % len(rel):] + rel)[:3]
        body = f"""<article class="guide narrow">
<h1>{pg['title']}</h1>
<div class="meta">Checked {d['checked']} against IRS Publication 527 (2025) and the other IRS pages listed under Sources. US federal rules only. <a href="{P}/about/">How we make content</a></div>
<p class="lead">{pg['lead']}</p>
<h2 id="calculator">Calculator</h2>
{CALC_FORMS[pg['calc']]()}
{secs}
{fq}
<h2 id="templates">Keep landlord books in these categories</h2>
<p>Our rental spreadsheets use Schedule E-style expense categories (you can rename them), track security deposits separately from income, and total everything per property:</p>
{promo('free', '🆓', 'FREE Rental Income &amp; Expense Tracker', 'Rent and expenses for up to 3 rentals with editable Schedule E-style categories, monthly net cash flow, totals per property and per category. Excel and Google Sheets.', 'cswnop', 'Free ($0+).')}
{promo('paid', '🏠', 'Rental Property Bookkeeping Spreadsheet', 'Books for up to 10 rentals: income and expenses by Schedule E line name, tenants and leases with late flags, rent roll, tenant ledger, security deposits with return deadlines, a P&amp;L per property and a dashboard.', 'msbbh', 'Excel / Google Sheets · $12.')}
<div class="note">General information, not tax or legal advice. State and local rules (for example on security deposits) differ. Ask a qualified professional for your situation.</div>
{sources_block(pg['sources'])}
</article>
{related([(f"landlord/{x['slug']}/", x['short'], x['desc'][:110].rsplit(' ', 1)[0] + '…') for x in rel])}"""
        made.append(page(path, pg.get("seo_title", pg["title"]), pg["desc"], pg["title"], body, [("", "Home"), ("landlord/", "Landlord bookkeeping"), (path, pg["short"])], fschema, calc=True))
    cards = "".join(f'<a class="card" href="{P}/landlord/{p["slug"]}/"><span class="tag">Calculator + guide</span><h3>{p["short"]}</h3><p>{p["desc"]}</p></a>' for p in pages)
    body = f"""<article class="guide">
<h1>Landlord bookkeeping: categories, rules and calculators</h1>
<div class="meta">Based on IRS Publication 527 (2025) and IRS rate pages, checked {d['checked']}. US federal rules.</div>
<p class="lead">Plain-English pages for small landlords who do their own books: what counts as income, which expense goes on which Schedule E line, repairs versus improvements, depreciation and cash flow. Each has a calculator that runs in your browser.</p>
</article>
<section class="block"><div class="grid g2">{cards}</div></section>
<article class="guide narrow">
{promo('free', '🆓', 'FREE Rental Income &amp; Expense Tracker', 'Rent and expenses for up to 3 rentals with Schedule E-style categories and monthly cash flow. Excel and Google Sheets.', 'cswnop', 'Free ($0+).')}
{promo('paid', '🏠', 'Rental Property Bookkeeping Spreadsheet', 'Up to 10 rentals: Schedule E-style expense log, tenants and leases, rent roll, tenant ledger, deposits, per-property P&amp;L and dashboard.', 'msbbh', 'Excel / Google Sheets · $12.')}
{sources_block([["IRS Publication 527 (2025), Residential Rental Property", "https://www.irs.gov/publications/p527"]])}
</article>"""
    made.insert(0, page("landlord/", "Landlord Bookkeeping Guides and Calculators", "Free guides and calculators for small landlords: Schedule E expense categories, repairs vs improvements, depreciation, cash flow, deposits and mileage.", "Landlord bookkeeping", body, [("", "Home"), ("landlord/", "Landlord bookkeeping")], og_type="hub"))
    return made

# ---------------------------------------------------------------- sitemap
def update_sitemap(generated):
    sm = os.path.join(ROOT, "sitemap.xml")
    existing = re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", open(sm, encoding="utf-8").read())
    entries = dict(existing)
    for path in generated:
        entries[f"{BASE}/{path}"] = TODAY
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines += [f"  <url><loc>{u}</loc><lastmod>{m}</lastmod></url>" for u, m in entries.items()]
    lines.append("</urlset>")
    open(sm, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return len(entries)

if __name__ == "__main__":
    made = build_etsy() + build_rates() + build_landlord()
    n = update_sitemap(made)
    print(f"generated {len(made)} pages; sitemap has {n} URLs")
