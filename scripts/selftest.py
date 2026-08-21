# -*- coding: utf-8 -*-
"""
CalcNest MVP V1.5 — selftest (GATE-B)
静态验证：文件齐全 / 关键 DOM 结构 / 计算逻辑断言 / SEO 要素 / 链接完整性
用法: python scripts/selftest.py
"""
import os
import re
import sys
import html.parser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASS = 0
FAIL = 0

def ok(name):
    global PASS
    PASS += 1
    print("[PASS] %s" % name)

def bad(name, detail=""):
    global FAIL
    FAIL += 1
    print("[FAIL] %s %s" % (name, ("-> " + detail) if detail else ""))

def read(p):
    with open(os.path.join(ROOT, p), "r", encoding="utf-8") as f:
        return f.read()

# ---------- 1. 文件齐全 ----------
REQUIRED = [
    "index.html", "about.html", "privacy.html", "terms.html", "contact.html",
    "css/style.css", "js/main.js",
    "tools/rent-affordability-calculator.html",
    "tools/retirement-savings-calculator.html",
    "tools/credit-card-payoff-calculator.html",
    "tools/compound-interest-calculator.html",
    "articles/how-much-rent-can-i-afford.html",
    "articles/rent-to-income-ratio-explained.html",
    "articles/how-much-to-save-for-retirement.html",
    "articles/four-percent-rule-retirement-explained.html",
    "articles/credit-card-snowball-vs-avalanche.html",
    "articles/credit-card-minimum-payment-trap.html",
    "articles/how-compound-interest-works.html",
    "articles/rule-of-72-explained.html",
    "articles/security-deposit-calculator-guide.html",
    "articles/roth-ira-vs-traditional-explained.html",
    "articles/credit-utilization-ratio-explained.html",
    "sitemap.xml", "robots.txt", "404.html", "js/analytics.js",
]
print("=== 1. 文件齐全 ===")
for f in REQUIRED:
    if os.path.isfile(os.path.join(ROOT, f)):
        ok("file: %s" % f)
    else:
        bad("file missing: %s" % f)

# 1.1 文章质量（AdSense 审核关键：每篇 ≥800 词）
print("\n=== 1.1 文章字数（AdSense 审核标准 ≥800 词） ===")
import re as _re
article_files = [f for f in REQUIRED if f.startswith("articles/")]
for f in article_files:
    h = read(f)
    m = _re.search(r'<article class="prose">(.*?)</article>', h, _re.S)
    body = m.group(1) if m else h
    body = _re.sub(r"<script.*?</script>", "", body, flags=_re.S)
    text = _re.sub(r"<[^>]+>", " ", body)
    words = len(_re.findall(r"[A-Za-z]+", text))
    if words >= 800:
        ok("%s: %d words" % (f, words))
    else:
        bad("%s: only %d words (<800)" % (f, words))

# ---------- 2. 每页关键结构 ----------
print("\n=== 2. 页面结构 ===")
PAGES = [f for f in REQUIRED if f.endswith(".html")]
for f in PAGES:
    try:
        h = read(f)
    except Exception as e:
        bad("read %s" % f, str(e)); continue
    base = f.split("/")[-1]
    if f == "index.html":
        prefix = ""
    elif f.count("/") >= 1 and "tools" in f or "articles" in f:
        prefix = "../"
    else:
        prefix = ""
    # title & meta description
    if re.search(r"<title>[^<]{10,}</title>", h):
        ok("%s has title" % base)
    else:
        bad("%s title" % base, "missing or too short")
    if 'name="description"' in h:
        ok("%s has meta description" % base)
    else:
        bad("%s meta description" % base)
    if "stylesheet" in h:
        ok("%s links stylesheet" % base)
    else:
        bad("%s stylesheet" % base)
    # canonical
    if "rel=\"canonical\"" in h:
        ok("%s has canonical" % base)
    else:
        bad("%s canonical" % base)
    # cookie banner (compliance)
    if 'id="cookie-banner"' in h and 'id="cookie-accept"' in h:
        ok("%s cookie banner" % base)
    else:
        bad("%s cookie banner" % base)
    # footer year span
    if 'id="year"' in h:
        ok("%s footer year" % base)
    else:
        bad("%s footer year" % base)
    # main.js loaded
    if "main.js" in h:
        ok("%s loads main.js" % base)
    else:
        bad("%s main.js" % base)

# ---------- 3. 计算逻辑断言 ----------
print("\n=== 3. 计算逻辑 (静态公式核验) ===")
# Rent: safe = gross * 0.30 (30% rule)
rent_html = read("tools/rent-affordability-calculator.html")
if "var safeRent = gross * rule;" in rent_html and 'value="30"' in rent_html:
    ok("rent: 30% rule present")
else:
    bad("rent: 30% rule missing")
if "((debts + safeRent) / gross) * 100" in rent_html:
    ok("rent: DTI formula present")
else:
    bad("rent: DTI formula")
if "id=\"gross-income\"" in rent_html and "id=\"monthly-debts\"" in rent_html and "id=\"city-rule\"" in rent_html:
    ok("rent: key inputs present")
else:
    bad("rent: key inputs")

# Retirement: FV of annuity
ret_html = read("tools/retirement-savings-calculator.html")
if "Math.pow(1 + i, n)" in ret_html and "PMT * ((Math.pow(1 + i, n) - 1) / i)" in ret_html:
    ok("retirement: FV annuity formula present")
else:
    bad("retirement: FV annuity formula")
if 'id="withdrawal-rate"' in ret_html and "withdrawal" in ret_html:
    ok("retirement: withdrawal slider present")
else:
    bad("retirement: withdrawal slider")

# Credit card: month-by-month simulation
cc_html = read("tools/credit-card-payoff-calculator.html")
if "cur * monthlyRate" in cc_html and "cur + interest - payment" in cc_html:
    ok("creditcard: month-by-month sim present")
else:
    bad("creditcard: simulation logic")
if "cc-balance" in cc_html and "cc-apr" in cc_html and "cc-extra" in cc_html:
    ok("creditcard: key inputs present")
else:
    bad("creditcard: key inputs")
# V1.5 回归：永不还清检测（防"天文数字"复发）
if "neverPaidOff" in cc_html and "payment <= interest" in cc_html:
    ok("creditcard V1.5: neverPaidOff guard present")
else:
    bad("creditcard V1.5: neverPaidOff guard MISSING")
if "Interest saved vs minimum-only" in cc_html:
    ok("creditcard: saved label present")
else:
    bad("creditcard: saved label missing")
# V1.5 回归：APR 上限防御（0~100）
if "apr > 100" in cc_html:
    ok("creditcard V1.5: APR 0~100 guard present")
else:
    bad("creditcard V1.5: APR guard MISSING")

# V1.5 强复审回归：4 工具统一 sanitize + finiteMoney + 负值/上限守卫
ci_html = read("tools/compound-interest-calculator.html")
for t_html, tname in [
    (rent_html, "rent"),
    (ret_html, "retirement"),
    (cc_html, "creditcard"),
    (ci_html, "compound"),
]:
    if "function sanitize" in t_html and "finiteMoney" in t_html:
        ok("%s V1.5: sanitize+finiteMoney present" % tname)
    else:
        bad("%s V1.5: sanitize/finiteMoney MISSING" % tname)
    if tname in ("retirement", "compound"):
        if "rate > 100" in t_html and "rate < 0" in t_html:
            ok("%s V1.5: rate 0~100 guard present" % tname)
        else:
            bad("%s V1.5: rate guard MISSING" % tname)
    elif tname == "rent":
        if "debts < 0" in t_html:
            ok("rent V1.5: negative-value guard present")
        else:
            bad("rent V1.5: negative guard MISSING")

# Compound interest: FV with contributions
if "Math.pow(1 + i, n)" in ci_html and "P + PMT * n" in ci_html:
    ok("compound: FV formula present")
else:
    bad("compound: FV formula")
if "simpleFutureValue" in ci_html:
    ok("compound: simple-interest comparison present")
else:
    bad("compound: simple-interest comparison")

# ---------- 4. Schema.org ----------
print("\n=== 4. 结构化数据 ===")
schema_pages = {
    "index.html": ["WebSite", "Organization"],
    "about.html": ["AboutPage"],
    "contact.html": ["ContactPage"],
    "tools/rent-affordability-calculator.html": ["SoftwareApplication", "FAQPage"],
    "tools/retirement-savings-calculator.html": ["SoftwareApplication"],
    "tools/credit-card-payoff-calculator.html": ["SoftwareApplication"],
    "tools/compound-interest-calculator.html": ["SoftwareApplication"],
    "articles/how-much-rent-can-i-afford.html": ["Article"],
    "articles/how-much-to-save-for-retirement.html": ["Article"],
    "articles/credit-card-snowball-vs-avalanche.html": ["Article"],
    "articles/how-compound-interest-works.html": ["Article"],
}
for f, types in schema_pages.items():
    try:
        h = read(f)
    except Exception:
        bad("schema read %s" % f); continue
    for t in types:
        if ('"@type": "%s"' % t) in h:
            ok("%s schema %s" % (f, t))
        else:
            bad("%s schema %s" % (f, t))

# ---------- 5. sitemap 覆盖 ----------
print("\n=== 5. sitemap 完整性 ===")
try:
    sm = read("sitemap.xml")
    urls = re.findall(r"<loc>(.*?)</loc>", sm)
    if len(urls) == 21:
        ok("sitemap: 21 URLs")
    else:
        bad("sitemap: expected 21, got %d" % len(urls))
    missing = [u for u in urls if not u.startswith("https://aicalcnest.com/")]
    if not missing:
        ok("sitemap: all URLs use canonical domain")
    else:
        bad("sitemap: bad URLs", str(missing))
    for f in REQUIRED:
        if f.endswith(".html"):
            slug = f if f == "index.html" else f
            if slug.replace(".html", ".html") in sm.replace("https://aicalcnest.com/", ""):
                pass
    if "robots.txt" in read("robots.txt"):
        pass
    if "Sitemap:" in read("robots.txt"):
        ok("robots.txt: sitemap referenced")
    else:
        bad("robots.txt: sitemap reference")
except Exception as e:
    bad("sitemap/robots", str(e))

# ---------- 6. 内部链接完整性 ----------
print("\n=== 6. 内部链接完整性 ===")
def extract_links(html_text):
    links = set()
    for m in re.finditer(r'href="([^"#][^"]*)"', html_text):
        href = m.group(1)
        if href.startswith(("http", "mailto:", "data:")):
            continue
        if href.endswith(".html"):
            links.add(href)
    return links

broken = []
for f in PAGES:
    try:
        h = read(f)
    except Exception:
        continue
    base_dir = os.path.dirname(f)
    for link in extract_links(h):
        target = os.path.normpath(os.path.join(base_dir, link))
        if not os.path.isfile(os.path.join(ROOT, target)):
            broken.append("%s -> %s" % (f, link))
if not broken:
    ok("all internal .html links resolve")
else:
    bad("broken internal links", "; ".join(broken[:10]))

# ---------- 7. 合规四件套 (AdSense 关键) ----------
print("\n=== 7. 合规页面 ===")
for f in ["about.html", "privacy.html", "terms.html", "contact.html"]:
    h = read(f)
    if "<h1>" in h:
        ok("%s has h1" % f)
    else:
        bad("%s h1" % f)
privacy = read("privacy.html")
if "1280268550@qq.com" in privacy and "GDPR" in privacy:
    ok("privacy: contact + GDPR present")
else:
    bad("privacy: contact/GDPR")

# ---------- 8. 版本号 ----------
print("\n=== 8. 版本标识 ===")
if "V1.5" in read("css/style.css") or "V1.5" in read("js/main.js"):
    ok("version marker V1.5 in assets")
else:
    bad("version marker V1.5 missing in assets")

print("\n===== 结果: %d PASS / %d FAIL =====" % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
