import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

USER = "imedkablavi"
OUT = Path("dist")
OUT.mkdir(exist_ok=True)
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

user = api(f"https://api.github.com/users/{USER}")
repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=updated")

stars = sum(r.get("stargazers_count", 0) for r in repos)
forks = sum(r.get("forks_count", 0) for r in repos)
langs = Counter()
for repo in repos:
    try:
        data = api(repo["languages_url"])
        for lang, value in data.items():
            langs[lang] += value
    except Exception:
        pass

total_lang = sum(langs.values()) or 1
language_rows = [(k, v / total_lang * 100) for k, v in langs.most_common(8)]


def card(title, body, width=500, height=230):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs><linearGradient id="g" x1="0" x2="1"><stop stop-color="#071018"/><stop offset="1" stop-color="#0d1720"/></linearGradient></defs>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="14" fill="url(#g)" stroke="#263b48"/>
<text x="24" y="38" fill="#36bcf7" font-family="monospace" font-size="20" font-weight="700">{esc(title)}</text>
{body}
</svg>'''

metrics = [
    ("Public Repositories", user.get("public_repos", 0)),
    ("Followers", user.get("followers", 0)),
    ("Total Stars", stars),
    ("Total Forks", forks),
]
metric_svg = "".join(
    f'<text x="28" y="{82+i*34}" fill="#9ca3af" font-family="sans-serif" font-size="15">{esc(label)}</text>'
    f'<text x="455" y="{82+i*34}" text-anchor="end" fill="#e5e7eb" font-family="monospace" font-size="17" font-weight="700">{value}</text>'
    for i, (label, value) in enumerate(metrics)
)
OUT.joinpath("github-stats.svg").write_text(card("GitHub / profile metrics", metric_svg), encoding="utf-8")

palette = ["#36bcf7", "#7dd3fc", "#4ade80", "#a78bfa", "#f59e0b", "#fb7185", "#22d3ee", "#94a3b8"]
rows = []
for i, (lang, pct) in enumerate(language_rows):
    y = 76 + i * 19
    color = palette[i % len(palette)]
    rows.append(f'<rect x="25" y="{y-10}" width="{max(4, pct*4.2):.1f}" height="8" rx="4" fill="{color}"/>')
    rows.append(f'<text x="205" y="{y}" fill="#d1d5db" font-family="monospace" font-size="13">{esc(lang)}</text>')
    rows.append(f'<text x="470" y="{y}" text-anchor="end" fill="#9ca3af" font-family="monospace" font-size="13">{pct:.1f}%</text>')
OUT.joinpath("top-languages.svg").write_text(card("Top languages / public code", "".join(rows)), encoding="utf-8")
