# -*- coding: utf-8 -*-
"""
CalcNest MVP V1.4 — HTML 强制复审 (GATE-C)
检查：DOM 完整性 / 事件绑定 / 键名一致性 / 表单联动 / 运行时防御
用法: python scripts/html_review.py
"""
import os
import re
import sys

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

TOOLS = [
    "tools/rent-affordability-calculator.html",
    "tools/retirement-savings-calculator.html",
    "tools/credit-card-payoff-calculator.html",
    "tools/compound-interest-calculator.html",
]

print("=== 1. 共用资产 ===")
css = read("css/style.css")
js = read("js/main.js")
for item in ["btn", "faq-item", "cookie-banner", "form-group", "result-card", "insight-box"]:
    if item in css:
        ok("css has .%s" % item)
    else:
        bad("css missing .%s" % item)
if "getElementById('nav-toggle')" in js or "getElementById(\"nav-toggle\")" in js or "nav-toggle" in js:
    ok("js binds nav-toggle")
else:
    bad("js missing nav-toggle bind")
if "cookie-accept" in js:
    ok("js binds cookie-accept")
else:
    bad("js missing cookie-accept bind")
if "DOMContentLoaded" in js:
    ok("js uses DOMContentLoaded")
else:
    bad("js missing DOMContentLoaded")

print("\n=== 2. 工具页控件完整性 ===")
for t in TOOLS:
    try:
        h = read(t)
    except Exception as e:
        bad("read %s" % t, str(e)); continue
    name = t.split("/")[-1]
    # extract inline script
    scripts = re.findall(r"<script>(.*?)</script>", h, re.S)
    js_code = "\n".join(scripts)
    # find all input/select ids in HTML
    ids = re.findall(r'id="([^"]+)"', h)
    # forms
    if "<form" in h:
        ok("%s has form" % name)
    else:
        bad("%s no form" % name)
    # each input/select id referenced in JS getElementById
    controls = re.findall(r'<(?:input|select|button)[^>]*id="([^"]+)"', h)
    controls = [c for c in controls if c not in ("nav-toggle", "cookie-accept")]
    for c in controls:
        # must be referenced either via getElementById or a var assignment in inline js
        if ("getElementById('" + c + "')" in js_code) or ("getElementById(\"" + c + "\")" in js_code) or ("'" + c + "'" in js_code):
            ok("%s: %s referenced" % (name, c))
        else:
            bad("%s: %s NOT referenced in JS" % (name, c))
    # form submit listener
    if "addEventListener('submit'" in js_code or 'addEventListener("submit"' in js_code:
        ok("%s: submit listener" % name)
    else:
        bad("%s: no submit listener" % name)
    # preventDefault (no page reload)
    if "preventDefault" in js_code:
        ok("%s: preventDefault (SPA-like)" % name)
    else:
        bad("%s: no preventDefault" % name)
    # result card toggle
    if "result-card" in js_code:
        ok("%s: result-card shown on calc" % name)
    else:
        bad("%s: result-card not toggled" % name)

print("\n=== 3. 数值防御 (V1.4: sanitize + finiteMoney + 守卫) ===")
for t in TOOLS:
    h = read(t)
    name = t.split("/")[-1]
    scripts = re.findall(r"<script>(.*?)</script>", h, re.S)
    js_code = "\n".join(scripts)
    if "function sanitize" in js_code:
        ok("%s: sanitize 防御存在 (V1.4)" % name)
    else:
        bad("%s: sanitize 缺失" % name)
    if "finiteMoney" in js_code:
        ok("%s: finiteMoney 兜底存在 (V1.4)" % name)
    else:
        bad("%s: finiteMoney 缺失" % name)
    # 守卫：每个工具按自身的零/负值/上限守卫检查
    guards = {
        "rent-affordability-calculator.html": ["gross <= 0", "debts < 0"],
        "retirement-savings-calculator.html": ["years <= 0", "rate > 100", "rate < 0"],
        "credit-card-payoff-calculator.html": ["balance <= 0", "apr > 100", "apr < 0"],
        "compound-interest-calculator.html": ["years <= 0", "rate > 100", "rate < 0"],
    }
    for g in guards.get(name, []):
        if g in js_code:
            ok("%s: 守卫 %s 存在" % (name, g))
        else:
            bad("%s: 守卫 %s 缺失" % (name, g))

print("\n=== 4. 每个 ID 唯一性 ===")
for t in TOOLS + ["index.html"]:
    h = read(t)
    name = t
    ids = re.findall(r'id="([^"]+)"', h)
    dup = [i for i in set(ids) if ids.count(i) > 1]
    if not dup:
        ok("%s: ids unique" % name)
    else:
        bad("%s: duplicate ids" % name, str(dup))

print("\n=== 5. Schema.org 引用完整性 ===")
for t in TOOLS:
    h = read(t)
    name = t.split("/")[-1]
    if h.count('application/ld+json') >= 1:
        ok("%s: has JSON-LD" % name)
    else:
        bad("%s: no JSON-LD" % name)

print("\n===== 复审结果: %d PASS / %d FAIL =====" % (PASS, FAIL))
print("复审结果: %s" % ("通过" if FAIL == 0 else "存在失败"))
sys.exit(0 if FAIL == 0 else 1)
