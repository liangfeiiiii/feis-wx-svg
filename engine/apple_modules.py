#!/usr/bin/env python3
"""feis-wx-svg · 苹果发布会极简风公众号 SVG 模块引擎（B 路线：正文 + 动效模块）

仅依赖 Python 3 标准库，零外部依赖。
严格遵守微信公众号原生 SVG 安全白名单：无 id、无 fill-opacity 动画、无滤镜、无渐变、无 mask/clipPath、无 JS。

用法：
  python3 engine/apple_modules.py <pack_spec.json> [-o <输出目录>]
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

W = 750
FONT_STACK = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif'
MONO_STACK = '"SF Mono", ui-monospace, Menlo, Monaco, Consolas, monospace'
EASE = 'calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1"'

THEMES = {
    "apple-light": {
        "bg": "#F5F5F7",
        "card": "#FFFFFF",
        "card_alt": "#EFEFF2",
        "border": "#E5E5EA",
        "text": "#1D1D1F",
        "sub": "#6E6E73",
        "muted": "#86868B",
        "accent": "#0071E3",
        "accent_soft": "#E8F2FC",
        "accent_text": "#FFFFFF",
        "danger": "#C93B2B",
        "danger_soft": "#FBECEB",
        "ok": "#1F8A4C",
        "ok_soft": "#E9F6EE",
        "dark_card": "#1D1D1F",
        "dark_text": "#F5F5F7",
        "dark_sub": "#A1A1A6",
    },
    "apple-dark": {
        "bg": "#0A0A0C",
        "card": "#161618",
        "card_alt": "#1F1F23",
        "border": "#2C2C30",
        "text": "#F5F5F7",
        "sub": "#A1A1A6",
        "muted": "#6E6E73",
        "accent": "#2997FF",
        "accent_soft": "#132940",
        "accent_text": "#FFFFFF",
        "danger": "#FF6961",
        "danger_soft": "#2F1919",
        "ok": "#30D158",
        "ok_soft": "#142B1C",
        "dark_card": "#242428",
        "dark_text": "#FFFFFF",
        "dark_sub": "#B0B0B8",
    },
}


def n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def fade_up(begin, dur=0.55, dy=16):
    return (
        f'<animate attributeName="opacity" values="0;1" begin="{n(begin)}s" dur="{n(dur)}s" fill="freeze" {EASE}/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 {n(dy)};0 0" '
        f'begin="{n(begin)}s" dur="{n(dur)}s" fill="freeze" {EASE}/>'
    )


def fade_in(begin, dur=0.45):
    return f'<animate attributeName="opacity" values="0;1" begin="{n(begin)}s" dur="{n(dur)}s" fill="freeze" {EASE}/>'


def draw_line(x1, y1, x2, y2, stroke, width, begin, dur=0.6, opacity=1.0):
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return (
        f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" '
        f'stroke="{stroke}" stroke-width="{n(width)}" stroke-linecap="round" '
        f'stroke-dasharray="{n(length)}" stroke-dashoffset="{n(length)}" opacity="{n(opacity)}">'
        f'<animate attributeName="stroke-dashoffset" values="{n(length)};0" '
        f'begin="{n(begin)}s" dur="{n(dur)}s" fill="freeze" {EASE}/>'
        f'</line>'
    )


def wrap_lines(text, max_units):
    """按全角=2、半角=1 的宽度估算法自然断行，避免超出卡片边界。"""
    if not text:
        return []
    lines, cur, w = [], "", 0.0
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur, w = "", 0.0
            continue
        cw = 2.0 if ord(ch) > 0x2E7F else 1.15
        if w + cw > max_units and cur:
            lines.append(cur)
            cur, w = ch, cw
        else:
            cur += ch
            w += cw
    if cur:
        lines.append(cur)
    return lines


def get_theme(spec_theme, mod):
    base = dict(THEMES.get(mod.get("theme") or spec_theme or "apple-light", THEMES["apple-light"]))
    if mod.get("accent"):
        base["accent"] = mod["accent"]
    return base


def wrap_section(svg_body, height, bg):
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {n(height)}" width="100%" '
        f'style="display:block;width:100%;height:auto;border-radius:16px;background-color:{bg};">'
        f'<rect x="0" y="0" width="{W}" height="{n(height)}" rx="28" fill="{bg}"/>'
        f'{svg_body}</svg>'
    )
    return (
        f'<section style="margin:24px 0;padding:0;line-height:0;font-size:0;'
        f'border-radius:16px;overflow:hidden;background-color:{bg};">'
        f'{svg}</section>'
    )


# ---------- 1. hero-metric ----------

def render_hero_metric(mod, th):
    kicker = escape(mod.get("kicker", ""))
    metric = escape(str(mod.get("metric", "")))
    unit = escape(mod.get("unit", ""))
    title = escape(mod.get("title", ""))
    subtitle = mod.get("subtitle", "")
    sub_lines = wrap_lines(subtitle, 46)[:2]

    h = 370 + (len(sub_lines) - 1) * 32
    els = []

    # 右侧极简秩序同心弧线（克制装饰，无 id 无滤镜）
    els.append(
        f'<g opacity="0">'
        f'<circle cx="640" cy="128" r="118" fill="none" stroke="{th["border"]}" stroke-width="1.5"/>'
        f'<circle cx="640" cy="128" r="76" fill="none" stroke="{th["accent"]}" stroke-width="1.5" opacity="0.28"/>'
        f'<circle cx="640" cy="128" r="6" fill="{th["accent"]}"/>'
        f'{fade_in(0.35, 0.7)}</g>'
    )

    # Kicker
    if kicker:
        els.append(
            f'<g opacity="0"><text x="52" y="72" font-size="22" font-weight="600" letter-spacing="1.8" '
            f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>{fade_up(0.08, 0.45, 10)}</g>'
        )

    # 超大核心数字/关键词
    metric_size = 112 if len(metric) <= 4 else (88 if len(metric) <= 7 else 68)
    metric_w = sum(metric_size * (0.95 if ord(c) > 0x2E7F else 0.62) for c in mod.get("metric", ""))
    els.append(
        f'<g opacity="0">'
        f'<text x="48" y="198" font-size="{metric_size}" font-weight="700" letter-spacing="-2" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{metric}</text>'
        + (
            f'<text x="{n(56 + metric_w)}" y="194" font-size="30" font-weight="600" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{unit}</text>'
            if unit else ""
        )
        + f'{fade_up(0.22, 0.6, 20)}</g>'
    )

    # 展开细线
    els.append(draw_line(52, 232, 698, 232, th["border"], 1.5, 0.48, 0.65))
    els.append(draw_line(52, 232, 132, 232, th["accent"], 2.5, 0.52, 0.55))

    # 标题与副标题
    els.append(
        f'<g opacity="0"><text x="52" y="286" font-size="32" font-weight="700" letter-spacing="-0.5" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>{fade_up(0.62, 0.5, 12)}</g>'
    )
    for i, line in enumerate(sub_lines):
        els.append(
            f'<g opacity="0"><text x="52" y="{n(330 + i * 34)}" font-size="23" font-weight="400" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{escape(line)}</text>{fade_up(0.76 + i * 0.1, 0.5, 10)}</g>'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 2. compare-split ----------

def render_compare_split(mod, th):
    kicker = escape(mod.get("kicker", ""))
    title = escape(mod.get("title", ""))
    left = mod.get("left", {})
    right = mod.get("right", {})
    l_items = left.get("items", [])[:5]
    r_items = right.get("items", [])[:5]
    rows = max(len(l_items), len(r_items), 3)

    card_y = 148
    row_h = 56
    card_h = 92 + rows * row_h
    h = card_y + card_h + 44
    els = []

    if kicker:
        els.append(
            f'<g opacity="0"><text x="48" y="64" font-size="21" font-weight="600" letter-spacing="1.6" '
            f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>{fade_up(0.05, 0.45, 10)}</g>'
        )
    els.append(
        f'<g opacity="0"><text x="48" y="114" font-size="36" font-weight="700" letter-spacing="-0.8" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>{fade_up(0.14, 0.5, 14)}</g>'
    )

    # 左卡：弱化对比
    lx, lw = 48, 316
    els.append(
        f'<g opacity="0">'
        f'<rect x="{lx}" y="{card_y}" width="{lw}" height="{card_h}" rx="22" '
        f'fill="{th["card_alt"]}" stroke="{th["border"]}" stroke-width="1"/>'
        f'<rect x="{lx + 24}" y="{card_y + 24}" width="12" height="12" rx="6" fill="{th["danger"]}" opacity="0.75"/>'
        f'<text x="{lx + 46}" y="{card_y + 37}" font-size="22" font-weight="700" '
        f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{escape(left.get("tag", "旧方式"))}</text>'
        f'{fade_up(0.32, 0.55, 16)}</g>'
    )
    els.append(draw_line(lx + 24, card_y + 60, lx + lw - 24, card_y + 60, th["border"], 1, 0.48, 0.45))

    for i, item in enumerate(l_items):
        iy = card_y + 104 + i * row_h
        t = 0.55 + i * 0.14
        els.append(
            f'<g opacity="0">'
            f'<line x1="{lx + 26}" y1="{iy - 8}" x2="{lx + 40}" y2="{iy - 8}" '
            f'stroke="{th["danger"]}" stroke-width="2.2" stroke-linecap="round" opacity="0.7"/>'
            f'<text x="{lx + 54}" y="{iy}" font-size="23" font-weight="500" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{escape(item)}</text>'
            f'{fade_up(t, 0.45, 10)}</g>'
        )

    # 右卡：高亮聚焦
    rx, rw = 386, 316
    els.append(
        f'<g opacity="0">'
        f'<rect x="{rx}" y="{card_y}" width="{rw}" height="{card_h}" rx="22" '
        f'fill="{th["dark_card"]}"/>'
        f'<rect x="{rx + 24}" y="{card_y + 24}" width="12" height="12" rx="6" fill="{th["ok"]}"/>'
        f'<text x="{rx + 46}" y="{card_y + 37}" font-size="22" font-weight="700" '
        f'fill="{th["dark_text"]}" font-family=\'{FONT_STACK}\'>{escape(right.get("tag", "新方式"))}</text>'
        f'{fade_up(0.46, 0.55, 18)}</g>'
    )
    els.append(draw_line(rx + 24, card_y + 60, rx + rw - 24, card_y + 60, "#3A3A3F", 1, 0.62, 0.45))

    for i, item in enumerate(r_items):
        iy = card_y + 104 + i * row_h
        t = 0.72 + i * 0.14
        # 精细对勾路径
        check = (
            f'<path d="M{rx + 26} {iy - 8} L{rx + 32} {iy - 2} L{rx + 43} {iy - 14}" '
            f'fill="none" stroke="{th["ok"]}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" '
            f'stroke-dasharray="28" stroke-dashoffset="28">'
            f'<animate attributeName="stroke-dashoffset" values="28;0" begin="{n(t + 0.1)}s" dur="0.35s" fill="freeze" {EASE}/>'
            f'</path>'
        )
        els.append(
            f'<g opacity="0">'
            f'<text x="{rx + 56}" y="{iy}" font-size="23" font-weight="600" '
            f'fill="{th["dark_text"]}" font-family=\'{FONT_STACK}\'>{escape(item)}</text>'
            f'{fade_up(t, 0.45, 10)}</g>{check}'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 3. flow-strip ----------

def render_flow_strip(mod, th):
    kicker = escape(mod.get("kicker", ""))
    title = escape(mod.get("title", ""))
    steps = mod.get("steps", [])[:4]
    footnote = escape(mod.get("footnote", ""))
    cnt = max(len(steps), 1)

    start_y = 152
    step_h = 112
    gap = 18
    h = start_y + cnt * step_h + (cnt - 1) * gap + (72 if footnote else 42)
    els = []

    if kicker:
        els.append(
            f'<g opacity="0"><text x="48" y="64" font-size="21" font-weight="600" letter-spacing="1.6" '
            f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>{fade_up(0.05, 0.45, 10)}</g>'
        )
    els.append(
        f'<g opacity="0"><text x="48" y="114" font-size="36" font-weight="700" letter-spacing="-0.8" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>{fade_up(0.14, 0.5, 14)}</g>'
    )

    # 左侧纵向轨道线
    rail_x = 84
    if cnt > 1:
        y_top = start_y + 56
        y_bot = start_y + (cnt - 1) * (step_h + gap) + 56
        els.append(draw_line(rail_x, y_top, rail_x, y_bot, th["border"], 2, 0.35, 0.85))
        # 光点顺轨道流转
        els.append(
            f'<circle cx="{rail_x}" cy="{y_top}" r="5" fill="{th["accent"]}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0.9" keyTimes="0;0.1;0.9;1" begin="0.45s" dur="1.8s" fill="freeze"/>'
            f'<animate attributeName="cy" values="{y_top};{y_bot}" begin="0.45s" dur="1.6s" fill="freeze" {EASE}/>'
            f'</circle>'
        )

    for i, st in enumerate(steps):
        sy = start_y + i * (step_h + gap)
        t = 0.28 + i * 0.28
        num = escape(str(st.get("num", f"0{i + 1}")))
        st_title = escape(st.get("title", ""))
        st_desc = escape(st.get("desc", ""))
        is_last = (i == cnt - 1)
        badge_bg = th["accent"] if is_last else th["card"]
        badge_fg = th["accent_text"] if is_last else th["text"]
        badge_stroke = th["accent"] if is_last else th["border"]

        els.append(
            f'<g opacity="0">'
            f'<rect x="132" y="{sy}" width="570" height="{step_h}" rx="20" '
            f'fill="{th["card"]}" stroke="{th["border"]}" stroke-width="1"/>'
            f'<text x="160" y="{sy + 48}" font-size="26" font-weight="700" '
            f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{st_title}</text>'
            f'<text x="160" y="{sy + 82}" font-size="21" font-weight="400" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{st_desc}</text>'
            f'<circle cx="{rail_x}" cy="{sy + 56}" r="24" fill="{badge_bg}" stroke="{badge_stroke}" stroke-width="1.5"/>'
            f'<text x="{rail_x}" y="{sy + 63}" text-anchor="middle" font-size="18" font-weight="700" '
            f'fill="{badge_fg}" font-family=\'{MONO_STACK}\'>{num}</text>'
            f'{fade_up(t, 0.55, 16)}</g>'
        )

    if footnote:
        els.append(
            f'<g opacity="0"><text x="48" y="{h - 24}" font-size="20" font-weight="500" '
            f'fill="{th["muted"]}" font-family=\'{FONT_STACK}\'>{footnote}</text>'
            f'{fade_in(0.4 + cnt * 0.28, 0.5)}</g>'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 4. bento-grid ----------

def render_bento_grid(mod, th):
    kicker = escape(mod.get("kicker", ""))
    title = escape(mod.get("title", ""))
    cards = mod.get("cards", [])[:4]
    n_cards = len(cards)

    start_y = 148
    gap = 18
    full_w = 654
    half_w = (full_w - gap) // 2
    card_h = 204
    els = []

    if kicker:
        els.append(
            f'<g opacity="0"><text x="48" y="64" font-size="21" font-weight="600" letter-spacing="1.6" '
            f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>{fade_up(0.05, 0.45, 10)}</g>'
        )
    els.append(
        f'<g opacity="0"><text x="48" y="114" font-size="36" font-weight="700" letter-spacing="-0.8" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>{fade_up(0.14, 0.5, 14)}</g>'
    )

    # 布局坐标：3 张卡用 1(通栏) + 2(并排)；4 张卡用 2x2；2 张卡用 2 并排
    boxes = []
    if n_cards == 3:
        boxes = [
            (48, start_y, full_w, 188),
            (48, start_y + 188 + gap, half_w, card_h),
            (48 + half_w + gap, start_y + 188 + gap, half_w, card_h),
        ]
        h = start_y + 188 + gap + card_h + 44
    elif n_cards == 4:
        boxes = [
            (48, start_y, half_w, card_h),
            (48 + half_w + gap, start_y, half_w, card_h),
            (48, start_y + card_h + gap, half_w, card_h),
            (48 + half_w + gap, start_y + card_h + gap, half_w, card_h),
        ]
        h = start_y + card_h * 2 + gap + 44
    else:
        for i in range(n_cards):
            boxes.append((48 + i * (half_w + gap), start_y, half_w if n_cards > 1 else full_w, card_h))
        h = start_y + card_h + 44

    for i, (c, (bx, by, bw, bh)) in enumerate(zip(cards, boxes)):
        t = 0.28 + i * 0.16
        is_dark = bool(c.get("highlight"))
        bg = th["dark_card"] if is_dark else th["card"]
        fg = th["dark_text"] if is_dark else th["text"]
        sub_fg = th["dark_sub"] if is_dark else th["sub"]
        lbl_fg = th["accent"] if not is_dark else th["accent"]
        stroke = "none" if is_dark else th["border"]

        label = escape(c.get("label", ""))
        val = escape(str(c.get("value", "")))
        desc_lines = wrap_lines(c.get("desc", ""), 38 if bw > 400 else 20)[:2]
        val_size = 40 if len(val) <= 6 else (32 if len(val) <= 10 else 26)

        els.append(
            f'<g opacity="0">'
            f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="24" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="1"/>'
            f'<text x="{bx + 28}" y="{by + 44}" font-size="19" font-weight="600" letter-spacing="1" '
            f'fill="{lbl_fg}" font-family=\'{FONT_STACK}\'>{label}</text>'
            f'<text x="{bx + 28}" y="{by + 104}" font-size="{val_size}" font-weight="700" letter-spacing="-0.8" '
            f'fill="{fg}" font-family=\'{FONT_STACK}\'>{val}</text>'
            + "".join(
                f'<text x="{bx + 28}" y="{by + 144 + j * 28}" font-size="20" font-weight="400" '
                f'fill="{sub_fg}" font-family=\'{FONT_STACK}\'>{escape(dl)}</text>'
                for j, dl in enumerate(desc_lines)
            )
            + f'{fade_up(t, 0.55, 16)}</g>'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 5. quote-seal ----------

def render_quote_seal(mod, th):
    kicker = escape(mod.get("kicker", ""))
    quote_lines = wrap_lines(mod.get("quote", ""), 26)[:3]
    subquote = escape(mod.get("subquote", ""))
    author = escape(mod.get("author", ""))

    h = 240 + len(quote_lines) * 48 + (42 if subquote else 0)
    els = []

    # 居中克制短横线从中心展开
    els.append(draw_line(345, 58, 405, 58, th["accent"], 3, 0.1, 0.5))

    if kicker:
        els.append(
            f'<g opacity="0"><text x="375" y="102" text-anchor="middle" font-size="20" font-weight="600" '
            f'letter-spacing="2" fill="{th["muted"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>'
            f'{fade_in(0.22, 0.45)}</g>'
        )

    qy = 158 if kicker else 136
    for i, line in enumerate(quote_lines):
        els.append(
            f'<g opacity="0"><text x="375" y="{qy + i * 50}" text-anchor="middle" font-size="36" font-weight="700" '
            f'letter-spacing="-0.5" fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{escape(line)}</text>'
            f'{fade_up(0.32 + i * 0.16, 0.55, 14)}</g>'
        )

    cur_y = qy + len(quote_lines) * 50 + 10
    if subquote:
        els.append(
            f'<g opacity="0"><text x="375" y="{cur_y}" text-anchor="middle" font-size="22" font-weight="400" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{subquote}</text>'
            f'{fade_in(0.65, 0.5)}</g>'
        )
        cur_y += 42

    if author:
        els.append(
            f'<g opacity="0"><text x="375" y="{cur_y + 12}" text-anchor="middle" font-size="19" font-weight="600" '
            f'letter-spacing="1.2" fill="{th["muted"]}" font-family=\'{FONT_STACK}\'>{author}</text>'
            f'{fade_in(0.8, 0.5)}</g>'
        )

    return wrap_section("".join(els), h, th["bg"])


RENDERERS = {
    "hero-metric": render_hero_metric,
    "compare-split": render_compare_split,
    "flow-strip": render_flow_strip,
    "bento-grid": render_bento_grid,
    "quote-seal": render_quote_seal,
}


# ---------- 微信规则静态体检 ----------

FORBIDDEN_PATTERNS = [
    ("id属性", re.compile(r'\bid\s*=', re.I)),
    ("fill-opacity动画", re.compile(r'attributeName\s*=\s*["\']fill-opacity["\']', re.I)),
    ("xlink:href", re.compile(r'\bxlink:href\b', re.I)),
    ("filter滤镜", re.compile(r'<filter\b', re.I)),
    ("渐变标签", re.compile(r'<(linearGradient|radialGradient)\b', re.I)),
    ("mask/clipPath", re.compile(r'<(mask|clipPath)\b', re.I)),
    ("style标签", re.compile(r'<style\b', re.I)),
    ("script脚本", re.compile(r'<script\b', re.I)),
]


def lint_wechat_svg(html):
    issues = [name for name, pat in FORBIDDEN_PATTERNS if pat.search(html)]
    size_bytes = len(html.encode("utf-8"))
    if size_bytes > 1000 * 1024:
        issues.append(f"体积过大({size_bytes // 1024}KB)")
    return {"ok": len(issues) == 0, "issues": issues, "bytes": size_bytes}


def slugify(text, fallback):
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text).strip("-")
    return s[:28] or fallback


PREVIEW_TPL = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 非叔 SVG 预览</title>
<style>
  :root {{
    --bg: #F5F5F7; --surface: #FFFFFF; --text: #1D1D1F; --sub: #6E6E73;
    --border: rgba(0,0,0,0.08); --accent: #0071E3;
  }}
  [data-mode="dark"] {{
    --bg: #000000; --surface: #161618; --text: #F5F5F7; --sub: #A1A1A6;
    --border: rgba(255,255,255,0.12); --accent: #2997FF;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", sans-serif;
    transition: background-color 240ms cubic-bezier(0.22,1,0.36,1), color 240ms cubic-bezier(0.22,1,0.36,1);
    -webkit-font-smoothing: antialiased;
  }}
  .bar {{
    position: sticky; top: 0; z-index: 10; backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    background: color-mix(in srgb, var(--surface) 82%, transparent);
    border-bottom: 1px solid var(--border);
    padding: 12px 20px; display: flex; align-items: center; justify-content: center; gap: 10px;
  }}
  .btn {{
    border: 1px solid var(--border); background: var(--surface); color: var(--text);
    padding: 7px 14px; border-radius: 999px; font-size: 13px; font-weight: 500; cursor: pointer;
    transition: transform 120ms ease, background-color 180ms ease;
  }}
  .btn:active {{ transform: scale(0.96); }}
  .btn.primary {{ background: var(--accent); color: #fff; border-color: transparent; }}
  .phone {{
    width: 410px; max-width: calc(100% - 24px); margin: 28px auto 64px;
    background: var(--surface); border-radius: 28px; padding: 28px 20px 40px;
    border: 1px solid var(--border); box-shadow: 0 20px 60px rgba(0,0,0,0.08);
    transition: background-color 240ms cubic-bezier(0.22,1,0.36,1);
  }}
  .phone h1 {{ font-size: 22px; line-height: 1.35; margin: 0 0 8px; letter-spacing: -0.4px; }}
  .meta {{ font-size: 13px; color: var(--sub); margin-bottom: 24px; }}
  .mod-wrap {{ position: relative; margin-bottom: 24px; }}
  .mod-head {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 8px; font-size: 12px; color: var(--sub);
  }}
  .copy-mini {{
    border: 1px solid var(--border); background: transparent; color: var(--text);
    border-radius: 999px; padding: 4px 10px; font-size: 12px; cursor: pointer;
  }}
  .copy-mini:active {{ transform: scale(0.96); }}
  .toast {{
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(16px);
    background: #1D1D1F; color: #F5F5F7; padding: 10px 18px; border-radius: 999px;
    font-size: 13px; opacity: 0; pointer-events: none;
    transition: opacity 200ms ease, transform 220ms cubic-bezier(0.22,1,0.36,1);
  }}
  .toast.show {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
</style>
</head>
<body>
<div class="bar">
  <button class="btn primary" onclick="replayAll()">重播全部动效</button>
  <button class="btn" onclick="toggleMode()">切换深浅底</button>
</div>
<div class="phone">
  <h1>{title}</h1>
  <div class="meta">非叔 SVG 模块预览 · 可将同目录 feis-pack.json 直接拖入 Chrome 插件</div>
  <div id="stage"></div>
</div>
<div class="toast" id="toast"></div>
<script>
const PACK = {pack_json};
function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(window._tt); window._tt = setTimeout(() => t.classList.remove('show'), 1800);
}}
function renderAll() {{
  const stage = document.getElementById('stage');
  stage.innerHTML = '';
  PACK.modules.forEach((m, idx) => {{
    const wrap = document.createElement('div');
    wrap.className = 'mod-wrap';
    wrap.innerHTML = `<div class="mod-head"><span>模块 ${{idx + 1}} · ${{m.name}} · ${{(m.bytes/1024).toFixed(1)}}KB</span>
      <button class="copy-mini" data-idx="${{idx}}">复制模块</button></div><div class="slot">${{m.html}}</div>`;
    wrap.querySelector('.copy-mini').onclick = async () => {{
      try {{
        await navigator.clipboard.write([new ClipboardItem({{
          'text/html': new Blob([m.html], {{type: 'text/html'}}),
          'text/plain': new Blob([m.html], {{type: 'text/plain'}})
        }})]);
        showToast('已复制「' + m.name + '」，去公众号粘贴');
      }} catch (e) {{
        showToast('本地文件受限，请直接把 feis-pack.json 拖进 Chrome 插件');
      }}
    }};
    stage.appendChild(wrap);
  }});
}}
function replayAll() {{
  document.getElementById('stage').innerHTML = '';
  requestAnimationFrame(renderAll);
}}
function toggleMode() {{
  document.documentElement.dataset.mode = document.documentElement.dataset.mode === 'dark' ? 'light' : 'dark';
}}
renderAll();
</script>
</body>
</html>
"""


def build_pack(spec, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    title = spec.get("title", "未命名文章")
    default_theme = spec.get("theme", "apple-light")
    mods_in = spec.get("modules") or sys.exit("配置里缺少 modules 数组")

    packed = []
    for idx, mod in enumerate(mods_in, 1):
        kind = mod.get("type")
        if kind not in RENDERERS:
            sys.exit(f"第 {idx} 个模块类型「{kind}」不支持，可选：{' / '.join(RENDERERS)}")
        th = get_theme(default_theme, mod)
        html = RENDERERS[kind](mod, th)
        lint = lint_wechat_svg(html)
        name = mod.get("name") or mod.get("title") or f"{kind}-{idx}"
        fname = f"{idx:02d}-{slugify(name, kind)}.html"
        (out / fname).write_text(html, encoding="utf-8")
        packed.append({
            "id": f"mod-{idx:02d}",
            "index": idx,
            "name": name,
            "type": kind,
            "theme": mod.get("theme") or default_theme,
            "file": fname,
            "bytes": lint["bytes"],
            "lint": lint,
            "html": html,
        })

    pack_obj = {
        "packVersion": 1,
        "generator": "feis-wx-svg",
        "title": title,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "modules": packed,
    }
    pack_text = json.dumps(pack_obj, ensure_ascii=False, indent=2)
    (out / "feis-pack.json").write_text(pack_text, encoding="utf-8")

    safe_json = pack_text.replace("</", "<\\/")
    (out / "preview.html").write_text(
        PREVIEW_TPL.format(title=escape(title), pack_json=safe_json),
        encoding="utf-8",
    )
    return pack_obj


def main():
    ap = argparse.ArgumentParser(description="feis-wx-svg · 苹果发布会极简风公众号 SVG 模块生成器")
    ap.add_argument("spec", help="模块配置 JSON 路径")
    ap.add_argument("-o", "--out", help="输出目录（默认：配置同级同名目录）")
    a = ap.parse_args()
    sp = Path(a.spec)
    spec = json.loads(sp.read_text(encoding="utf-8"))
    out = Path(a.out) if a.out else sp.parent / sp.stem
    pack = build_pack(spec, out)
    total_kb = sum(m["bytes"] for m in pack["modules"]) / 1024
    ok_all = all(m["lint"]["ok"] for m in pack["modules"])
    print(f"✅ 已生成 {len(pack['modules'])} 个苹果风 SVG 模块 → {out}/ (总计 {total_kb:.1f}KB · 微信合规={'通过' if ok_all else '有警告'})")
    for m in pack["modules"]:
        status = "OK" if m["lint"]["ok"] else ",".join(m["lint"]["issues"])
        print(f"   {m['file']}  [{m['type']}]  {m['bytes']/1024:.1f}KB  ({status})")


if __name__ == "__main__":
    main()
