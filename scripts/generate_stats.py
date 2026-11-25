"""Fetch GitHub stats via GraphQL and generate SVG cards.

Requires GITHUB_TOKEN env var (provided by Actions default token).
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN", "")
USER = os.environ.get("GITHUB_USER", "Hack-master22")
API = "https://api.github.com/graphql"
OUT = Path(__file__).parent.parent
W = 620

# ── GraphQL ──────────────────────────────────────────────────────────

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date weekday } }
      }
    }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC) {
      nodes { name primaryLanguage { name } languages(first:10, orderBy:{field:SIZE,direction:DESC}) { edges { size node { name } } } }
    }
  }
}
"""


def graphql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


# ── SVG builders ─────────────────────────────────────────────────────

def _style():
    return ('<style>'
            '@media(prefers-color-scheme:dark){.bg{fill:#0d1117}.t1{fill:#c9d1d9}.t2{fill:#848d97}.bar{fill:#c9d1d9}.ln{stroke:#30363d}}'
            '@media(prefers-color-scheme:light){.bg{fill:#ffffff}.t1{fill:#1f2328}.t2{fill:#656d76}.bar{fill:#1f2328}.ln{stroke:#d0d7de}}'
            '</style>')


def stats_svg(total, weeks_data):
    # sparkline from weekly totals (last 52 weeks)
    weekly = []
    for w in weeks_data[-52:]:
        weekly.append(sum(d["contributionCount"] for d in w["contributionDays"]))
    mx = max(weekly) or 1
    spark_w, spark_h = 400, 50
    ox, oy = 200, 80
    points = []
    for i, v in enumerate(weekly):
        x = ox + (i / (len(weekly) - 1)) * spark_w
        y = oy + spark_h - (v / mx) * spark_h
        points.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(points)
    fill_points = f"{ox},{oy + spark_h} " + polyline + f" {ox + spark_w},{oy + spark_h}"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 148" width="{W}">
<defs>{_style()}</defs>
<rect class="bg" width="{W}" height="148" rx="6"/>
<text class="t1" x="20" y="50" font-family="JetBrains Mono,monospace" font-size="36" font-weight="600">
{total}<animate attributeName="opacity" from="0" to="1" dur="0.6s" fill="freeze"/>
</text>
<text class="t2" x="20" y="68" font-family="JetBrains Mono,monospace" font-size="11">contributions in the last year</text>
<polygon points="{fill_points}" fill="currentColor" class="t2" opacity="0.13">
<animate attributeName="opacity" from="0" to="0.13" dur="0.8s" begin="0.3s" fill="freeze"/>
</polygon>
<polyline points="{polyline}" fill="none" stroke="currentColor" class="t2" stroke-width="1.5" opacity="0">
<animate attributeName="opacity" from="0" to="0.6" dur="0.8s" begin="0.3s" fill="freeze"/>
</polyline>
</svg>"""


def streak_svg(current, longest, cur_range, long_range):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 96" width="{W}">
<defs>{_style()}</defs>
<rect class="bg" width="{W}" height="96" rx="6"/>
<line class="ln" x1="310" y1="16" x2="310" y2="80"/>
<text class="t2" x="20" y="32" font-family="JetBrains Mono,monospace" font-size="11">current streak</text>
<text class="t1" x="20" y="58" font-family="JetBrains Mono,monospace" font-size="28" font-weight="600">{current}</text>
<text class="t2" x="20" y="76" font-family="JetBrains Mono,monospace" font-size="10">{cur_range}</text>
<text class="t2" x="330" y="32" font-family="JetBrains Mono,monospace" font-size="11">longest streak</text>
<text class="t1" x="330" y="58" font-family="JetBrains Mono,monospace" font-size="28" font-weight="600">{longest}</text>
<text class="t2" x="330" y="76" font-family="JetBrains Mono,monospace" font-size="10">{long_range}</text>
</svg>"""


def langs_svg(lang_bytes):
    if not lang_bytes:
        return ""
    total = sum(lang_bytes.values())
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: -x[1])[:6]
    h = 30 + len(sorted_langs) * 24
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}">',
        f"<defs>{_style()}</defs>",
        f'<rect class="bg" width="{W}" height="{h}" rx="6"/>',
        f'<text class="t2" x="20" y="22" font-family="JetBrains Mono,monospace" font-size="11">languages by bytes</text>',
    ]
    for i, (lang, b) in enumerate(sorted_langs):
        pct = b / total * 100
        bar_w = pct / 100 * 350
        y = 42 + i * 24
        lines.append(f'<text class="t1" x="20" y="{y}" font-family="JetBrains Mono,monospace" font-size="11">{lang}</text>')
        lines.append(f'<rect class="bar" x="160" y="{y - 10}" width="0" height="12" rx="3" opacity="0.7">'
                     f'<animate attributeName="width" from="0" to="{bar_w:.0f}" dur="0.5s" begin="{0.1 * i:.1f}s" fill="freeze"/></rect>')
        lines.append(f'<text class="t2" x="{165 + 350}" y="{y}" font-family="JetBrains Mono,monospace" font-size="10">{pct:.1f}%</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def compute_streaks(weeks_data):
    days = []
    for w in weeks_data:
        for d in w["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))
    # current streak (from today backwards)
    current = 0
    cur_start = cur_end = ""
    for date, count in reversed(days):
        if count > 0:
            current += 1
            cur_start = date
            if not cur_end:
                cur_end = date
        else:
            if current > 0:
                break
    # longest streak
    longest = 0
    long_start = long_end = ""
    streak = 0
    s_start = ""
    for date, count in days:
        if count > 0:
            streak += 1
            if streak == 1:
                s_start = date
            if streak > longest:
                longest = streak
                long_start = s_start
                long_end = date
        else:
            streak = 0
    return current, longest, f"{cur_start} – {cur_end}" if cur_start else "–", f"{long_start} – {long_end}" if long_start else "–"


def main():
    if not TOKEN:
        print("GITHUB_TOKEN not set, generating placeholder SVGs")
        (OUT / "stats.svg").write_text(stats_svg(0, [{"contributionDays": [{"contributionCount": 0}]}] * 52), encoding="utf-8")
        (OUT / "streak.svg").write_text(streak_svg(0, 0, "–", "–"), encoding="utf-8")
        (OUT / "langs.svg").write_text(langs_svg({"JavaScript": 60, "CSS": 30, "HTML": 10}), encoding="utf-8")
        return

    data = graphql(QUERY, {"login": USER})
    user = data["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    total = cal["totalContributions"]
    weeks = cal["weeks"]

    # language bytes
    lang_bytes = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            lang_bytes[name] = lang_bytes.get(name, 0) + edge["size"]

    cur, lon, cr, lr = compute_streaks(weeks)

    (OUT / "stats.svg").write_text(stats_svg(total, weeks), encoding="utf-8")
    (OUT / "streak.svg").write_text(streak_svg(cur, lon, cr, lr), encoding="utf-8")
    (OUT / "langs.svg").write_text(langs_svg(lang_bytes), encoding="utf-8")
    print(f"stats: {total} contributions, streak: {cur}/{lon}, langs: {len(lang_bytes)}")


if __name__ == "__main__":
    main()
