import math
import re
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

BG, BG1, BG2 = "#282828", "#3c3836", "#504945"
FG, GRAY = "#ebdbb2", "#928374"
RED, ORANGE, YELLOW, GREEN, AQUA, BLUE, PURPLE = (
    "#fb4934", "#fe8019", "#fabd2f", "#b8bb26", "#8ec07c", "#83a598", "#d3869b")
DARK_ORANGE = "#d65d0e"
FONT = "SFMono-Regular, Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"

REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def shield_frame(pos, cols=41, rows=21):
    cx, cy = (cols - 1) / 2, (rows - 1) / 2
    top, bottom, half = -10.0, 10.0, 9.2
    out = []
    for j in range(rows):
        y = j - cy
        if y <= -2:
            w = half
        else:
            t = (y + 2) / (bottom + 2)
            w = half * max(0.0, 1 - t ** 1.5) ** 0.62
        row = []
        for i in range(cols):
            u = (i - cx) * 0.5
            d = w - abs(u)
            ch = (" ", "")
            if d >= 0 and y >= top and w > 0.3:
                dt = y - top
                ls = next((n for n, lim in enumerate((1.0, 1.5, 2.0, 2.5, 3.0)) if d < lim), 5)
                lt = int(dt) if dt < 5 else 5
                layer = min(ls, lt)
                idx = j if ls <= lt else i
                if layer == 0:
                    ch = ("@", "a")
                    if (lt == 0 and i % 4 == 0) or (ls == 0 and lt > 0 and j % 4 == 1):
                        ch = ("o", "b")
                elif layer == 1:
                    ch = ("#", "b") if idx % 2 == 0 else ("=", "h")
                elif layer == 2:
                    ch = ("(~)~"[idx % 4], "a")
                elif layer == 3:
                    ch = ("=", "h")
                elif layer == 4:
                    ch = ("o", "a") if idx % 3 == 0 else (".", "d")
                else:
                    ch = ("%", "c") if (i // 2 + j) % 2 == 0 else ("+", "h")
                if ls <= 1 and lt <= 1:
                    ch = ("O", "b")
                elif ls == 2 and lt == 2:
                    ch = ("*", "b")
                elif ls in (3, 4) and lt in (3, 4) and ls == lt:
                    ch = ("+", "b")
                if ls <= 2 and lt > 2 and j in (8, 12):
                    ch = ("O", "b")
                if lt == 0 and abs(i - cx) <= 1.5 and ch[1]:
                    ch = ("<*>"[int(i - cx + 1.5) % 3], "b") if abs(i - cx) < 1.5 else ch
                if lt == 1 and abs(i - cx) < 3.5:
                    ch = ("^", "b") if abs(i - cx) % 2 == 0 else ("=", "h")
                if y >= bottom - 1 and abs(u) < 0.8 and ch[1]:
                    ch = ("*", "b")
                if ch[1] and abs(0.8 * u + 0.6 * y - pos) < 1.3:
                    ch = (ch[0], "e")
            row.append(ch)
        out.append(row)
    return out


def frame_to_text(frame, x, y0, lh):
    cls_color = {"a": ORANGE, "b": YELLOW, "c": DARK_ORANGE, "d": GRAY, "e": "#fbf1c7", "h": "#af3a03"}
    lines = []
    for n, row in enumerate(frame):
        parts, run, cur = [], "", None
        for ch, cls in row + [(" ", "")]:
            if cls != cur and run:
                color = cls_color.get(cur)
                parts.append(f'<tspan fill="{color}">{escape(run)}</tspan>' if color else escape(run))
                run = ""
            cur = cls
            run += ch
        lines.append(f'<text x="{x}" y="{y0 + n * lh}" xml:space="preserve">{"".join(parts)}</text>')
    return "\n".join(lines)


def animated_shield(x, y0, lh, frames=16, sweep=11, cycle=3.2):
    step = cycle / frames
    groups = []
    for f in range(frames):
        pos = -14 + 28 * f / (sweep - 1) if f < sweep else 99
        delay = 0 if f == 0 else -(cycle - f * step)
        groups.append(f'<g class="gf" style="animation-delay:{delay:.3f}s">'
                      f'{frame_to_text(shield_frame(pos), x, y0, lh)}</g>')
    css = (f".gf{{opacity:0;animation:gf {cycle}s steps(1,end) infinite}}"
           f"@keyframes gf{{0%{{opacity:1}}{100/frames:.3f}%{{opacity:0}}100%{{opacity:0}}}}")
    return "\n".join(groups), css


def anvil_scene(cycle=1.6):
    ix, iy = 150, 108
    px, py = 250, 88
    strike, lift = 0.40, 0.48
    fmt = lambda v: f"{v:.3f}".rstrip("0").rstrip(".") or "0"

    anvil = (
        f'<path d="M58,122 Q84,121 100,112 L208,112 L208,128 L182,140 L174,140 L178,168 '
        f'L194,184 L194,196 L106,196 L106,184 L122,168 L126,140 L118,140 Q94,138 82,132 Z" fill="#665c54"/>'
        f'<path d="M100,112 L208,112 L208,121 L100,121 Z" fill="#7c6f64"/>'
        f'<path d="M58,122 Q84,121 100,112" fill="none" stroke="{YELLOW}" stroke-width="2" stroke-linecap="round"/>'
        f'<path d="M100,112 L208,112" stroke="{YELLOW}" stroke-width="3" stroke-linecap="round"/>'
        f'<rect x="106" y="186" width="88" height="10" fill="{BG2}"/>'
        f'<path d="M126,140 L122,168 M174,140 L178,168" stroke="{BG2}" stroke-width="3"/>')
    work = (f'<rect x="130" y="108" width="40" height="4" rx="2" fill="{ORANGE}">'
            f'<animate attributeName="fill" values="{RED};{ORANGE};{YELLOW};{ORANGE};{RED}" dur="{cycle}s" repeatCount="indefinite"/></rect>')

    angle_vals = f"32 {px} {py};32 {px} {py};0 {px} {py};0 {px} {py};32 {px} {py}"
    angle_keys = f"0;{fmt(strike)};{fmt(lift - 0.04)};{fmt(lift)};1"
    hammer = (
        f'<g><line x1="{px + 22}" y1="{py}" x2="{px - 100}" y2="{py}" stroke="#b57614" stroke-width="6" stroke-linecap="round"/>'
        f'<rect x="{px - 112}" y="{py - 12}" width="24" height="32" rx="3" fill="#a89984"/>'
        f'<rect x="{px - 112}" y="{py - 12}" width="24" height="7" rx="3" fill="#d5c4a1"/>'
        f'<animateTransform attributeName="transform" type="rotate" dur="{cycle}s" repeatCount="indefinite" '
        f'values="{angle_vals}" keyTimes="{angle_keys}"/></g>')

    rnd = random.Random(11)
    sparks = []
    hit = lift - 0.04
    for _ in range(16):
        ang = math.radians(rnd.uniform(200, 340))
        sp = rnd.uniform(25, 75)
        dx, dy = sp * math.cos(ang), sp * math.sin(ang)
        r = rnd.uniform(1.1, 2.4)
        col = rnd.choice([ORANGE, YELLOW, RED, "#fbf1c7"])
        sparks.append(
            f'<circle r="{r:.1f}" fill="{col}" opacity="0" cx="{ix}" cy="{iy}">'
            f'<animate attributeName="cx" values="{ix};{ix};{ix + dx:.0f};{ix + dx * 1.25:.0f};{ix + dx * 1.25:.0f}" '
            f'keyTimes="0;{fmt(hit)};{fmt(hit + .22)};{fmt(hit + .42)};1" dur="{cycle}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{iy};{iy};{iy + dy:.0f};{iy + dy + 40:.0f};{iy + dy + 40:.0f}" '
            f'keyTimes="0;{fmt(hit)};{fmt(hit + .22)};{fmt(hit + .42)};1" dur="{cycle}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0;1;0.8;0;0" '
            f'keyTimes="0;{fmt(hit)};{fmt(hit + .03)};{fmt(hit + .25)};{fmt(hit + .42)};1" dur="{cycle}s" repeatCount="indefinite"/></circle>')
    flash = (f'<circle cx="{ix}" cy="{iy}" r="0" fill="#fbf1c7" opacity="0">'
             f'<animate attributeName="r" values="0;0;16;0;0" keyTimes="0;{fmt(hit)};{fmt(hit + .04)};{fmt(hit + .12)};1" dur="{cycle}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="0;{fmt(hit)};{fmt(hit + .04)};{fmt(hit + .12)};1" dur="{cycle}s" repeatCount="indefinite"/></circle>')
    return f"{anvil}{work}{hammer}{flash}{''.join(sparks)}"


W = 860
HEADER_H = 220
LINE_Y_TOP, LINE_PAD = 12, 18


def header_part():
    lines = ["Machine Learning Engineer @ Tractian",
             "Deploying & monitoring ML models",
             "Performance \u00b7 data processing",
             "Python \u00b7 PyTorch \u00b7 Go"]
    cw, fs = 13.2, 22
    cycle, slot = 16.0, 4.0
    x0, ty = 300, 150
    items = []
    cursor_events = [(0.0, 0.0)]
    fmt = lambda v: f"{v:.4f}".rstrip("0").rstrip(".") or "0"
    for k, text in enumerate(lines):
        n = len(text)
        s = k * slot / cycle
        dt = 1.6 / cycle / n
        end = s + 3.6 / cycle
        times = [0.0] + [s + i * dt for i in range(1, n + 1)] + [end, 1.0]
        widths = [0.1] + [i * cw for i in range(1, n + 1)] + [0.1, 0.1]
        cursor_events += [(s + i * dt, i * cw) for i in range(1, n + 1)] + [(end, 0.0)]
        base_w = n * cw if k == 0 else 0.1
        items.append(
            f'<clipPath id="clip{k}"><rect x="{x0}" y="{ty - fs}" width="{base_w:.1f}" height="{fs + 10}">'
            f'<animate attributeName="width" calcMode="discrete" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{";".join(fmt(t) for t in times)}" values="{";".join(f"{w:.1f}" for w in widths)}"/></rect></clipPath>'
            f'<text x="{x0}" y="{ty}" class="typed" clip-path="url(#clip{k})" opacity="{1 if k == 0 else 0}" xml:space="preserve">{escape(text)}'
            f'<animate attributeName="opacity" calcMode="discrete" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{fmt(0.0)};{fmt(s)};{fmt(end)};1" values="{0 if k else 1};1;0;0"/></text>')
    cursor_events.append((1.0, 0.0))
    items.append(
        f'<rect x="{x0}" y="{ty - fs + 3}" width="9" height="{fs}" fill="{YELLOW}" opacity=".9">'
        f'<animate attributeName="x" calcMode="discrete" dur="{cycle}s" repeatCount="indefinite" '
        f'keyTimes="{";".join(fmt(t) for t, _ in cursor_events)}" '
        f'values="{";".join(f"{x0 + w:.1f}" for _, w in cursor_events)}"/></rect>')

    sparks = []

    css = (f".name{{font-size:46px;font-weight:700;fill:url(#ember)}}"
           f".typed{{font-size:{fs}px;fill:{FG}}}"
           f".glow{{animation:glow 3s ease-in-out infinite alternate}}"
           f"@keyframes glow{{from{{opacity:.10}}to{{opacity:.28}}}}")
    svg = f'''<ellipse class="glow" cx="150" cy="130" rx="135" ry="85" fill="{ORANGE}"/>
{anvil_scene()}
{"".join(sparks)}
<text x="{x0}" y="104" class="name">PEDRO CRESPAN</text>
{"".join(items)}'''
    return css, svg


def neofetch_part(dy):
    shield_svg, shield_css = animated_shield(28, 78, 14)
    info = [
        ("pcrespan", "@", "github", None),
        None,
        ("Rank", "Machine Learning Engineer", None),
        ("Guild", "Tractian", None),
        ("Academy", "UNESP \u00b7 Information Systems", None),
        ("Craft", "Performance \u00b7 Model deployment", None),
        ("", "Monitoring \u00b7 Data processing", None),
        ("Location", "Bauru, Brasil", None),
    ]
    x, y = 360, 92
    rows = []
    for n, item in enumerate(info):
        yy = y + n * 24
        if item is None:
            rows.append(f'<text x="{x}" y="{yy}" class="dim">{"-" * 30}</text>')
        elif len(item) == 4:
            rows.append(f'<text x="{x}" y="{yy}"><tspan class="user">{escape(item[0])}</tspan>'
                        f'<tspan class="dim">{item[1]}</tspan><tspan class="user">{escape(item[2])}</tspan></text>')
        else:
            label = f'<tspan class="lab">{escape(item[0]).ljust(10).replace(" ", chr(160))}</tspan>' if item[0] else \
                f'<tspan class="lab">{chr(160) * 10}</tspan>'
            rows.append(f'<text x="{x}" y="{yy}">{label}<tspan class="val">{escape(item[1])}</tspan></text>')
    palette = [BG1, RED, GREEN, YELLOW, BLUE, PURPLE, AQUA, FG]
    sw = "".join(f'<rect x="{x + i * 28}" y="{y + len(info) * 24 + 6}" width="28" height="16" fill="{c}"/>'
                 for i, c in enumerate(palette))
    css = (f".info text{{font-size:15px}}.user{{fill:{ORANGE};font-weight:700}}.lab{{fill:{ORANGE};font-weight:700}}"
           f".val{{fill:{FG}}}.dim{{fill:{GRAY}}}.prompt{{font-size:13px}}"
           f".cur{{animation:blink 1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}{shield_css}")
    svg = f'''<g transform="translate(0 {dy})">
<text x="24" y="58" class="prompt"><tspan fill="{GREEN}">pcrespan@github</tspan><tspan fill="{FG}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{FG}">$ neofetch</tspan></text>
{shield_svg}
<g class="info">
{chr(10).join(rows)}
{sw}
<rect class="cur" x="{x + 8 * 28 + 14}" y="{y + len(info) * 24 + 6}" width="9" height="16" fill="{YELLOW}"/>
</g>
</g>'''
    shield_bottom = 78 + 20 * 14
    return css, svg, shield_bottom + dy


def profile():
    divider_y = HEADER_H
    PROMPT_GAP = 58
    dy = divider_y + PROMPT_GAP - 58
    h_css, h_svg = header_part()
    n_css, n_svg, content_bottom = neofetch_part(dy)
    bottom_y = content_bottom + 22
    H = bottom_y + LINE_Y_TOP

    def rule(y):
        return (f'<line x1="{LINE_PAD}" x2="{W - LINE_PAD}" y1="{y}" y2="{y}" stroke="url(#rule)" '
                f'stroke-width="2" stroke-linecap="round"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Pedro Crespan, Machine Learning Engineer at Tractian. Typing header and a neofetch-style card with an animated ASCII shield.">
<title>Pedro Crespan - Machine Learning Engineer</title>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="#32302f"/></linearGradient>
<linearGradient id="ember" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{ORANGE}"/><stop offset="1" stop-color="{YELLOW}"/></linearGradient>
<linearGradient id="rule" gradientUnits="userSpaceOnUse" x1="{LINE_PAD}" y1="0" x2="{W - LINE_PAD}" y2="0"><stop offset="0" stop-color="{ORANGE}"/><stop offset="1" stop-color="{YELLOW}"/></linearGradient>
</defs>
<style>
text{{font-family:{FONT};font-size:12px;fill:{FG}}}
{h_css}
{n_css}
{REDUCED}
</style>
<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>
{h_svg}
{n_svg}
{rule(LINE_Y_TOP)}
{rule(bottom_y)}
</svg>
'''
    (OUT / "profile.svg").write_text(svg, encoding="utf-8")


def badge(name, label, value, color):
    cw = 7.4
    lw = int(len(label) * cw + 18)
    vw = int(len(value) * cw + 18)
    W, H = lw + vw, 28
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}: {escape(value)}">
<title>{escape(label)}: {escape(value)}</title>
<style>text{{font-family:{FONT};font-size:12px;font-weight:700}}</style>
<rect width="{W}" height="{H}" rx="5" fill="{BG1}"/>
<rect x="{lw}" width="{vw}" height="{H}" rx="5" fill="{color}"/><rect x="{lw}" width="8" height="{H}" fill="{color}"/>
<text x="{lw / 2}" y="18" text-anchor="middle" fill="{FG}">{escape(label)}</text>
<text x="{lw + vw / 2}" y="18" text-anchor="middle" fill="{BG}">{escape(value)}</text>
</svg>
'''
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    profile()
    badge("badge-location", "LOC", "Bauru, Brasil", GREEN)
    badge("badge-linkedin", "IN", "LinkedIn", BLUE)
    badge("badge-researchgate", "RG", "ResearchGate", AQUA)
    print("assets written to", OUT)
