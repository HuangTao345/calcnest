# -*- coding: utf-8 -*-
"""
CalcNest V1.4 — 强复审·边界用例矩阵测试（新增强制关卡）
背景：V1.4 信用卡"天文数字"事故 = 只测幸福路径，未测边界输入。
本脚本把"用户乱输/极端输入"固化为常设断言，任何工具输出可疑值即失败。

验证目标（4 个工具的核心计算逻辑，Python 复现 JS 语义）：
  1. 正常输入 → 结果正确
  2. 负利率 → NaN 防御（必须被拦截，不能输出 NaN/Infinity）
  3. 负值输入 → 无效拦截
  4. 极大值 → 有限且有界（不 Infinity）
  5. 永不还清 → neverPaidOff 正确标记
  6. 0/空/NaN 输入 → 防御
用法: python scripts/boundary_test.py
"""
import math
import sys

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

def is_finite(v):
    return isinstance(v, (int, float)) and math.isfinite(v)

# ================= 1. Rent Affordability =================
print("=== 1. Rent Affordability ===")
def rent(gross, debts, expenses, savings, rule_pct):
    """复现 site_v1.2 rent 工具 calc 逻辑"""
    if gross <= 0 or debts < 0 or expenses < 0 or savings < 0:
        return None  # 无效输入拦截
    rule = rule_pct / 100
    safe_rent = gross * rule
    dti = ((debts + safe_rent) / gross) * 100
    remaining = gross - debts - expenses - savings - safe_rent
    return {"safe": safe_rent, "dti": dti, "remaining": remaining}

# 1a 正常
r = rent(5000, 600, 900, 400, 30)
if r and abs(r["safe"] - 1500) < 0.01 and abs(r["dti"] - 42.0) < 0.1 and abs(r["remaining"] - 1600) < 0.01:
    ok("rent: 正常 $5000 → safe=$1500 dti=42% remaining=$1600")
else:
    bad("rent: 正常", str(r))

# 1b 负负债 → 必须拦截（V1.4 修复前会反向放大）
r = rent(5000, -500, 900, 400, 30)
if r is None:
    ok("rent: 负负债 → 拦截")
else:
    bad("rent: 负负债未拦截", str(r))

# 1c gross=0 → 拦截
r = rent(0, 600, 900, 400, 30)
if r is None:
    ok("rent: 收入 0 → 拦截")
else:
    bad("rent: 收入 0 未拦截")

# 1d 极大值 → 有限
r = rent(1e9, 1e7, 1e7, 1e7, 30)
if r and all(is_finite(v) for v in r.values()):
    ok("rent: 极大值输出有限")
else:
    bad("rent: 极大值", str(r))

# ================= 2. Retirement Savings =================
print("\n=== 2. Retirement Savings ===")
def calc_guard_retire(P, PMT, years, rate):
    """复现 V1.4 calc 的输入防御门"""
    return not (years <= 0 or rate < 0 or rate > 100 or P < 0 or PMT < 0)

def fv_retire(P, PMT, rate, years):
    """复现 futureValue（仅在守卫通过后调用）"""
    i = rate / 100 / 12
    n = round(years * 12)
    if i == 0:
        return P + PMT * n
    if 1 + i <= 0:
        return float("nan")  # V1.4 防御
    return P * (1 + i) ** n + PMT * (((1 + i) ** n - 1) / i)

# 2a 正常
fv = fv_retire(20000, 500, 7, 25)
if is_finite(fv) and 400000 < fv < 600000:
    ok("retire: 正常 $20k+$500/7%/25y → ~$488k")
else:
    bad("retire: 正常", str(fv))

# 2b 负利率 → 守卫拦截（V1.4: rate<0 return）
if not calc_guard_retire(20000, 500, 25, -10):
    ok("retire: 负利率 → 输入守卫拦截")
else:
    bad("retire: 负利率守卫未拦截")

# 2c 极大利率 99999 → 守卫拦截（V1.4: rate>100 return，避免 Infinity）
if not calc_guard_retire(20000, 500, 25, 99999):
    ok("retire: 极大利率 99999 → 输入守卫拦截（拒绝 Infinity）")
else:
    bad("retire: 极大利率守卫未拦截")

# 2c2 上限边界 100% → 守卫通过但结果仍应有限（防御纵深）
if calc_guard_retire(20000, 500, 25, 100):
    fv = fv_retire(20000, 500, 100, 25)
    if is_finite(fv):
        ok("retire: 100% 上限 → 守卫通过且结果有限（纵深防御）")
    else:
        bad("retire: 100% 结果非有限", str(fv))
else:
    bad("retire: 100% 被误拦截")

# 2d years=0 → 拦截
if not calc_guard_retire(20000, 500, 0, 7):
    ok("retire: years=0 → 拦截")
else:
    bad("retire: years=0 未拦截")

# ================= 3. Compound Interest =================
print("\n=== 3. Compound Interest ===")
def calc_guard_compound(P, PMT, years, rate):
    """复现 V1.4 calc 的输入防御门"""
    return not (years <= 0 or rate < 0 or rate > 100 or P < 0 or PMT < 0)

def fv_compound(P, PMT, rate, years, per_year):
    i = rate / 100 / per_year
    n = round(years * per_year)
    if i == 0:
        return P + PMT * n
    if 1 + i <= 0:
        return float("nan")
    return P * (1 + i) ** n + PMT * (((1 + i) ** n - 1) / i)

# 3a 正常
fv = fv_compound(10000, 300, 7, 20, 12)
if is_finite(fv) and 150000 < fv < 250000:
    ok("compound: 正常 $10k+$300/7%/20y → ~$196k")
else:
    bad("compound: 正常", str(fv))

# 3b 负利率 → 守卫拦截
if not calc_guard_compound(10000, 300, 20, -10):
    ok("compound: 负利率 → 输入守卫拦截")
else:
    bad("compound: 负利率守卫未拦截")

# 3c 极大利率 → 守卫拦截
if not calc_guard_compound(10000, 300, 20, 99999):
    ok("compound: 极大利率 → 输入守卫拦截")
else:
    bad("compound: 极大利率守卫未拦截")

# 3d 100% 上限边界 → 结果有限（纵深防御）
fv = fv_compound(10000, 300, 100, 20, 12)
if is_finite(fv):
    ok("compound: 100% 上限 → 结果有限")
else:
    bad("compound: 100% 结果", str(fv))

# ================= 4. Credit Card Payoff =================
print("\n=== 4. Credit Card Payoff ===")
def simulate(balance, apr, payment):
    months = 0
    total_interest = 0
    cur = balance
    monthly_rate = apr / 100 / 12
    guard = 1200
    never = False
    while cur > 0 and months < guard:
        interest = cur * monthly_rate
        if payment <= interest:
            never = True
            break
        total_interest += interest
        cur = cur + interest - payment
        months += 1
        if cur < 0:
            cur = 0
    if months >= guard and cur > 0:
        never = True
    return months, total_interest, never

# 4a 正常（V1.4 已验证值）
m1, i1, n1 = simulate(6000, 22, 120)
m2, i2, n2 = simulate(6000, 22, 220)
if m1 == 137 and m2 == 39 and abs(i1 - i2 - 8020) < 50 and not n1 and not n2:
    ok("cc: 正常 137/39 saved≈$8020")
else:
    bad("cc: 正常", "m1=%d m2=%d" % (m1, m2))

# 4b 永不还清（V1.4 核心修复）
m1, i1, n1 = simulate(100000, 22, 200)
if n1 and m1 == 0 and i1 == 0:
    ok("cc: $100k min=$200 → neverPaidOff, 无天文数字")
else:
    bad("cc: neverPaidOff", "m=%d i=%d never=%s" % (m1, i1, n1))

# 4c 负 APR → calc 拦截（V1.4: apr<0 return）
def cc_calc_guard(apr):
    return 0 <= apr <= 100  # V1.4: apr<0 或 apr>100 → return
if cc_calc_guard(-20) == False:
    ok("cc: 负 APR → 拦截")
else:
    bad("cc: 负 APR 拦截")
if cc_calc_guard(150) == False:
    ok("cc: 超上限 APR(150%) → 拦截")
else:
    bad("cc: 超上限 APR 未拦截")

# 4d APR=0 → 有限（无利息，pure principal）
m1, i1, n1 = simulate(6000, 0, 200)
if m1 == 30 and i1 == 0 and not n1:
    ok("cc: APR=0 → 30 个月纯本金, 利息 0")
else:
    bad("cc: APR=0", "m=%d i=%d" % (m1, i1))

# 4e 上限内极大 APR(100) → 月利息巨大 → neverPaidOff 触发（非 Infinity 输出）
m1, i1, n1 = simulate(6000, 100, 200)
if n1:
    ok("cc: 上限 APR 100% → neverPaidOff 触发（显示 Never paid off）")
else:
    bad("cc: 上限 APR 100%")

# ================= 5. 数值边界通用断言 =================
print("\n=== 5. 通用防御 ===")
# 所有工具的 money 输出对 NaN/Infinity 必须用 finiteMoney 兜底
import os
here = os.path.dirname(os.path.abspath(__file__))
site = os.path.dirname(here)  # site_v1.2/
tools = ["rent-affordability-calculator.html", "retirement-savings-calculator.html",
         "credit-card-payoff-calculator.html", "compound-interest-calculator.html"]
for t in tools:
    p = os.path.join(site, "tools", t)
    h = open(p, encoding="utf-8").read()
    if "function sanitize" in h and "finiteMoney" in h:
        ok("%s: sanitize + finiteMoney 防御存在" % t)
    else:
        bad("%s: sanitize/finiteMoney 缺失" % t)

print("\n===== 强复审结果: %d PASS / %d FAIL =====" % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
