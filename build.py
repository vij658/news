#!/usr/bin/env python3
"""Render data.json -> index.html and checkpoints/checkpoint-NN.html.

Usage: python3 build.py
Edit data.json (shows, episodes, status, checkpoint number), then re-run.
"""
import html
import json
import pathlib

root = pathlib.Path(__file__).resolve().parent
d = json.loads((root / "data.json").read_text(encoding="utf-8"))
e = html.escape

CSS = """
:root{--bg:#fafaf8;--fg:#1c1c1a;--muted:#6b6b66;--card:#fff;--line:#e4e2dc;--accent:#1a5fb4;--ok:#1f7a3d;--warn:#a35a00}
@media(prefers-color-scheme:dark){:root{--bg:#151514;--fg:#ecebe6;--muted:#9a9990;--card:#1f1f1d;--line:#33332f;--accent:#7db3ff;--ok:#6fcf8f;--warn:#f0b35a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 18px 60px}
h1{font-size:24px;margin:0 0 4px}
h2{font-size:19px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:0 0 2px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.sub{color:var(--muted);margin:0 0 18px}
.banner{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--warn);border-radius:8px;padding:12px 14px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
.card.secondary{opacity:.88}
.meta{color:var(--muted);font-size:13px;margin:2px 0 8px}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;border:1px solid var(--line);margin-right:6px}
.ok{color:var(--ok);border-color:var(--ok)}.warn{color:var(--warn);border-color:var(--warn)}
ul{margin:6px 0 6px 18px;padding:0}li{margin:2px 0}
.play{display:inline-block;margin-top:6px;padding:6px 12px;border:1px solid var(--accent);border-radius:8px;font-size:13px}
code{background:var(--line);padding:0 4px;border-radius:4px;font-size:12.5px}
nav a{margin-right:12px;font-size:13px}
"""


def watch(vid):
    return f"https://www.youtube.com/watch?v={vid}"


def render_show(s):
    cls = "card secondary" if s.get("secondary") else "card"
    handle = f' <code>{e(s["handle"])}</code>' if s.get("handle") else ""
    tags = f'<span class="tag {e(s.get("tag", "ok"))}">{e(s["cadence"])}</span>'
    if s.get("tag2"):
        tags += f'<span class="tag warn">{e(s["tag2"])}</span>'
    out = [f'<div class="{cls}">',
           f'<h3>{e(s["title"])} — {e(s["channel"])}{handle}</h3>',
           f'<div class="meta">{tags} {e(s.get("note", ""))}</div><ul>']
    for ep in s["episodes"]:
        length = f' · {e(ep["len"])}' if ep.get("len") else ""
        if ep.get("id"):
            out.append(f'<li><a href="{watch(ep["id"])}">{e(ep["label"])}</a>{length}</li>')
        else:
            out.append(f'<li>{e(ep["label"])}{length}</li>')
    out.append("</ul>")
    if s.get("find"):
        out.append(f'<a href="{e(s["find"])}">{e(s.get("find_label", "Find all episodes"))}</a>')
    out.append("</div>")
    return "\n".join(out)


def render_category(c):
    out = [f'<h2 id="{e(c["id"])}">{e(c["name"])}</h2>']
    if c.get("intro"):
        out.append(f'<p class="meta">{e(c["intro"])}</p>')
    for s in c["shows"]:
        out.append(render_show(s))
    if c.get("excluded"):
        out.append(f'<p class="meta"><strong>Looked at / still open:</strong> {e(c["excluded"])}</p>')
    if c.get("playlist"):
        out.append(f'<p class="meta"><strong>✅ Saved playlist (private):</strong> {e(c["playlist"]["name"])} — {c["playlist"]["videos"]} videos</p>')
    ids = []
    for s in c["shows"]:
        if s.get("secondary"):
            continue
        first = next((ep["id"] for ep in s["episodes"] if ep.get("id")), None)
        if first:
            ids.append(first)
    if ids:
        out.append(f'<a class="play" href="https://www.youtube.com/watch_videos?video_ids={",".join(ids)}">'
                   "▶ Quick-play latest (temporary queue, not a saved playlist)</a>")
    return "\n".join(out)


n = d["checkpoint"]
nav = " ".join(f'<a href="#{e(c["id"])}">{e(c["name"].split("·")[1].strip())}</a>' for c in d["categories"])
gaps = "".join(f"<li>{e(g)}</li>" for g in d["gaps"])
page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Weekly News Playlists — Checkpoint {n}</title>
<style>{CSS}</style></head>
<body><main>
<h1>Weekly News Playlists — Research Checkpoint {n}</h1>
<p class="sub">Saved {e(d["saved"])} · covers the week of {e(d["week"])} · every show below was checked on YouTube itself (title, upload date, length), not taken from web articles.</p>
<p class="meta"><strong><a href="channels.html">→ Channel directory: 33 channels with links, upload days and reliability</a></strong></p>
<nav>{nav}</nav>
<div class="banner"><strong>Status:</strong> {d["status"]}<br><strong>Open gaps:</strong><ul>{gaps}</ul></div>
{"".join(render_category(c) + chr(10) for c in d["categories"])}
</main></body></html>
"""

(root / "index.html").write_text(page, encoding="utf-8")
(root / "checkpoints").mkdir(exist_ok=True)
(root / "checkpoints" / f"checkpoint-{n:02d}.html").write_text(page, encoding="utf-8")
print(f"wrote index.html and checkpoints/checkpoint-{n:02d}.html "
      f"({sum(len(c['shows']) for c in d['categories'])} shows, {len(d['categories'])} categories)")
