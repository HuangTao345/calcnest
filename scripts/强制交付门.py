# -*- coding: utf-8 -*-
"""
CalcNest MVP V1.4 — 强制交付门 (FORCE GATES)
适用 Gate（MVP 无背景素材/音频检测需求，GATE-A/GATE-D 本期 N/A）：
  GATE-B: selftest.py 全 PASS
  GATE-C: html_review.py 全 PASS
  GATE-E: docs/v1.0_preview.png 存在（视觉预览已渲染）
  GATE-F: docs/大笔记_*.md 存在 + 根目录 STATUS.md 已更新
  GATE-G: 版本号 V1.4 全局一致
用法: python scripts/强制交付门.py
任一 FAIL -> 非 0 退出码 -> 拒绝交付
"""
import os
import re
import subprocess
import sys

# 强制 UTF-8 输出，兼容中文/emoji
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(ROOT)  # 垂直计算工具站/
WORKSPACE_ROOT = os.path.dirname(PROJECT_ROOT)  # 音乐理论与编程混合专家/
VERSION = "V1.4"

failures = []

def run_gate(name, cmd, cwd):
    print("\n========== GATE-%s: %s ==========" % (name[0], name))
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout[-3000:] if len(r.stdout) > 3000 else r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[-1500:])
    if r.returncode == 0:
        print("[GATE %s PASS] %s" % (name[0], name))
        return True
    print("[GATE %s FAIL] %s (exit %d)" % (name[0], name, r.returncode))
    return False

print("=" * 60)
print("强制交付门 | CalcNest MVP %s" % VERSION)
print("=" * 60)

# GATE-B: selftest
if not run_gate("GATE-B selftest.py", [sys.executable, "selftest.py"], os.path.join(ROOT, "scripts")):
    failures.append("GATE-B")

# GATE-B2 (强复审·边界用例): 用户乱输/极端输入必须被防御 (V1.4 新增, 事故沉淀)
if not run_gate("GATE-B2 boundary_test.py", [sys.executable, "boundary_test.py"], os.path.join(ROOT, "scripts")):
    failures.append("GATE-B2")

# GATE-C: html_review
if not run_gate("GATE-C html_review.py", [sys.executable, "html_review.py"], os.path.join(ROOT, "scripts")):
    failures.append("GATE-C")

# GATE-E: preview png exists
print("\n========== GATE-E: 视觉预览图 ==========")
preview = os.path.join(ROOT, "docs", VERSION.lower() + "_preview.png")
if os.path.isfile(preview) and os.path.getsize(preview) > 5000:
    print("[GATE E PASS] %s_preview.png 存在 (%d bytes)" % (VERSION.lower(), os.path.getsize(preview)))
else:
    print("[GATE E FAIL] %s_preview.png 缺失或过小" % VERSION.lower())
    failures.append("GATE-E")

# GATE-F: 大笔记 + STATUS
print("\n========== GATE-F: 大笔记 + STATUS ==========")
# 检查大笔记：site/docs/ 和 PROJECT_ROOT/docs/ 都行
notes_candidates = []
for notes_dir in [os.path.join(ROOT, "docs"), os.path.join(PROJECT_ROOT, "docs")]:
    if os.path.isdir(notes_dir):
        notes_candidates += [os.path.join(notes_dir, f) for f in os.listdir(notes_dir) if f.startswith("大笔记_") and f.endswith(".md")]
if notes_candidates:
    # 优先找含当前版本号的大笔记
    versioned = [n for n in notes_candidates if VERSION in os.path.basename(n)]
    chosen = versioned[0] if versioned else notes_candidates[0]
    print("[GATE F PASS] 大笔记: %s" % os.path.basename(chosen))
else:
    print("[GATE F FAIL] docs/ 下无 大笔记_*.md (检查了 site/docs/ 和 PROJECT_ROOT/docs/)")
    failures.append("GATE-F")
# STATUS.md：在 PROJECT_ROOT 或 WORKSPACE_ROOT 之一
status_path = None
for sp in [os.path.join(PROJECT_ROOT, "STATUS.md"), os.path.join(WORKSPACE_ROOT, "STATUS.md")]:
    if os.path.isfile(sp):
        status_path = sp; break
if status_path and VERSION in open(status_path, encoding="utf-8").read():
    print("[GATE F PASS] STATUS.md 已更新 (含 %s) @ %s" % (VERSION, os.path.relpath(status_path, WORKSPACE_ROOT)))
else:
    print("[GATE F FAIL] STATUS.md 未更新或未含 %s" % VERSION)
    failures.append("GATE-F")

# GATE-G: 版本号全局同步
print("\n========== GATE-G: 版本号同步 ==========")
v_issues = []
# css/js 注释
for asset in ["css/style.css", "js/main.js"]:
    content = open(os.path.join(ROOT, asset), encoding="utf-8").read()
    if VERSION not in content:
        v_issues.append(asset)
# README
readme = os.path.join(PROJECT_ROOT, "README.md")
if os.path.isfile(readme) and VERSION not in open(readme, encoding="utf-8").read():
    v_issues.append("README.md")
# 各 HTML title 品牌
for root_dir, _, files in os.walk(ROOT):
    for fn in files:
        if fn.endswith(".html"):
            p = os.path.join(root_dir, fn)
            content = open(p, encoding="utf-8").read()
            if "CalcNest" not in content:
                v_issues.append(os.path.relpath(p, ROOT))
if not v_issues:
    print("[GATE G PASS] 版本/品牌号全局一致")
else:
    print("[GATE G FAIL] 以下文件缺版本/品牌标识: %s" % ", ".join(v_issues[:10]))
    failures.append("GATE-G")

print("\n" + "=" * 60)
if failures:
    print("[GATE FAIL] 失败关卡: %s" % ", ".join(failures))
    print("禁止交付：必须先修复并重跑全部关卡")
    sys.exit(1)
else:
    print("[GATE PASS] 全部强制关卡通过，可以交付")
    sys.exit(0)
