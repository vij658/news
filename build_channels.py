#!/usr/bin/env python3
"""Render channels.json -> channels.html and channels.csv.

Usage: python3 build_channels.py
"""
import csv
import html
import json
import pathlib
import urllib.parse

root = pathlib.Path(__file__).resolve().parent
d = json.loads((root / "channels.json").read_text(encoding="utf-8"))
e = html.escape
YT = "https://www.youtube.com"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

CSS = """
:root{--bg:#fafaf8;--fg:#1c1c1a;--muted:#6b6b66;--card:#fff;--line:#e4e2dc;--accent:#1a5fb4;--ok:#1f7a3d;--warn:#a35a00;--blue:#1a5fb4;--grey:#6b6b66}
@media(prefers-color-scheme:dark){:root{--bg:#151514;--fg:#ecebe6;--muted:#9a9990;--card:#1f1f1d;--line:#33332f;--accent:#7db3ff;--ok:#6fcf8f;--warn:#f0b35a;--blue:#7db3ff;--grey:#9a9990}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 18px 60px}
h1{font-size:24px;margin:0 0 4px}
h2{font-size:19px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:0 0 2px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.sub{color:var(--muted);margin:0 0 18px}
.box{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:10px 0}
.meta{color:var(--muted);font-size:13px;margin:2px 0 6px}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;border:1px solid var(--line);margin-right:6px}
.t-core{color:var(--ok);border-color:var(--ok)}.t-seasonal{color:var(--blue);border-color:var(--blue)}
.t-backup{color:var(--warn);border-color:var(--warn)}.t-small{color:var(--grey);border-color:var(--grey)}
.links a{display:inline-block;margin:4px 12px 0 0;font-size:13px}
code{background:var(--line);padding:0 4px;border-radius:4px;font-size:12.5px}
nav a{margin-right:12px;font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}
th{background:var(--card)}
textarea{width:100%;height:170px;font:12px/1.4 ui-monospace,Menlo,monospace;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:8px}
ul{margin:6px 0 6px 18px;padding:0}li{margin:2px 0}
"""


def urls(c):
    h = c["handle"]
    home = f"{YT}/{h}"
    vids = f"{home}/videos"
    kw = c.get("kw") or ""
    find = f"{home}/search?query={urllib.parse.quote(kw)}" if kw else vids
    return home, vids, find


def card(c, tiers):
    home, vids, find = urls(c)
    tier = c["tier"]
    seen = f'<a href="{YT}/watch?v={e(c["seen"])}">Example episode</a>' if c.get("seen") else ""
    extra = "".join(f'<a href="{e(x["url"])}">{e(x["label"])}</a>' for x in c.get("extra", []))
    find_label = "Find this week's episode" if c.get("kw") else "Newest videos"
    return (
        '<div class="card">'
        f'<h3>{e(c["name"])} <code>{e(c["handle"])}</code></h3>'
        f'<div class="meta"><span class="tag t-{e(tier)}" title="{e(tiers[tier])}">{e(tier)}</span>'
        f'{e(c["show"])} · {e(c["when"])}</div>'
        f'<div>{e(c["note"])}</div>'
        f'<div class="links"><a href="{e(home)}">Channel</a><a href="{e(vids)}">All videos</a>'
        f'<a href="{e(find)}">{find_label}</a>{extra}{seen}</div>'
        "</div>"
    )


cats = d["categories"]
nav = " ".join(f'<a href="#{e(c["id"])}">{e(c["name"].split("·")[1].strip())}</a>' for c in cats)
legend = "".join(f'<span class="tag t-{k}">{k}</span> {e(v.split(": ", 1)[1])}<br>' for k, v in d["tiers"].items())

body = []
for c in cats:
    body.append(f'<h2 id="{e(c["id"])}">{e(c["name"])}</h2>')
    body.extend(card(ch, d["tiers"]) for ch in c["channels"])

# check-by-day table
by_day = {k: [] for k in DAYS}
for c in cats:
    for ch in c["channels"]:
        for day in ch.get("days", []):
            by_day[day].append(f'{ch["show"].split(" (")[0]} ({c["name"].split("·")[1].strip()})')
rows = "".join(f"<tr><th>{k}</th><td>{e('; '.join(v)) or '—'}</td></tr>" for k, v in by_day.items())
no_day = [ch["show"].split(" (")[0] for c in cats for ch in c["channels"] if not ch.get("days")]

all_urls = "\n".join(
    f'{c["name"].split("·")[1].strip()} | {ch["name"]} | {YT}/{ch["handle"]}' for c in cats for ch in c["channels"]
)
total = sum(len(c["channels"]) for c in cats)
not_weekly = "".join(f"<li>{e(x)}</li>" for x in d["not_weekly"])

page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Weekly News Channels</title>
<style>{CSS}</style></head>
<body><main>
<h1>Weekly News Channels — {total} channels in 8 categories</h1>
<p class="sub">Saved {e(d["saved"])} · each channel was seen posting a weekly summary on YouTube itself. Use "Find this week's episode" to jump to the newest one. See also <a href="index.html">the research page with episode links</a>.</p>
<nav>{nav}</nav>
<div class="box">{legend}</div>
{"".join(body)}
<h2 id="byday">Which day to check</h2>
<table>{rows}</table>
<p class="meta">No fixed day (check on the weekend): {e("; ".join(no_day))}.</p>
<h2 id="skip">Checked and not weekly</h2>
<ul>{not_weekly}</ul>
<h2 id="plain">Plain list (copy and paste)</h2>
<textarea readonly>{e(all_urls)}</textarea>
<p class="meta">The same list is in <a href="channels.csv">channels.csv</a>, with search links, upload day and reliability.</p>
</main></body></html>
"""
(root / "channels.html").write_text(page, encoding="utf-8")

with (root / "channels.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["category", "channel", "handle", "show", "when", "reliability", "channel_url", "find_weekly_url", "note"])
    for c in cats:
        for ch in c["channels"]:
            home, vids, find = urls(ch)
            w.writerow([c["name"].split("·")[1].strip(), ch["name"], ch["handle"], ch["show"], ch["when"],
                        ch["tier"], home, find, ch["note"]])
print(f"wrote channels.html and channels.csv ({total} channels)")
