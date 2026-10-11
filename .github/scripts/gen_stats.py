#!/usr/bin/env python3
"""Fetch live GitHub stats and render an artistic stats SVG card.
Runs locally (unauthenticated) or in GitHub Actions (GITHUB_TOKEN).
Output: assets/stats.svg (relative to repo root when run in Actions)."""
import collections
import datetime
import json
import os
import random
import sys
import urllib.request

USER = "amkkoussay"
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/card-stats.svg"

TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats-card"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


user = get(f"https://api.github.com/users/{USER}")
repos = []
page = 1
while True:
    batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner")
    repos.extend(batch)
    if len(batch) < 100:
        break
    page += 1

own = [r for r in repos if not r.get("fork")]
stars = sum(r["stargazers_count"] for r in repos)
forks = sum(r["forks_count"] for r in repos)

lang_bytes = collections.Counter()
for r in own:
    try:
        lang_bytes.update(get(r["languages_url"]))
    except Exception:
        pass
top = lang_bytes.most_common(5)
total_bytes = sum(lang_bytes.values()) or 1

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "HTML": "#e34c26",
    "CSS": "#563d7c", "TypeScript": "#3178c6", "Java": "#b07219",
    "C++": "#f34b7d", "C": "#555555", "Shell": "#89e051",
    "Dockerfile": "#384d54", "Vue": "#41b883", "PHP": "#4F5D95",
    "Go": "#00ADD8", "Rust": "#dea584", "Kotlin": "#A97BFF",
    "Jupyter Notebook": "#DA5B0B", "SCSS": "#c6538c", "Ruby": "#701516",
    "Swift": "#F05138", "C#": "#178600",
}
langs = [
    {"name": n, "pct": b / total_bytes, "color": LANG_COLORS.get(n, "#8b9bb4")}
    for n, b in top
]

today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

W, H = 1200, 560
random.seed(21)
stars_bg = "\n".join(
    f'<circle cx="{random.uniform(15, W-15):.1f}" cy="{random.uniform(10, 250):.1f}" '
    f'r="{random.choice([0.7, 1.0, 1.4, 1.9])}" fill="#dfe9ff" opacity="{random.uniform(0.25, 0.9):.2f}"/>'
    for _ in range(60)
)

def stat(x, y, value, label):
    return (
        f'<text x="{x}" y="{y}" font-family="Georgia, \'Times New Roman\', serif" font-size="54" '
        f'font-weight="bold" fill="#f2f6ff">{value}</text>\n'
        f'<text x="{x}" y="{y+30}" font-family="Georgia, \'Times New Roman\', serif" font-size="14" '
        f'fill="#8fa8d8" letter-spacing="2">{label}</text>'
    )

bars = []
by = 178
for l in langs:
    pct = l["pct"]
    pct_label = f"{pct:.0%}" if pct >= 0.005 else "&lt;1%"
    bars.append(
        f'<text x="620" y="{by}" font-family="Georgia, \'Times New Roman\', serif" font-size="20" fill="#dfe9ff">{l["name"]}</text>\n'
        f'<text x="1130" y="{by}" text-anchor="end" font-family="\'DejaVu Sans Mono\', monospace" font-size="19" fill="#8fa8d8">{pct_label}</text>\n'
        f'<rect x="620" y="{by+12}" width="510" height="14" rx="7" fill="#16294f"/>\n'
        f'<rect x="620" y="{by+12}" width="{510*pct:.1f}" height="14" rx="7" fill="{l["color"]}"/>\n'
    )
    by += 64
bars_svg = "\n".join(bars)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Live GitHub stats for {USER}">
<defs>
<linearGradient id="sky2" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#050b1c"/>
<stop offset="0.6" stop-color="#0c2148"/>
<stop offset="1" stop-color="#0a1a3a"/>
</linearGradient>
<radialGradient id="vig2" cx="0.5" cy="0.4" r="0.9">
<stop offset="0.6" stop-color="#000" stop-opacity="0"/>
<stop offset="1" stop-color="#01040c" stop-opacity="0.55"/>
</radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#sky2)"/>
{stars_bg}
<path d="M0,505 L140,440 L260,485 L400,430 L540,490 L700,445 L860,492 L1000,448 L1200,490 L1200,560 L0,560 Z" fill="#0a1836" opacity="0.9"/>
<rect width="{W}" height="{H}" fill="url(#vig2)"/>
<text x="70" y="66" font-family="Georgia, 'Times New Roman', serif" font-size="16" fill="#8fa8d8" letter-spacing="4">LIVE FROM GITHUB</text>
<text x="1130" y="66" text-anchor="end" font-family="'DejaVu Sans Mono', monospace" font-size="14" fill="#5f7bb0">auto-refreshed daily</text>
<line x1="70" y1="86" x2="1130" y2="86" stroke="#27406e" stroke-width="1"/>
<text x="70" y="140" font-family="Georgia, 'Times New Roman', serif" font-size="16" fill="#8fa8d8" letter-spacing="4">ACTIVITY</text>
{stat(70, 205, stars, "TOTAL STARS")}
{stat(330, 205, forks, "FORKS")}
{stat(70, 330, user["public_repos"], "PUBLIC REPOS")}
{stat(330, 330, user["followers"], "FOLLOWERS")}
<line x1="560" y1="120" x2="560" y2="400" stroke="#27406e" stroke-width="1"/>
<text x="620" y="140" font-family="Georgia, 'Times New Roman', serif" font-size="16" fill="#8fa8d8" letter-spacing="4">TOP LANGUAGES</text>
{bars_svg}
<text x="70" y="528" font-family="'DejaVu Sans Mono', monospace" font-size="13" fill="#5f7bb0">updated {today} UTC · github.com/{USER}</text>
</svg>
"""
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: {stars} stars, {forks} forks, {len(langs)} langs")
