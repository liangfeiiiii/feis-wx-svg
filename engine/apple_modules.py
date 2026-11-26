#!/usr/bin/env python3
"""feis-wx-svg · 苹果发布会极简风公众号 SVG 模块与整篇混排引擎

仅依赖 Python 3 标准库，零外部依赖。
严格遵守微信公众号原生 SVG 安全白名单：无 id、无 fill-opacity 动画、无滤镜、无渐变、无 mask/clipPath、无 <style>、无 JS。

支持 7 种高定组件：
  1. hero-metric    核心数据/关键词冲击卡
  2. compare-split  左右双栏高对比卡
  3. flow-strip     步骤链路与光点流转卡
  4. bento-grid     苹果经典 Bento 圆角网格卡
  5. quote-seal     极简留白金句落版卡
  6. swipe-gallery  横向左右滑动高定杂志画廊（微信原生横滑）
  7. click-reveal   点击揭晓互动卡片（微信原生 begin="click" 零 id 揭幕）

用法：
  python3 engine/apple_modules.py <modules.json> [-o <输出目录>]
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


CYCLE = 9.0  # 9 秒循环周期：前 2.2s 从 0→1 完整生长，中间 6s 清晰停留可读，末尾柔和重启


def _kt(cycle, *ts):
    return ";".join(f"{min(max(t / cycle, 0.0), 1.0):.4f}".rstrip("0").rstrip(".") or "0" for t in ts)


def loop_fade_up(t_in, dur=0.65, dy=18, cycle=CYCLE):
    """在 cycle 秒周期内：t_in 时从 0→1 轻盈上浮生长，停留至末尾柔和收束再循环。"""
    t0 = max(t_in, 0.02)
    t1 = min(t0 + dur, cycle - 1.2)
    t_hold = cycle - 0.85
    t_out = cycle - 0.28
    kt = _kt(cycle, 0, t0, t1, t_hold, t_out, cycle)
    ks = "0 0 1 1;0.22 1 0.36 1;0 0 1 1;0.4 0 0.2 1;0 0 1 1"
    return (
        f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" '
        f'dur="{n(cycle)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks}"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0 {n(dy)};0 {n(dy)};0 0;0 0;0 -6;0 {n(dy)}" keyTimes="{kt}" '
        f'dur="{n(cycle)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks}"/>'
    )


def loop_fade_in(t_in, dur=0.55, cycle=CYCLE):
    t0 = max(t_in, 0.02)
    t1 = min(t0 + dur, cycle - 1.2)
    t_hold = cycle - 0.85
    t_out = cycle - 0.28
    kt = _kt(cycle, 0, t0, t1, t_hold, t_out, cycle)
    ks = "0 0 1 1;0.22 1 0.36 1;0 0 1 1;0.4 0 0.2 1;0 0 1 1"
    return (
        f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt}" '
        f'dur="{n(cycle)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks}"/>'
    )


def loop_draw_line(x1, y1, x2, y2, stroke, width, t_in, dur=0.7, opacity=1.0, cycle=CYCLE):
    """线条在周期内从 0 长度一笔拉出，停留展示后柔和淡出再重画。"""
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    t0 = max(t_in, 0.02)
    t1 = min(t0 + dur, cycle - 1.2)
    t_hold = cycle - 0.85
    t_out = cycle - 0.28
    kt = _kt(cycle, 0, t0, t1, t_hold, t_out, cycle)
    ks = "0 0 1 1;0.22 1 0.36 1;0 0 1 1;0.4 0 0.2 1;0 0 1 1"
    L = n(length)
    op = n(opacity)
    return (
        f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" '
        f'stroke="{stroke}" stroke-width="{n(width)}" stroke-linecap="round" '
        f'stroke-dasharray="{L}" stroke-dashoffset="{L}">'
        f'<animate attributeName="stroke-dashoffset" values="{L};{L};0;0;0;{L}" keyTimes="{kt}" '
        f'dur="{n(cycle)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks}"/>'
        f'<animate attributeName="opacity" values="0;{op};{op};{op};0;0" keyTimes="{kt}" '
        f'dur="{n(cycle)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks}"/>'
        f'</line>'
    )


def loop_draw_path(d, stroke, width, length, t_in, dur=0.4, cycle=CYCLE):
    t0 = max(t_in, 0.02)
    t1 = min(t0 + dur, cycle - 1.2)
    t_hold = cycle - 0.85
    t_out = cycle - 0.28
    kt = _kt(cycle, 0, t0, t1, t_hold, t_out, cycle)
    ks = "0 0 1 1;0.22 1 0.36 1;0 0 1 1;0.4 0 0.2 1;0 0 1 1"
    L = n(length)
    return (
        f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{n(width)}" '
        f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{L}" stroke-dashoffset="{L}">'
        f'<animate attributeName="stroke-dashoffset" values="{L};{L};0;0;0;{L}" keyTimes="{kt}" '
        f'dur="{n(cycle)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks}"/>'
        f'<animate attributeName="opacity" values="0;1;1;1;0;0" keyTimes="{kt}" '
        f'dur="{n(cycle)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks}"/>'
        f'</path>'
    )


def wrap_lines(text, max_units):
    """按全角=2、半角=1.15 的宽度估算法自然断行，避免文字溢出卡片。"""
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


# ---------- 1. hero-metric（9 秒周期：0→1 完整生长 + 6 秒清晰停留 + 轻柔公转呼吸） ----------

def render_hero_metric(mod, th):
    kicker = escape(mod.get("kicker", ""))
    metric = escape(str(mod.get("metric", "")))
    unit = escape(mod.get("unit", ""))
    title = escape(mod.get("title", ""))
    subtitle = mod.get("subtitle", "")
    sub_lines = wrap_lines(subtitle, 46)[:2]

    h = 370 + max(len(sub_lines) - 1, 0) * 32
    els = []

    # 右侧极简同心圆环：随周期从 0→1 优雅渐显，并保持慢速公转呼吸
    els.append(
        f'<g opacity="0">'
        f'<circle cx="608" cy="126" r="98" fill="none" stroke="{th["border"]}" stroke-width="1.5"/>'
        f'<circle cx="608" cy="126" r="64" fill="none" stroke="{th["accent"]}" stroke-width="1.5" opacity="0.28"/>'
        f'<g>'
        f'<circle cx="608" cy="62" r="4.5" fill="{th["accent"]}" opacity="0.9"/>'
        f'<animateTransform attributeName="transform" type="rotate" from="0 608 126" to="360 608 126" dur="9s" repeatCount="indefinite"/>'
        f'</g>'
        f'<circle cx="608" cy="126" r="7" fill="{th["accent"]}">'
        f'<animate attributeName="opacity" values="1;0.45;1" dur="2.6s" repeatCount="indefinite"/>'
        f'</circle>'
        f'{loop_fade_in(0.35, 0.7)}</g>'
    )

    if kicker:
        els.append(
            f'<g opacity="0"><text x="52" y="72" font-size="22" font-weight="600" letter-spacing="1.8" '
            f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>{loop_fade_up(0.08, 0.5, 12)}</g>'
        )

    metric_size = 112 if len(metric) <= 4 else (88 if len(metric) <= 7 else 68)
    metric_w = sum(metric_size * (0.95 if ord(c) > 0x2E7F else 0.66) for c in str(mod.get("metric", "")))
    els.append(
        f'<g opacity="0">'
        f'<text x="48" y="198" font-size="{metric_size}" font-weight="700" letter-spacing="-2" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{metric}</text>'
        + (
            f'<text x="{n(68 + metric_w)}" y="192" font-size="30" font-weight="600" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{unit}</text>'
            if unit else ""
        )
        + f'{loop_fade_up(0.24, 0.65, 22)}</g>'
    )

    # 分割细线从左向右一笔拉出
    els.append(loop_draw_line(52, 232, 698, 232, th["border"], 1.5, 0.52, 0.7))
    els.append(loop_draw_line(52, 232, 148, 232, th["accent"], 2.5, 0.58, 0.6))

    els.append(
        f'<g opacity="0"><text x="52" y="286" font-size="32" font-weight="700" letter-spacing="-0.5" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>{loop_fade_up(0.72, 0.55, 14)}</g>'
    )
    for i, line in enumerate(sub_lines):
        els.append(
            f'<g opacity="0"><text x="52" y="{n(330 + i * 34)}" font-size="23" font-weight="400" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{escape(line)}</text>{loop_fade_up(0.9 + i * 0.14, 0.55, 12)}</g>'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 2. compare-split（9 秒周期：左先右后生长 + 对勾逐笔绘制） ----------

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
            f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>{loop_fade_up(0.06, 0.45, 10)}</g>'
        )
    els.append(
        f'<g opacity="0"><text x="48" y="114" font-size="36" font-weight="700" letter-spacing="-0.8" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>{loop_fade_up(0.16, 0.55, 14)}</g>'
    )

    def fit_font_size(text, base=22, max_w=244):
        est = sum(base * (1.0 if ord(c) > 0x2E7F else 0.58) for c in text)
        if est <= max_w:
            return base
        return max(16.5, round(base * max_w / est, 1))

    lx, lw = 38, 328
    els.append(
        f'<g opacity="0">'
        f'<rect x="{lx}" y="{card_y}" width="{lw}" height="{card_h}" rx="22" '
        f'fill="{th["card_alt"]}" stroke="{th["border"]}" stroke-width="1"/>'
        f'<rect x="{lx + 24}" y="{card_y + 24}" width="12" height="12" rx="6" fill="{th["danger"]}" opacity="0.72"/>'
        f'<text x="{lx + 46}" y="{card_y + 37}" font-size="22" font-weight="700" '
        f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{escape(left.get("tag", "旧方式"))}</text>'
        f'{loop_fade_up(0.32, 0.55, 16)}</g>'
    )
    els.append(loop_draw_line(lx + 24, card_y + 60, lx + lw - 24, card_y + 60, th["border"], 1, 0.48, 0.5))

    for i, item in enumerate(l_items):
        iy = card_y + 104 + i * row_h
        fs = fit_font_size(item, 22, lw - 74)
        els.append(
            f'<g opacity="0">'
            f'<line x1="{lx + 24}" y1="{iy - 8}" x2="{lx + 38}" y2="{iy - 8}" '
            f'stroke="{th["danger"]}" stroke-width="2.2" stroke-linecap="round" opacity="0.65"/>'
            f'<text x="{lx + 50}" y="{iy}" font-size="{n(fs)}" font-weight="500" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{escape(item)}</text>'
            f'{loop_fade_up(0.56 + i * 0.14, 0.45, 10)}</g>'
        )

    rx, rw = 384, 328
    els.append(
        f'<g opacity="0">'
        f'<rect x="{rx}" y="{card_y}" width="{rw}" height="{card_h}" rx="22" fill="{th["dark_card"]}"/>'
        f'<circle cx="{rx + 30}" cy="{card_y + 30}" r="6" fill="{th["ok"]}">'
        f'<animate attributeName="opacity" values="1;0.38;1" dur="2.2s" repeatCount="indefinite"/>'
        f'</circle>'
        f'<text x="{rx + 46}" y="{card_y + 37}" font-size="22" font-weight="700" '
        f'fill="{th["dark_text"]}" font-family=\'{FONT_STACK}\'>{escape(right.get("tag", "新方式"))}</text>'
        f'{loop_fade_up(0.5, 0.55, 18)}</g>'
    )
    els.append(loop_draw_line(rx + 24, card_y + 60, rx + rw - 24, card_y + 60, "#3A3A3F", 1, 0.66, 0.5))

    for i, item in enumerate(r_items):
        iy = card_y + 104 + i * row_h
        fs = fit_font_size(item, 22, rw - 76)
        t = 0.78 + i * 0.16
        check = loop_draw_path(
            f"M{rx + 24} {iy - 8} L{rx + 30} {iy - 2} L{rx + 41} {iy - 14}",
            th["ok"], 2.5, 28, t + 0.1, 0.36
        )
        els.append(
            f'<g opacity="0">'
            f'<text x="{rx + 52}" y="{iy}" font-size="{n(fs)}" font-weight="600" '
            f'fill="{th["dark_text"]}" font-family=\'{FONT_STACK}\'>{escape(item)}</text>'
            f'{loop_fade_up(t, 0.45, 10)}</g>{check}'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 3. flow-strip（9 秒周期：轨道绘制 + 步骤卡逐个长出 + 蓝点沿线流转） ----------

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
            f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>{loop_fade_up(0.06, 0.45, 10)}</g>'
        )
    els.append(
        f'<g opacity="0"><text x="48" y="114" font-size="36" font-weight="700" letter-spacing="-0.8" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>{loop_fade_up(0.16, 0.55, 14)}</g>'
    )

    rail_x = 84
    if cnt > 1:
        y_top = start_y + 56
        y_bot = start_y + (cnt - 1) * (step_h + gap) + 56
        els.append(loop_draw_line(rail_x, y_top, rail_x, y_bot, th["border"], 2, 0.36, 0.95))
        kt_dot = _kt(CYCLE, 0, 0.45, 2.1, CYCLE - 0.85, CYCLE - 0.28, CYCLE)
        ks_dot = "0 0 1 1;0.22 1 0.36 1;0 0 1 1;0.4 0 0.2 1;0 0 1 1"
        els.append(
            f'<circle cx="{rail_x}" cy="{y_top}" r="6" fill="{th["accent"]}" opacity="0">'
            f'<animate attributeName="cy" values="{y_top};{y_top};{y_bot};{y_bot};{y_bot};{y_top}" keyTimes="{kt_dot}" '
            f'dur="{n(CYCLE)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks_dot}"/>'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt_dot}" '
            f'dur="{n(CYCLE)}s" repeatCount="indefinite" calcMode="spline" keySplines="{ks_dot}"/>'
            f'</circle>'
        )

    for i, st in enumerate(steps):
        sy = start_y + i * (step_h + gap)
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
            f'{loop_fade_up(0.32 + i * 0.32, 0.55, 16)}</g>'
        )

    if footnote:
        els.append(
            f'<g opacity="0"><text x="48" y="{h - 24}" font-size="20" font-weight="500" '
            f'fill="{th["muted"]}" font-family=\'{FONT_STACK}\'>{footnote}</text>'
            f'{loop_fade_in(0.5 + cnt * 0.32, 0.5)}</g>'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 4. bento-grid（9 秒周期：Bento 卡片错峰从 0→1 浮起 + 呼吸状态点） ----------

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
            f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>{loop_fade_up(0.06, 0.45, 10)}</g>'
        )
    els.append(
        f'<g opacity="0"><text x="48" y="114" font-size="36" font-weight="700" letter-spacing="-0.8" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>{loop_fade_up(0.16, 0.55, 14)}</g>'
    )

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
        is_dark = bool(c.get("highlight"))
        bg = th["dark_card"] if is_dark else th["card"]
        fg = th["dark_text"] if is_dark else th["text"]
        sub_fg = th["dark_sub"] if is_dark else th["sub"]
        lbl_fg = th["accent"]
        stroke = "none" if is_dark else th["border"]

        label = escape(c.get("label", ""))
        val = escape(str(c.get("value", "")))
        desc_lines = wrap_lines(c.get("desc", ""), 38 if bw > 400 else 20)[:2]
        val_size = 40 if len(val) <= 6 else (32 if len(val) <= 10 else 26)

        pulse_dot = (
            f'<circle cx="{bx + bw - 32}" cy="{by + 36}" r="5" fill="{th["accent"]}">'
            f'<animate attributeName="opacity" values="1;0.3;1" begin="{n(i * 0.6)}s" dur="2.6s" repeatCount="indefinite"/>'
            f'</circle>'
        )

        els.append(
            f'<g opacity="0">'
            f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="24" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="1"/>'
            f'{pulse_dot}'
            f'<text x="{bx + 28}" y="{by + 44}" font-size="19" font-weight="600" letter-spacing="1" '
            f'fill="{lbl_fg}" font-family=\'{FONT_STACK}\'>{label}</text>'
            f'<text x="{bx + 28}" y="{by + 104}" font-size="{val_size}" font-weight="700" letter-spacing="-0.8" '
            f'fill="{fg}" font-family=\'{FONT_STACK}\'>{val}</text>'
            + "".join(
                f'<text x="{bx + 28}" y="{by + 144 + j * 28}" font-size="20" font-weight="400" '
                f'fill="{sub_fg}" font-family=\'{FONT_STACK}\'>{escape(dl)}</text>'
                for j, dl in enumerate(desc_lines)
            )
            + f'{loop_fade_up(0.32 + i * 0.24, 0.55, 18)}</g>'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 5. quote-seal（9 秒周期：短线展开 + 金句逐行浮现落版） ----------

def render_quote_seal(mod, th):
    kicker = escape(mod.get("kicker", ""))
    quote_lines = wrap_lines(mod.get("quote", ""), 26)[:3]
    subquote = escape(mod.get("subquote", ""))
    author = escape(mod.get("author", ""))

    h = 240 + len(quote_lines) * 48 + (42 if subquote else 0)
    els = []

    els.append(loop_draw_line(342, 58, 408, 58, th["accent"], 3, 0.08, 0.55))

    if kicker:
        els.append(
            f'<g opacity="0"><text x="375" y="102" text-anchor="middle" font-size="20" font-weight="600" '
            f'letter-spacing="2" fill="{th["muted"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>'
            f'{loop_fade_in(0.24, 0.45)}</g>'
        )

    qy = 158 if kicker else 136
    for i, line in enumerate(quote_lines):
        els.append(
            f'<g opacity="0"><text x="375" y="{qy + i * 50}" text-anchor="middle" font-size="36" font-weight="700" '
            f'letter-spacing="-0.5" fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{escape(line)}</text>'
            f'{loop_fade_up(0.38 + i * 0.18, 0.55, 16)}</g>'
        )

    cur_y = qy + len(quote_lines) * 50 + 10
    if subquote:
        els.append(
            f'<g opacity="0"><text x="375" y="{cur_y}" text-anchor="middle" font-size="22" font-weight="400" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{subquote}</text>'
            f'{loop_fade_in(0.76, 0.5)}</g>'
        )
        cur_y += 42

    if author:
        els.append(
            f'<g opacity="0"><text x="375" y="{cur_y + 12}" text-anchor="middle" font-size="19" font-weight="600" '
            f'letter-spacing="1.2" fill="{th["muted"]}" font-family=\'{FONT_STACK}\'>{author}</text>'
            f'{loop_fade_in(0.95, 0.5)}</g>'
        )

    return wrap_section("".join(els), h, th["bg"])


# ---------- 6. swipe-gallery（复刻高级横滑杂志展板，微信原生支持） ----------

def render_swipe_gallery(mod, th):
    kicker = escape(mod.get("kicker", "SWIPE GALLERY"))
    title = escape(mod.get("title", ""))
    hint = escape(mod.get("hint", "左右滑动浏览"))
    cards = mod.get("cards", [])[:6]
    total = len(cards)

    # 顶部标题 SVG（极简引导 + 微动滑动提示）
    head_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 118" width="100%" '
        f'style="display:block;width:100%;height:auto;">'
        f'<text x="36" y="42" font-size="20" font-weight="600" letter-spacing="1.6" '
        f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>'
        f'<text x="36" y="92" font-size="34" font-weight="700" letter-spacing="-0.6" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{title}</text>'
        f'<g>'
        f'<text x="714" y="88" text-anchor="end" font-size="20" font-weight="500" '
        f'fill="{th["muted"]}" font-family=\'{FONT_STACK}\'>{hint} →</text>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;-6 0;0 0" '
        f'keyTimes="0;0.5;1" dur="2.2s" repeatCount="3" {EASE}/>'
        f'</g></svg>'
    )

    # 横向滑动卡片轨道（微信原生保留 overflow-x:auto + white-space:nowrap + 内联 SVG）
    card_items = []
    for idx, c in enumerate(cards, 1):
        is_dark = bool(c.get("highlight"))
        bg = th["dark_card"] if is_dark else th["card"]
        fg = th["dark_text"] if is_dark else th["text"]
        sub_fg = th["dark_sub"] if is_dark else th["sub"]
        border = "none" if is_dark else th["border"]
        num = escape(str(c.get("num", f"{idx:02d}")))
        tag = escape(c.get("tag", ""))
        ctitle_lines = wrap_lines(c.get("title", ""), 18)[:2]
        desc_lines = wrap_lines(c.get("desc", ""), 26)[:4]
        foot = escape(c.get("foot", f"{idx} / {total}"))

        svg_card = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 620" width="270" '
            f'style="display:block;width:270px;height:310px;border-radius:18px;">'
            f'<rect x="1" y="1" width="538" height="618" rx="34" fill="{bg}" stroke="{border}" stroke-width="2"/>'
            # 顶部编号与标签
            f'<text x="42" y="72" font-size="24" font-weight="700" fill="{th["accent"]}" font-family=\'{MONO_STACK}\'>{num}</text>'
            f'<text x="498" y="70" text-anchor="end" font-size="20" font-weight="600" letter-spacing="1" '
            f'fill="{sub_fg}" font-family=\'{FONT_STACK}\'>{tag}</text>'
            f'<line x1="42" y1="102" x2="498" y2="102" stroke="{border if not is_dark else "#38383D"}" stroke-width="1.5"/>'
            # 大标题
            + "".join(
                f'<text x="42" y="{174 + j * 54}" font-size="40" font-weight="700" letter-spacing="-0.8" '
                f'fill="{fg}" font-family=\'{FONT_STACK}\'>{escape(ln)}</text>'
                for j, ln in enumerate(ctitle_lines)
            )
            # 正文说明
            + "".join(
                f'<text x="42" y="{318 + j * 40}" font-size="25" font-weight="400" '
                f'fill="{sub_fg}" font-family=\'{FONT_STACK}\'>{escape(ln)}</text>'
                for j, ln in enumerate(desc_lines)
            )
            # 右下角秩序细线与页脚
            + f'<line x1="42" y1="538" x2="102" y2="538" stroke="{th["accent"]}" stroke-width="3" stroke-linecap="round"/>'
            + f'<text x="498" y="546" text-anchor="end" font-size="20" font-weight="600" '
            f'fill="{sub_fg}" font-family=\'{MONO_STACK}\'>{foot}</text>'
            f'</svg>'
        )
        card_items.append(
            f'<section style="display:inline-block;vertical-align:top;width:270px;'
            f'margin-right:{14 if idx < total else 18}px;white-space:normal;">{svg_card}</section>'
        )

    return (
        f'<section style="margin:24px 0;padding:18px 0 22px;border-radius:16px;'
        f'background-color:{th["bg"]};overflow:hidden;">'
        f'<section style="line-height:0;font-size:0;margin-bottom:10px;">{head_svg}</section>'
        f'<section style="overflow-x:auto;overflow-y:hidden;white-space:nowrap;'
        f'-webkit-overflow-scrolling:touch;padding:4px 0 6px 18px;font-size:0;line-height:0;">'
        f'{"".join(card_items)}</section></section>'
    )


# ---------- 7. click-reveal（复刻头部公众号爆款“点击揭晓”互动卡片，零 id） ----------

def render_click_reveal(mod, th):
    kicker = escape(mod.get("kicker", "INTERACTIVE"))
    prompt = mod.get("prompt", "点击查看核心结论")
    prompt_lines = wrap_lines(prompt, 24)[:2]
    cta = escape(mod.get("cta", "轻点揭晓答案"))

    reveal_tag = escape(mod.get("reveal_tag", "已揭晓"))
    reveal_title = escape(mod.get("reveal_title", ""))
    reveal_lines = wrap_lines(mod.get("reveal_desc", ""), 34)[:3]

    h = 410
    els = []

    # 底层：揭晓后的真实内容（静静等在下面，盖板被点走后直接露出）
    els.append(
        f'<rect x="32" y="28" width="686" height="{h - 56}" rx="24" '
        f'fill="{th["card"]}" stroke="{th["border"]}" stroke-width="1.5"/>'
        f'<rect x="64" y="64" width="12" height="12" rx="6" fill="{th["ok"]}"/>'
        f'<text x="88" y="77" font-size="21" font-weight="700" letter-spacing="1.2" '
        f'fill="{th["ok"]}" font-family=\'{FONT_STACK}\'>{reveal_tag}</text>'
        f'<line x1="64" y1="104" x2="686" y2="104" stroke="{th["border"]}" stroke-width="1.2"/>'
        f'<text x="64" y="166" font-size="38" font-weight="700" letter-spacing="-0.8" '
        f'fill="{th["text"]}" font-family=\'{FONT_STACK}\'>{reveal_title}</text>'
        + "".join(
            f'<text x="64" y="{222 + i * 40}" font-size="25" font-weight="400" '
            f'fill="{th["sub"]}" font-family=\'{FONT_STACK}\'>{escape(ln)}</text>'
            for i, ln in enumerate(reveal_lines)
        )
    )

    # 顶层盖板：微信原生 begin="click"（点到谁，谁自己向上淡出移走，无需任何 id）
    cover_prompt_svg = "".join(
        f'<text x="375" y="{176 + i * 48}" text-anchor="middle" font-size="34" font-weight="700" '
        f'letter-spacing="-0.5" fill="{th["dark_text"]}" font-family=\'{FONT_STACK}\'>{escape(ln)}</text>'
        for i, ln in enumerate(prompt_lines)
    )
    btn_y = 266 if len(prompt_lines) > 1 else 242

    els.append(
        f'<g style="cursor:pointer;">'
        f'<rect x="32" y="28" width="686" height="{h - 56}" rx="24" fill="{th["dark_card"]}"/>'
        f'<circle cx="628" cy="112" r="96" fill="none" stroke="{th["accent"]}" stroke-width="1.5" opacity="0.22"/>'
        f'<text x="375" y="96" text-anchor="middle" font-size="20" font-weight="600" letter-spacing="2" '
        f'fill="{th["accent"]}" font-family=\'{FONT_STACK}\'>{kicker}</text>'
        f'{cover_prompt_svg}'
        # 居中胶囊按钮
        f'<rect x="255" y="{btn_y}" width="240" height="58" rx="29" fill="{th["accent"]}"/>'
        f'<circle cx="294" cy="{btn_y + 29}" r="5" fill="#FFFFFF">'
        f'<animate attributeName="opacity" values="1;0.35;1" dur="1.8s" repeatCount="indefinite"/>'
        f'</circle>'
        f'<text x="386" y="{btn_y + 37}" text-anchor="middle" font-size="22" font-weight="600" '
        f'fill="#FFFFFF" font-family=\'{FONT_STACK}\'>{cta}</text>'
        # 点击自身后丝滑上滑淡出并隐藏，露出底层答案
        f'<animate attributeName="opacity" from="1" to="0" begin="click" dur="0.45s" fill="freeze" {EASE}/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="0 -44" '
        f'begin="click" dur="0.45s" fill="freeze" {EASE}/>'
        f'<set attributeName="visibility" to="hidden" begin="click+0.46s" fill="freeze"/>'
        f'</g>'
    )

    return wrap_section("".join(els), h, th["bg"])


RENDERERS = {
    "hero-metric": render_hero_metric,
    "compare-split": render_compare_split,
    "flow-strip": render_flow_strip,
    "bento-grid": render_bento_grid,
    "quote-seal": render_quote_seal,
    "swipe-gallery": render_swipe_gallery,
    "click-reveal": render_click_reveal,
}


# ---------- 正文 Markdown → 微信安全苹果风混排 HTML ----------

SLOT_PAT = re.compile(r"^\s*(?:\[插入\s*SVG\s*模块\s*(\d+)[^\]]*\]|\{\{\s*module\s*:\s*(\d+)\s*\}\})\s*$")


def render_inline_md(text):
    """处理行内粗体与行内代码，输出微信安全的内联样式。"""
    s = escape(text)
    s = re.sub(
        r"`([^`]+)`",
        r'<code style="padding:2px 6px;border-radius:6px;background-color:#F2F2F5;'
        r'color:#1D1D1F;font-size:14px;font-family:Menlo,Consolas,monospace;">\1</code>',
        s,
    )
    s = re.sub(
        r"\*\*([^*]+)\*\*",
        r'<strong style="font-weight:700;color:#1D1D1F;">\1</strong>',
        s,
    )
    return s


def compose_article_html(md_text, packed_modules):
    """把正文 Markdown 与对应序号的 SVG 模块合并成可直接一键粘贴进公众号的完整 HTML。"""
    mod_by_idx = {m["index"]: m["html"] for m in packed_modules}
    used_indices = set()
    blocks = []

    for raw_line in md_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # 模块占位符
        m = SLOT_PAT.match(line)
        if m:
            idx = int(m.group(1) or m.group(2))
            if idx in mod_by_idx:
                blocks.append(mod_by_idx[idx])
                used_indices.add(idx)
            continue

        # 跳过一级主标题（公众号标题单独填在标题栏，正文不再重复堆大标题）
        if line.startswith("# "):
            continue

        if line.startswith("## "):
            title_txt = render_inline_md(line[3:].strip())
            blocks.append(
                f'<h2 data-feis-h2="1" style="margin:36px 0 16px;font-size:19px;font-weight:700;'
                f'line-height:1.4;color:#1D1D1F;letter-spacing:0px;">{title_txt}</h2>'
            )
            continue

        if line.startswith("### "):
            title_txt = render_inline_md(line[4:].strip())
            blocks.append(
                f'<h3 style="margin:26px 0 12px;font-size:16px;font-weight:700;'
                f'line-height:1.45;color:#1D1D1F;">{title_txt}</h3>'
            )
            continue

        if line.startswith("> "):
            quote_txt = render_inline_md(line[2:].strip())
            blocks.append(
                f'<section style="margin:24px 0;padding:14px 18px;border-left:3px solid #0071E3;'
                f'background-color:#F5F5F7;border-radius:0 12px 12px 0;font-size:15px;'
                f'line-height:1.8;color:#424245;">{quote_txt}</section>'
            )
            continue

        blocks.append(
            f'<p data-feis-p="1" style="margin:0 0 24px;font-size:15px;line-height:1.8;'
            f'letter-spacing:0px;color:#2C2C2E;text-align:left;">{render_inline_md(line)}</p>'
        )

    # 未在正文里显式占位的模块自动追加在文末
    for mod in packed_modules:
        if mod["index"] not in used_indices:
            blocks.append(mod["html"])

    return (
        f'<section data-feis-article="1" style="padding:12px 18px;font-family:{FONT_STACK};'
        f'background-color:#FFFFFF;color:#2C2C2E;box-sizing:border-box;">'
        f'{"".join(blocks)}</section>'
    )


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
    --border: rgba(0,0,0,0.08); --accent: #0071E3; --ok: #1F8A4C;
  }}
  [data-mode="dark"] {{
    --bg: #000000; --surface: #161618; --text: #F5F5F7; --sub: #A1A1A6;
    --border: rgba(255,255,255,0.12); --accent: #2997FF; --ok: #30D158;
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
    background: color-mix(in srgb, var(--surface) 84%, transparent);
    border-bottom: 1px solid var(--border);
    padding: 12px 16px; display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap;
  }}
  .btn {{
    border: 1px solid var(--border); background: var(--surface); color: var(--text);
    padding: 7px 14px; border-radius: 999px; font-size: 13px; font-weight: 500; cursor: pointer;
    transition: transform 120ms ease, background-color 180ms ease;
  }}
  .btn:active {{ transform: scale(0.96); }}
  .btn.primary {{ background: var(--accent); color: #fff; border-color: transparent; font-weight: 600; }}
  .phone {{
    width: 414px; max-width: calc(100% - 24px); margin: 24px auto 64px;
    background: var(--surface); border-radius: 28px; padding: 28px 20px 44px;
    border: 1px solid var(--border); box-shadow: 0 20px 60px rgba(0,0,0,0.08);
    transition: background-color 240ms cubic-bezier(0.22,1,0.36,1);
  }}
  .phone h1 {{ font-size: 22px; line-height: 1.38; margin: 0 0 8px; letter-spacing: -0.4px; }}
  .meta {{ font-size: 13px; color: var(--sub); margin-bottom: 22px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }}
  .article-body {{ background: #FFFFFF; border-radius: 16px; padding: 14px 12px; }}
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
  <button class="btn primary" onclick="copyWhole()">一键复制整篇到公众号</button>
  <button class="btn" onclick="replayAll()">重播动效</button>
  <button class="btn" onclick="toggleMode()">切换深浅底</button>
</div>
<div class="phone">
  <h1>{title}</h1>
  <div class="meta">非叔 SVG 完整预览 · 可将同目录 feis-pack.json 拖入 Chrome 插件一键插入</div>
  <div class="article-body" id="stage"></div>
</div>
<div class="toast" id="toast"></div>
<script>
const PACK = {pack_json};
function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(window._tt); window._tt = setTimeout(() => t.classList.remove('show'), 2000);
}}
function renderAll() {{
  document.getElementById('stage').innerHTML = PACK.articleHtml;
}}
function replayAll() {{
  const s = document.getElementById('stage');
  s.innerHTML = '';
  requestAnimationFrame(renderAll);
}}
function toggleMode() {{
  document.documentElement.dataset.mode = document.documentElement.dataset.mode === 'dark' ? 'light' : 'dark';
}}
async function copyWhole() {{
  try {{
    await navigator.clipboard.write([new ClipboardItem({{
      'text/html': new Blob([PACK.articleHtml], {{type: 'text/html'}}),
      'text/plain': new Blob([PACK.articleHtml], {{type: 'text/plain'}})
    }})]);
    showToast('已复制整篇文章，去公众号编辑器按 ⌘V 粘贴');
  }} catch (e) {{
    showToast('本地 file:// 受限时，请把 feis-pack.json 拖进 Chrome 插件一键复制');
  }}
}}
renderAll();
</script>
</body>
</html>
"""


def build_pack(spec, out_dir, base_dir=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    title = spec.get("title", "未命名文章")
    summary = spec.get("summary", "")
    category = spec.get("category", "apple-bento")
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

    # 若指定了 article_md，合并正文排版与所有 SVG 模块成一篇完整文章
    article_md_path = spec.get("article_md")
    if article_md_path:
        md_file = (Path(base_dir) / article_md_path) if base_dir else Path(article_md_path)
        md_text = md_file.read_text(encoding="utf-8")
        article_html = compose_article_html(md_text, packed)
        has_article = True
    else:
        article_html = (
            f'<section style="padding:8px 4px;font-family:{FONT_STACK};background-color:#FFFFFF;">'
            + "".join(m["html"] for m in packed)
            + "</section>"
        )
        has_article = False

    article_lint = lint_wechat_svg(article_html)
    (out / "article.html").write_text(article_html, encoding="utf-8")

    pack_obj = {
        "packVersion": 2,
        "generator": "feis-wx-svg",
        "title": title,
        "summary": summary,
        "category": category,
        "hasArticle": has_article,
        "articleHtml": article_html,
        "articleBytes": article_lint["bytes"],
        "articleLint": article_lint,
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
    ap = argparse.ArgumentParser(description="feis-wx-svg · 苹果发布会极简风公众号 SVG 模块与整篇混排生成器")
    ap.add_argument("spec", help="模块配置 JSON 路径")
    ap.add_argument("-o", "--out", help="输出目录（默认：配置同级 dist 目录）")
    a = ap.parse_args()
    sp = Path(a.spec).resolve()
    spec = json.loads(sp.read_text(encoding="utf-8"))
    out = Path(a.out) if a.out else sp.parent / "dist"
    pack = build_pack(spec, out, base_dir=sp.parent)
    art_kb = pack["articleBytes"] / 1024
    ok_all = pack["articleLint"]["ok"] and all(m["lint"]["ok"] for m in pack["modules"])
    mode_tag = "整篇图文混排" if pack["hasArticle"] else "纯模块集合"
    print(f"✅ [{mode_tag}] {pack['title']} → {out}/ (整篇 {art_kb:.1f}KB · {len(pack['modules'])} 个模块 · 微信合规={'通过' if ok_all else '有警告'})")
    for m in pack["modules"]:
        status = "OK" if m["lint"]["ok"] else ",".join(m["lint"]["issues"])
        print(f"   {m['file']}  [{m['type']}]  {m['bytes']/1024:.1f}KB  ({status})")


if __name__ == "__main__":
    main()
