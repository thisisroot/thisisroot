#!/usr/bin/env python3
"""
Dot-matrix profile generator for github.com/thisisroot.

Display type is drawn as LED dots from a 5x7 bitmap font (scripts/dotfont.py),
so it renders identically everywhere. Every graphic is built twice, for
GitHub's dark and light themes.

    python scripts/profile.py static               # assets/*.svg
    python scripts/profile.py telemetry --out dist # live stats (needs GITHUB_TOKEN)

Edit the CONTENT section to change what the profile says.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import urllib.request
from xml.sax.saxutils import escape as esc

from dotfont import FONT

ROOT = pathlib.Path(__file__).resolve().parent.parent
USER = os.environ.get("GH_USER", "thisisroot")
YEAR = dt.date.today().year
W = 900
MONO = "ui-monospace, 'SF Mono', 'JetBrains Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# ───────────────────────────── content ─────────────────────────────
TAGLINE = "SYSTEMS ENGINEERING  /  CROSS-PLATFORM APPS  /  NETWORKED SOFTWARE"
SPECS = [
    ("01  SYSTEMS", "Rust · backend · crypto protocols"),
    ("02  APPLICATIONS", "Flutter · Dart · cross-platform"),
    ("03  PROTOCOLS", "REST · WebSockets · OpenAPI"),
]
TICKER = "NOW BUILDING  *  TRUST  -  SELF-HOSTED MESSENGER  *  QFORGE  -  INVERSE MATERIALS DESIGN  *  ZDM  -  DOWNLOAD MANAGER  *  "
MOTTO = "LESS MAGIC. MORE OWNERSHIP."

PROJECTS = [  # slug, name, description lines, tags
    ("hilbertforge", "HILBERT FORGE",
     ["QForge: inverse materials design. Give it target properties,",
      "get back candidate crystal structures, checked and analysed."],
     ["RUST", "PYTHON", "ML"]),
    ("zdm", "ZDM",
     ["Segmented download manager. The best download manager ever.",
      "zeddm.ir"],
     ["RUST", "REACT", "TYPESCRIPT"]),
    ("trust", "TRUST",
     ["Self-hosted, cross-platform messenger. Flutter client, Rust",
      "server, MLS end-to-end encryption in progress."],
     ["RUST", "FLUTTER", "MLS"]),
]

THEMES = {
    "dark": dict(bg="#0A0A0A", panel="#111111", fg="#EDEDE6", muted="#86867F",
                 unlit="#1A1A1A", grid="#161616", rule="#262626", accent="#FF3B1F"),
    "light": dict(bg="#F3F2ED", panel="#EAE9E3", fg="#141414", muted="#6E6E68",
                  unlit="#E0DFD8", grid="#E6E5DF", rule="#D3D2CB", accent="#E8341C"),
}

# extra glyphs for this design
FONT.update({
    "↗": ".####|...##|..#.#|.#..#|#....|.....|.....".split("|"),
    "*": ".....|..#..|#.#.#|.###.|#.#.#|..#..|.....".split("|"),
})


# ───────────────────────────── dot-matrix type ─────────────────────────────
def tw(s: str, sc: int) -> int:
    return (len(s) * 6 - 1) * sc if s else 0


def snap(v: float, sc: int) -> int:
    return int(round(v / sc)) * sc


def dm_d(s: str, x: int, y: int, sc: int) -> str:
    out = []
    for i, ch in enumerate(s.upper()):
        rows = FONT.get(ch, FONT[" "])
        ox = x + i * 6 * sc
        for ry, row in enumerate(rows):
            cx = 0
            while cx < len(row):
                if row[cx] == "#":
                    st = cx
                    while cx < len(row) and row[cx] == "#":
                        cx += 1
                    out.append(f"M{ox + st * sc} {y + ry * sc}h{(cx - st) * sc}v{sc}h-{(cx - st) * sc}z")
                else:
                    cx += 1
    return "".join(out)


class Doc:
    """Collects dot patterns so each (scale, colour) pair is defined once."""

    def __init__(self, t: dict):
        self.t, self.pats = t, {}

    def pat(self, sc: int, colour: str, r: float = 0.4) -> str:
        key = f"p{sc}_{colour.strip('#')}_{int(r * 100)}"
        self.pats[key] = (f'<pattern id="{key}" width="{sc}" height="{sc}" patternUnits="userSpaceOnUse">'
                          f'<circle cx="{sc / 2}" cy="{sc / 2}" r="{sc * r:.2f}" fill="{colour}"/></pattern>')
        return f"url(#{key})"

    def dm(self, s, x, y, sc, colour, anchor="start", unlit=False, extra=""):
        """Dot-matrix text. (x, y) = top-left; snapped to the dot grid."""
        if anchor == "middle":
            x -= tw(s, sc) / 2
        elif anchor == "end":
            x -= tw(s, sc)
        x, y = snap(x, sc), snap(y, sc)
        bg = ""
        if unlit:  # the panel of dark LEDs behind the lit ones
            bg = (f'<rect x="{x - sc}" y="{y - sc}" width="{tw(s, sc) + 2 * sc}" height="{9 * sc}" '
                  f'fill="{self.pat(sc, self.t["unlit"])}"/>')
        return bg + f'<path d="{dm_d(s, x, y, sc)}" fill="{self.pat(sc, colour)}" {extra}/>'

    def mono(self, s, x, y, size, colour, anchor="start", ls=0, weight=400):
        return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" font-weight="{weight}" '
                f'letter-spacing="{ls}" fill="{colour}" text-anchor="{anchor}">{esc(s)}</text>')

    def svg(self, h, title, body, grid=True):
        t = self.t
        gridpat = (f'<pattern id="bggrid" width="12" height="12" patternUnits="userSpaceOnUse">'
                   f'<circle cx="6" cy="6" r="1" fill="{t["grid"]}"/></pattern>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
                f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
                f'<defs>{gridpat}{"".join(self.pats.values())}'
                f'<clipPath id="card"><rect width="{W}" height="{h}" rx="18"/></clipPath></defs>'
                f'<g clip-path="url(#card)"><rect width="{W}" height="{h}" fill="{t["bg"]}"/>'
                + (f'<rect width="{W}" height="{h}" fill="url(#bggrid)"/>' if grid else "")
                + body + "</g>"
                f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="17.5" fill="none" stroke="{t["rule"]}"/>'
                "</svg>\n")


def led(d: Doc, x, y, r=4.5):
    """Pulsing red status LED."""
    a = d.t["accent"]
    return (f'<circle cx="{x}" cy="{y}" r="{r * 2.2}" fill="{a}" opacity=".15">'
            f'<animate attributeName="opacity" values=".25;0;.25" dur="2.4s" repeatCount="indefinite"/></circle>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{a}">'
            f'<animate attributeName="opacity" values="1;.35;1" dur="2.4s" repeatCount="indefinite"/></circle>')


# ───────────────────────────── hero ─────────────────────────────
def hero(t) -> str:
    d, H, px = Doc(t), 420, 54
    b = [
        d.mono(f"{USER.upper()}  /  PROFILE", px, 52, 12, t["muted"], ls=2.5),
        led(d, W - px - 220, 47.5),
        d.mono("ONLINE", W - px - 204, 52, 12, t["fg"], ls=2.5),
        d.mono("EST. 2017", W - px, 52, 12, t["muted"], anchor="end", ls=2.5),
    ]
    # title: lit dots over an unlit LED panel; a cursor blinks after it
    sc, title = 12, "THISISROOT"
    tx = snap((W - tw(title + " ", sc)) / 2, sc)
    b.append(d.dm(title + " ", tx, 96, sc, t["fg"], unlit=True))
    cur_x = tx + len(title) * 6 * sc
    b.append(f'<rect x="{cur_x}" y="{snap(96, sc)}" width="{5 * sc}" height="{7 * sc}" '
             f'fill="{d.pat(sc, t["accent"])}"><animate attributeName="opacity" values="1;0" '
             f'dur="1.1s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    b.append(d.mono(TAGLINE, px, 232, 13, t["muted"], ls=1.5))
    b.append(f'<path d="M{px} 258H{W - px}" stroke="{t["rule"]}"/>')
    col = (W - 2 * px) / len(SPECS)
    for i, (label, value) in enumerate(SPECS):
        x = px + i * col
        b.append(d.mono(label, x, 290, 11, t["accent"], ls=2))
        b.append(d.mono(value, x, 314, 13.5, t["fg"]))

    # scrolling LED ticker
    tsc, band = 3, 72
    ty = snap(H - band / 2 - 3.5 * tsc, tsc)
    span = len(TICKER) * 6 * tsc
    reel = d.dm(TICKER * 3, 0, ty, tsc, t["accent"])
    b.append(f'<rect x="0" y="{H - band}" width="{W}" height="{band}" fill="{t["panel"]}"/>'
             f'<path d="M0 {H - band}H{W}" stroke="{t["rule"]}"/>'
             f'<rect x="0" y="{ty - tsc}" width="{W}" height="{9 * tsc}" fill="{d.pat(tsc, t["unlit"])}"/>'
             f'<g><animateTransform attributeName="transform" type="translate" values="0 0;-{span} 0" '
             f'dur="{span / 45:.1f}s" repeatCount="indefinite"/>{reel}</g>')
    return d.svg(H, f"{USER} — systems engineering, cross-platform apps, networked software", "".join(b))


# ───────────────────────────── projects ─────────────────────────────
def project(t, i, name, lines, tags) -> str:
    d, H = Doc(t), 150
    b = [d.dm(f"{i + 1:02d}", 40, 40, 4, t["accent"]),
         d.dm(name, 120, 35, 5, t["fg"])]
    for j, line in enumerate(lines):
        b.append(d.mono(line, 120, 101 + j * 22, 14, t["muted"] if j else t["muted"]))
    # tags, right-aligned pills (approximate mono width: 0.62em)
    x = W - 92
    for tag in reversed(tags):
        w = len(tag) * 11 * 0.62 + len(tag) * 1.5 + 22
        x -= w
        b.append(f'<rect x="{x:.1f}" y="34" width="{w:.1f}" height="24" rx="12" fill="none" stroke="{t["rule"]}"/>'
                 + d.mono(tag, x + w / 2, 50, 11, t["fg"], anchor="middle", ls=1.5))
        x -= 8
    b.append(d.dm("↗", W - 70, 35, 4, t["accent"]))
    return d.svg(H, f"{name} — {' '.join(lines)}", "".join(b), grid=False)


# ───────────────────────────── footer ─────────────────────────────
def footer(t) -> str:
    d, H = Doc(t), 96
    b = [d.dm(MOTTO, 40, 36, 3, t["fg"]),
         d.mono(f"© {YEAR}  {USER.upper()}", W - 40, 52, 12, t["muted"], anchor="end", ls=2)]
    return d.svg(H, MOTTO, "".join(b))


# ───────────────────────────── telemetry (live) ─────────────────────────────
def gql(query: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": f"{USER}-profile"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]


def fetch(token: str) -> dict:
    u = gql(f"""{{ user(login: "{USER}") {{
      pullRequests {{ totalCount }}
      contributionsCollection {{
        contributionYears totalCommitContributions
        contributionCalendar {{ totalContributions
          weeks {{ contributionDays {{ contributionLevel date }} }} }} }} }} }}""", token)["user"]
    cc = u["contributionsCollection"]
    years = cc["contributionYears"]
    aliases = " ".join(f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
                       f'{{ contributionCalendar {{ totalContributions }} }}' for y in years)
    per = gql(f'{{ user(login: "{USER}") {{ {aliases} }} }}', token)["user"]
    return {
        "stats": [
            ("CONTRIBUTIONS / 1Y", cc["contributionCalendar"]["totalContributions"]),
            ("COMMITS / 1Y", cc["totalCommitContributions"]),
            ("PULL REQUESTS", u["pullRequests"]["totalCount"]),
            ("ALL-TIME", sum(v["contributionCalendar"]["totalContributions"] for v in per.values())),
        ],
        "weeks": [[day["contributionLevel"] for day in w["contributionDays"]]
                  for w in cc["contributionCalendar"]["weeks"]],
    }


LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def telemetry(t, data) -> str:
    d, px = Doc(t), 54
    weeks = data["weeks"][-53:]
    step = 15
    gx = (W - (len(weeks) - 1) * step) / 2
    gy = 196
    H = gy + 6 * step + 64
    b = [d.mono("TELEMETRY", px, 52, 12, t["muted"], ls=2.5),
         led(d, px + 126, 47.5, 3.5),
         d.mono(f"UPDATED {dt.date.today().isoformat()}", W - px, 52, 12, t["muted"], anchor="end", ls=2.5)]
    col = (W - 2 * px) / len(data["stats"])
    for i, (label, val) in enumerate(data["stats"]):
        x = px + i * col
        b.append(d.dm(str(val), x, 82, 6, t["fg"]))
        b.append(d.mono(label, x, 150, 11, t["accent"] if i == 0 else t["muted"], ls=2))
    b.append(f'<path d="M{px} 172H{W - px}" stroke="{t["rule"]}"/>')
    op = {0: None, 1: .35, 2: .6, 3: .82, 4: 1}
    for wi, week in enumerate(weeks):
        dots = []
        for di, lvl in enumerate(week):
            lv = LEVEL.get(lvl, 0)
            cx, cy = gx + wi * step, gy + di * step
            if lv == 0:
                dots.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="4.6" fill="{t["unlit"]}"/>')
            else:
                dots.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="4.6" fill="{t["accent"]}" fill-opacity="{op[lv]}"/>')
        b.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{.2 + wi * .025:.3f}s" fill="freeze"/>'
                 + "".join(dots) + "</g>")
    b.append(d.mono("LAST 12 MONTHS", px, H - 26, 11, t["muted"], ls=2))
    legend_x = W - px - 50 - 5 * 15
    b.append(d.mono("LESS", legend_x - 12, H - 26, 11, t["muted"], anchor="end", ls=2))
    for k in range(5):
        fill = (f'fill="{t["unlit"]}"' if k == 0 else f'fill="{t["accent"]}" fill-opacity="{op[k]}"')
        b.append(f'<circle cx="{legend_x + k * 15 + 4}" cy="{H - 30}" r="4.6" {fill}/>')
    b.append(d.mono("MORE", W - px, H - 26, 11, t["muted"], anchor="end", ls=2))
    return d.svg(H, f"Telemetry — GitHub activity for {USER}", "".join(b))


# ───────────────────────────── main ─────────────────────────────
def write(path: pathlib.Path, svg: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8", newline="\n")
    print(f"wrote {path} ({len(svg) // 1024} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["static", "telemetry"])
    ap.add_argument("--out", default="dist")
    a = ap.parse_args()
    if a.mode == "static":
        A = ROOT / "assets"
        for name, t in THEMES.items():
            write(A / f"hero-{name}.svg", hero(t))
            write(A / f"footer-{name}.svg", footer(t))
            for i, (slug, pname, lines, tags) in enumerate(PROJECTS):
                write(A / f"project-{slug}-{name}.svg", project(t, i, pname, lines, tags))
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is not set")
        data = fetch(token)
        for name, t in THEMES.items():
            write(pathlib.Path(a.out) / f"telemetry-{name}.svg", telemetry(t, data))


if __name__ == "__main__":
    main()
