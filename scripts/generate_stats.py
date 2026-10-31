import datetime
import json
import os
import random
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

API = "https://api.github.com"
USER = os.environ.get("GH_USER", "pcrespan")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = Path(__file__).resolve().parent.parent / "assets"

EXCLUDE_LANGS = {"Jupyter Notebook"}

CARD_W, CARD_H = 420, 230

C = dict(bg="#282828", border="#504945", fg="#ebdbb2", gray="#928374",
         orange="#fe8019", yellow="#fabd2f", green="#b8bb26", aqua="#8ec07c",
         blue="#83a598", purple="#d3869b", red="#fb4934")
BAR_COLORS = [C["orange"], C["yellow"], C["green"], C["aqua"], C["blue"], C["purple"], C["red"]]
FONT = "SFMono-Regular, Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"

if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", USER):
    sys.exit("GH_USER is not a valid GitHub username")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def call(path, payload=None):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "profile-stats-script"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, headers=headers)
    with _opener.open(req, timeout=20) as resp:
        return json.load(resp)


def fetch():
    user = call(f"/users/{USER}")
    repos, page = [], 1
    while page <= 5:
        chunk = call(f"/users/{USER}/repos?type=owner&per_page=100&page={page}")
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]

    langs = {}
    for r in own:
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", r["full_name"]):
            continue
        for lang, n in call(f"/repos/{r['full_name']}/languages").items():
            if lang not in EXCLUDE_LANGS:
                langs[lang] = langs.get(lang, 0) + n

    contrib = None
    if TOKEN:
        q = ('query($u:String!){user(login:$u){contributionsCollection{'
             'totalCommitContributions totalPullRequestContributions '
             'totalIssueContributions restrictedContributionsCount '
             'contributionCalendar{totalContributions weeks{contributionDays{contributionCount date weekday}}}}}}')
        res = call("/graphql", {"query": q, "variables": {"u": USER}})
        contrib = res["data"]["user"]["contributionsCollection"]

    return {
        "repos": len(own),
        "stars": sum(r["stargazers_count"] for r in own),
        "forks": sum(r["forks_count"] for r in own),
        "followers": user["followers"],
        "contrib": contrib,
        "langs": langs,
    }


def card(width, height, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
text{{font-family:{FONT};}}
.t{{font-size:15px;font-weight:700;fill:{C["orange"]}}}
.l{{font-size:13px;fill:{C["gray"]}}}
.v{{font-size:13px;font-weight:700;fill:{C["yellow"]}}}
.p{{font-size:12px;fill:{C["fg"]}}}
.row{{opacity:0;animation:in .6s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateX(-8px)}}to{{opacity:1;transform:none}}}}
@media (prefers-reduced-motion:reduce){{.row{{animation:none;opacity:1}}}}
</style>
<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="10" fill="{C["bg"]}" stroke="{C["border"]}"/>
{body}
</svg>
'''


def stats_svg(d):
    rows = [("Public repos", d["repos"]), ("Stars earned", d["stars"]),
            ("Forks", d["forks"]), ("Followers", d["followers"])]
    if d["contrib"]:
        c = d["contrib"]
        rows += [("Commits (12 mo)", c["totalCommitContributions"] + c["restrictedContributionsCount"]),
                 ("Pull requests (12 mo)", c["totalPullRequestContributions"]),
                 ("Issues (12 mo)", c["totalIssueContributions"])]
    w, h = CARD_W, CARD_H
    body = [f'<text x="20" y="32" class="t">GitHub stats / {escape(USER)}</text>',
            f'<line x1="20" y1="42" x2="{w-20}" y2="42" stroke="{C["border"]}"/>']
    top, pad, gap_max = 42, 26, 34
    gap = min(gap_max, (h - top - 2 * pad) / max(len(rows) - 1, 1))
    first = top + (h - top - gap * (len(rows) - 1)) / 2 + 4
    for i, (label, val) in enumerate(rows):
        y = first + gap * i
        body.append(f'<g class="row" style="animation-delay:{i*0.12:.2f}s">'
                    f'<rect x="20" y="{y-9}" width="8" height="8" fill="{BAR_COLORS[i % len(BAR_COLORS)]}"/>'
                    f'<text x="38" y="{y}" class="l">{escape(label)}</text>'
                    f'<text x="{w-20}" y="{y}" class="v" text-anchor="end">{escape(str(val))}</text></g>')
    return card(w, h, f"GitHub stats for {USER}", "\n".join(body)), h


def langs_svg(d):
    total = sum(d["langs"].values()) or 1
    top = sorted(d["langs"].items(), key=lambda kv: -kv[1])[:7]
    w, bar_x, bar_w = CARD_W, 20, 380
    body = [f'<text x="20" y="32" class="t">Languages</text>',
            f'<clipPath id="bar"><rect x="{bar_x}" y="48" width="{bar_w}" height="10" rx="5"/></clipPath>',
            f'<g clip-path="url(#bar)"><rect x="{bar_x}" y="48" width="{bar_w}" height="10" fill="{C["border"]}"/>']
    x = bar_x
    for i, (_, n) in enumerate(top):
        seg = bar_w * n / total
        body.append(f'<rect x="{x:.1f}" y="48" width="{seg:.1f}" height="10" fill="{BAR_COLORS[i % len(BAR_COLORS)]}"/>')
        x += seg
    body.append('</g>')
    for i, (lang, n) in enumerate(top):
        col, row = i % 2, i // 2
        lx, ly = 20 + col * 200, 86 + row * 24
        body.append(f'<g class="row" style="animation-delay:{i*0.12:.2f}s">'
                    f'<circle cx="{lx+4}" cy="{ly-4}" r="4" fill="{BAR_COLORS[i % len(BAR_COLORS)]}"/>'
                    f'<text x="{lx+16}" y="{ly}" class="p">{escape(lang)} '
                    f'<tspan fill="{C["gray"]}">{100*n/total:.1f}%</tspan></text></g>')
    return card(w, CARD_H, f"Top languages for {USER}", "\n".join(body))


LEVELS = ["#3c3836", "#6b4a1e", "#b57614", "#d79921", "#fabd2f"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def contributions_svg(cal, placeholder=False):
    weeks = cal["weeks"]
    counts = [int(day["contributionCount"]) for wk in weeks for day in wk["contributionDays"]]
    peak = max(counts + [1])
    total = int(cal["totalContributions"])
    w, h, cell, pitch, left, top = 860, 200, 12, 15, 34, 58

    def level(n):
        if n <= 0:
            return 0
        ratio = n / peak
        return 1 if ratio <= .25 else 2 if ratio <= .5 else 3 if ratio <= .75 else 4

    title = "Contributions" if placeholder else f"{total} contributions in the last year"
    body = [f'<text x="20" y="32" class="t">{escape(title)}</text>']
    last_label = -9
    for i, wk in enumerate(weeks):
        days = wk["contributionDays"]
        if not days:
            continue
        date = days[0]["date"]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            raise ValueError("unexpected date format")
        month = int(date[5:7])
        prev = weeks[i - 1]["contributionDays"][0]["date"] if i else None
        if i - last_label >= 3 and (prev is None or int(prev[5:7]) != month):
            body.append(f'<text x="{left + i * pitch}" y="{top - 8}" class="l" style="font-size:10px">{MONTHS[month - 1]}</text>')
            last_label = i
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body.append(f'<text x="{left - 8}" y="{top + row * pitch + 10}" class="l" style="font-size:10px" text-anchor="end">{name}</text>')
    for i, wk in enumerate(weeks):
        cells = []
        for day in wk["contributionDays"]:
            n, date, wd = int(day["contributionCount"]), day["date"], int(day["weekday"])
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or not 0 <= wd <= 6:
                raise ValueError("unexpected calendar data")
            tip = "" if placeholder else f"<title>{n} contributions on {date}</title>"
            cells.append(f'<rect x="{left + i * pitch}" y="{top + wd * pitch}" width="{cell}" height="{cell}" rx="2" fill="{LEVELS[level(n)]}">{tip}</rect>')
        body.append(f'<g class="row" style="animation-delay:{i * 0.015:.3f}s">{"".join(cells)}</g>')
    ly = top + 7 * pitch + 22
    lx = w - 20 - (5 * 15 + 70)
    body.append(f'<text x="{lx}" y="{ly + 9}" class="l" style="font-size:10px">Less</text>')
    for n, col in enumerate(LEVELS):
        body.append(f'<rect x="{lx + 32 + n * 15}" y="{ly}" width="{cell}" height="{cell}" rx="2" fill="{col}"/>')
    body.append(f'<text x="{lx + 32 + 5 * 15 + 4}" y="{ly + 9}" class="l" style="font-size:10px">More</text>')
    return card(w, h, title, "\n".join(body))


def placeholder_calendar():
    rnd = random.Random(3)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks = []
    for i in range(53):
        days = []
        for wd in range(7):
            day = start + datetime.timedelta(days=i * 7 + wd)
            if day <= today:
                days.append({"contributionCount": rnd.choice([0, 0, 0, 1, 2, 3, 5, 8]), "date": day.isoformat(), "weekday": wd})
        weeks.append({"contributionDays": days})
    return {"totalContributions": 0, "weeks": weeks}


def main():
    if "--placeholder" in sys.argv:
        OUT.mkdir(exist_ok=True)
        (OUT / "contributions.svg").write_text(contributions_svg(placeholder_calendar(), placeholder=True), encoding="utf-8")
        print("ok: placeholder contribution graph written")
        return
    d = fetch()
    stats, _ = stats_svg(d)
    langs = langs_svg(d)
    graph = contributions_svg(d["contrib"]["contributionCalendar"]) if d["contrib"] else None
    OUT.mkdir(exist_ok=True)
    (OUT / "stats.svg").write_text(stats, encoding="utf-8")
    (OUT / "langs.svg").write_text(langs, encoding="utf-8")
    if graph:
        (OUT / "contributions.svg").write_text(graph, encoding="utf-8")
    print(f"ok: {d['repos']} repos, {len(d['langs'])} languages, contributions={'yes' if d['contrib'] else 'no (no token)'}")


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, KeyError, ValueError) as e:
        sys.exit(f"failed, existing assets left untouched: {e}")
