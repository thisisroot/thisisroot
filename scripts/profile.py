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

# The stack panel: rows of slots. Empty slots ("") render as open sockets.
STACK = [
    ("LANGUAGES", ["RUST", "DART", "GO", "TYPESCRIPT", "PYTHON"]),
    ("FRAMEWORKS", ["FLUTTER", "AXUM", "REACT", "DJANGO", ""]),
    ("PROTOCOLS", ["REST", "WEBSOCKETS", "OPENAPI", "JSON SCHEMA", "MLS"]),
    ("TOOLING", ["DOCKER", "POSTGRESQL", "LINUX", "GIT", "NEOVIM"]),
]
# Items the selector cycles through: item -> (what it's for, where it's used)
STACK_NOTES = {
    "RUST": ("Primary language. Servers, protocol and cryptography cores.",
             "TRUST SERVER  ·  ZDM  ·  QFORGE CORE"),
    "FLUTTER": ("One codebase for mobile, desktop and web clients.",
                "TRUST CLIENT"),
    "WEBSOCKETS": ("Realtime delivery over versioned, schema-first contracts.",
                   "TRUST PROTOCOL"),
    "MLS": ("Group end-to-end encryption through one shared Rust core.",
            "TRUST  ·  IN PROGRESS"),
    "AXUM": ("HTTP services and job orchestration in Rust.",
             "QFORGE CORE"),
    "PYTHON": ("Machine learning and materials-science bridge.",
               "QFORGE"),
    "REACT": ("Desktop interface and landing pages.",
              "ZDM"),
    "DOCKER": ("Self-hosting as a first-class deployment path.",
               "TRUST DEPLOY"),
}

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


# ───────────────────────────── stack inventory ─────────────────────────────
def cycle(i: int, n: int, period: float) -> str:
    """Show element i of n during its slice of a repeating period."""
    a, b = i / n, (i + 1) / n
    if i == 0:
        vals, kts = "1;0", f"0;{b:.4f}"
    elif i == n - 1:
        vals, kts = "0;1", f"0;{a:.4f}"
    else:
        vals, kts = "0;1;0", f"0;{a:.4f};{b:.4f}"
    return (f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" '
            f'dur="{period}s" calcMode="discrete" repeatCount="indefinite"/>')


def stack(t) -> str:
    d, px = Doc(t), 54
    x0, y0, sw, sh, gx, gy = px + 150, 84, 120, 44, 10.5, 10
    slots = {}
    b = [d.mono("STACK  /  INVENTORY", px, 52, 12, t["muted"], ls=2.5)]
    filled = sum(1 for _, items in STACK for it in items if it)
    total = sum(len(items) for _, items in STACK)
    b.append(d.mono(f"SLOTS {filled}/{total}", W - px, 52, 12, t["muted"], anchor="end", ls=2.5))
    for r, (label, items) in enumerate(STACK):
        y = y0 + r * (sh + gy)
        b.append(d.mono(label, px, y + sh / 2 + 4, 11, t["muted"], ls=2))
        for c, item in enumerate(items):
            x = x0 + c * (sw + gx)
            if not item:
                b.append(f'<rect x="{x}" y="{y}" width="{sw}" height="{sh}" rx="8" fill="none" '
                         f'stroke="{t["rule"]}" stroke-dasharray="3 4"/>')
                continue
            slots[item] = (x, y)
            b.append(f'<rect x="{x}" y="{y}" width="{sw}" height="{sh}" rx="8" fill="{t["panel"]}" stroke="{t["rule"]}"/>'
                     + d.mono(item, x + sw / 2, y + sh / 2 + 4.5, 12, t["fg"], anchor="middle", ls=1))
    feat = [k for k in STACK_NOTES if k in slots]
    n = len(feat)
    period = 3.2 * n
    pos = ";".join(f"{slots[k][0]} {slots[k][1]}" for k in feat)
    kts = ";".join(f"{i / n:.4f}" for i in range(n))
    b.append(f'<g><animateTransform attributeName="transform" type="translate" values="{pos}" keyTimes="{kts}" '
             f'dur="{period}s" calcMode="discrete" repeatCount="indefinite"/>'
             f'<rect x="-3" y="-3" width="{sw + 6}" height="{sh + 6}" rx="10" fill="none" stroke="{t["accent"]}" stroke-width="2"/>'
             f'<circle cx="{sw - 10}" cy="10" r="3" fill="{t["accent"]}"/></g>')
    py = y0 + len(STACK) * (sh + gy) + 14
    ph = 104
    b.append(f'<rect x="{px}" y="{py}" width="{W - 2 * px}" height="{ph}" rx="12" fill="{t["panel"]}" stroke="{t["rule"]}"/>')
    for i, k in enumerate(feat):
        what, where = STACK_NOTES[k]
        pips = "".join(f'<circle cx="{W - px - 24 - (n - 1 - j) * 14}" cy="{py + 26}" r="3.5" '
                       f'fill="{t["accent"] if j == i else t["unlit"]}"/>' for j in range(n))
        b.append(f"<g>{cycle(i, n, period)}"
                 + d.dm(k, px + 24, py + 18, 3, t["fg"])
                 + d.mono(what, px + 24, py + 66, 14, t["fg"])
                 + d.mono("USED IN  ·  " + where, px + 24, py + 88, 11, t["accent"], ls=2)
                 + pips + "</g>")
    return d.svg(py + ph + 34, "Stack — languages, frameworks, protocols and tooling", "".join(b))


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


def blend(c: str, bg: str, a: float) -> str:
    """Solid colour equal to `c` at opacity `a` over `bg`."""
    f = lambda h: [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(y + (x - y) * a):02X}" for x, y in zip(f(c), f(bg)))


def snake_embed(t, svg: str, x0: float, x1: float, y: float, levels: list[str]) -> tuple[str, float]:
    """Nest a Platane/snk SVG, recoloured to the theme with round LED cells.
    The cell grid (which starts at viewBox x=0) is fitted between x0 and x1."""
    open_end = svg.index(">", svg.index("<svg")) + 1
    head, inner = svg[:open_end], svg[open_end:svg.rindex("</svg>")]
    vb = head.split('viewBox="')[1].split('"')[0]
    minx, _, vw, vh = (float(v) for v in vb.split())
    grid_w = vw + 2 * minx  # snk pads the grid symmetrically
    k = (x1 - x0) / grid_w
    x, vw, vh = x0 + minx * k, vw * k, vh * k
    vars_ = (f"--cb:transparent;--cs:{t['fg']};--ce:{t['unlit']};"
             + "".join(f"--c{i}:{c};" for i, c in enumerate(levels)))
    style = "<style>.c{rx:6px;ry:6px;stroke:none}</style>"
    return (f'<svg x="{x:.1f}" y="{y}" width="{vw:.1f}" height="{vh:.1f}" viewBox="{vb}" style="{vars_}">'
            f"{inner}{style}</svg>"), vh


def telemetry(t, data, snake_svg: str | None = None) -> str:
    d, px = Doc(t), 54
    levels = [t["unlit"]] + [blend(t["accent"], t["bg"], a) for a in (.35, .6, .82, 1)]
    b = [d.mono("TELEMETRY", px, 52, 12, t["muted"], ls=2.5),
         led(d, px + 126, 47.5, 3.5),
         d.mono(f"UPDATED {dt.date.today().isoformat()}", W - px, 52, 12, t["muted"], anchor="end", ls=2.5)]
    col = (W - 2 * px) / len(data["stats"])
    for i, (label, val) in enumerate(data["stats"]):
        x = px + i * col
        b.append(d.dm(str(val), x, 82, 6, t["fg"]))
        b.append(d.mono(label, x, 150, 11, t["accent"] if i == 0 else t["muted"], ls=2))
    b.append(f'<path d="M{px} 172H{W - px}" stroke="{t["rule"]}"/>')

    if snake_svg:  # the snake eats the contribution graph
        nested, vh = snake_embed(t, snake_svg, px, W - px, 180, levels)
        b.append(nested)
        H = round(180 + vh + 36)
        caption = "LAST 12 MONTHS  ·  SNAKE.EXE"
    else:  # static fallback: plain dot calendar
        weeks, step, gy = data["weeks"][-53:], 15, 196
        gx = (W - (len(weeks) - 1) * step) / 2
        for wi, week in enumerate(weeks):
            b.append("".join(
                f'<circle cx="{gx + wi * step:.1f}" cy="{gy + di * step}" r="4.6" fill="{levels[LEVEL.get(lv, 0)]}"/>'
                for di, lv in enumerate(week)))
        H = gy + 6 * step + 64
        caption = "LAST 12 MONTHS"

    b.append(d.mono(caption, px, H - 26, 11, t["muted"], ls=2))
    legend_x = W - px - 50 - 5 * 15
    b.append(d.mono("LESS", legend_x - 12, H - 26, 11, t["muted"], anchor="end", ls=2))
    for k in range(5):
        b.append(f'<circle cx="{legend_x + k * 15 + 4}" cy="{H - 30}" r="4.6" fill="{levels[k]}"/>')
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
    ap.add_argument("--snake", help="Platane/snk SVG to embed in the telemetry panel")
    a = ap.parse_args()
    if a.mode == "static":
        A = ROOT / "assets"
        for name, t in THEMES.items():
            write(A / f"hero-{name}.svg", hero(t))
            write(A / f"stack-{name}.svg", stack(t))
            for i, (slug, pname, lines, tags) in enumerate(PROJECTS):
                write(A / f"project-{slug}-{name}.svg", project(t, i, pname, lines, tags))
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is not set")
        data = fetch(token)
        snake = pathlib.Path(a.snake) if a.snake else None
        snake_svg = snake.read_text(encoding="utf-8") if snake and snake.exists() else None
        for name, t in THEMES.items():
            write(pathlib.Path(a.out) / f"telemetry-{name}.svg", telemetry(t, data, snake_svg))


if __name__ == "__main__":
    main()
