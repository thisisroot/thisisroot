#!/usr/bin/env python3
"""
ROOT ARCADE — pixel-art SVG generator for the thisisroot profile README.

Every glyph is drawn from a hand-made 5x7 bitmap font, so the art looks the
same everywhere (GitHub can't load web fonts inside SVG images).

    python scripts/arcade.py static              # regenerate assets/*.svg
    python scripts/arcade.py hiscore --out dist  # live stats card (needs GITHUB_TOKEN)

Edit the CONTENT section below to change what the profile says.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import urllib.request
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
USER = os.environ.get("GH_USER", "thisisroot")
YEAR = dt.date.today().year

# ───────────────────────────── palette ─────────────────────────────
BG = "#050A06"
PANEL = "#0A160D"
GREEN = "#33FF66"
DIM = "#1D7A3A"
FAINT = "#123D20"
AMBER = "#FFB000"
CYAN = "#2EF2FF"
MAGENTA = "#FF3CAC"
RED = "#FF4D4D"
WHITE = "#E6FFE9"
GOLD = "#E8B64C"

# ───────────────────────────── content ─────────────────────────────
BOOT = [  # (left, right, colour of right)
    ("CPU  : RUST CORE @ 4.77MHZ", "OK", GREEN),
    ("MEM  : {mem}K BASE MEMORY", "OK", GREEN),
    ("I/O  : REST  WEBSOCKETS  OPENAPI", "OK", GREEN),
    ("GFX  : FLUTTER / DART", "OK", GREEN),
    ("SEC  : MLS CRYPTO CORE", "WIP", AMBER),
]
TAGLINE = "SYSTEMS  ·  CROSS-PLATFORM  ·  NETWORKED SOFTWARE"

WHOAMI = [
    ("CLASS", "SYSTEMS ENGINEER"),
    ("STACK", "RUST · FLUTTER · DART"),
    ("NETWORK", "REST · WEBSOCKETS · OPENAPI"),
    ("CRYPTO", "MLS  (IN PROGRESS)"),
    ("QUEST", "TRUST - SELF-HOSTED MESSENGER"),
    ("WM", "HYPRLAND + WAYBAR + EWW"),
    ("TERM", "KITTY + NEOVIM"),
    ("PLAYING", "SINCE 2017"),
    ("MOTTO", "LESS MAGIC. MORE OWNERSHIP."),
]

CARTS = [  # slug, title, description, language, language colour, public?
    ("trust-server", "TRUST-SERVER",
     "RUST BACKEND FOR ACCOUNTS, MESSAGING, REALTIME DELIVERY AND MEDIA.",
     "RUST", "#DEA584", True),
    ("trust-deploy", "TRUST-DEPLOY",
     "SELF-HOSTING KIT. RUN THE WHOLE TRUST STACK ON YOUR OWN METAL.",
     "DOCKER / SHELL", "#89E051", True),
    ("zdm", "ZDM",
     "SEGMENTED DOWNLOAD MANAGER. THE BEST DOWNLOAD MANAGER EVER!",
     "RUST", "#DEA584", True),
    ("paqet-i", "PAQET-I",
     "RAW PACKET TRANSPORT. FERRIES PACKETS ACROSS FORBIDDEN BOUNDARIES.",
     "GO", "#00ADD8", True),
    ("trust-client", "TRUST-CLIENT",
     "ONE FLUTTER APP FOR MOBILE, DESKTOP AND WEB. MONOCHROME, MOTION-LED.",
     "DART", "#00B4AB", False),
    ("trust-protocol", "TRUST-PROTOCOL",
     "VERSIONED REST + WEBSOCKET CONTRACTS. SCHEMAS ARE THE SOURCE OF TRUTH.",
     "JSON SCHEMA", "#F1E05A", False),
]

INVENTORY = [  # (category, colour, items)
    ("WEAPONS", AMBER, ["RUST", "DART", "GO", "TYPESCRIPT", "PYTHON"]),
    ("ARMOR", GREEN, ["FLUTTER", "DOCKER", "POSTGRESQL", "LINUX", "NEOVIM"]),
    ("SPELLS", MAGENTA, ["REST", "WEBSOCKETS", "OPENAPI", "JSONSCHEMA", "MLS"]),
]
FEATURED = [  # (row, col, flavour line 1, flavour line 2)
    (0, 0, "RUST - LEGENDARY WEAPON. FORGED IN THE BORROW CHECKER.",
     "+99 MEMORY SAFETY. FEARLESS CONCURRENCY."),
    (1, 0, "FLUTTER - EPIC ARMOR. ONE CODEBASE, EVERY SCREEN.",
     "MOBILE, DESKTOP AND WEB IN A SINGLE CAST."),
    (2, 1, "WEBSOCKETS - RARE SPELL. KEEPS THE LINE OPEN.",
     "REALTIME DELIVERY WITHOUT THE POLLING."),
    (2, 4, "MLS - MYTHIC SPELL. END-TO-END GROUP ENCRYPTION.",
     "STILL BEING ENCHANTED. HANDLE WITH CARE."),
    (1, 1, "DOCKER - UTILITY ARMOR. CARRY YOUR WORLD IN A BOX.",
     "SELF-HOSTING IS A FIRST-CLASS PATH."),
]

# ───────────────────────────── 5x7 font ─────────────────────────────
_F = {
    "A": ".###. #...# #...# ##### #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "####. #...# #...# #...# #...# #...# ####.",
    "E": "##### #.... #.... ####. #.... #.... #####",
    "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .####",
    "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": ".###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    "J": "..### ...#. ...#. ...#. ...#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    "N": "#...# #...# ##..# #.#.# #..## #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.",
    "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
    "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    "2": ".###. #...# ....# ...#. ..#.. .#... #####",
    "3": "##### ...#. ..#.. ...#. ....# #...# .###.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": "..##. .#... #.... ####. #...# #...# .###.",
    "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ...#. .##..",
    " ": "..... ..... ..... ..... ..... ..... .....",
    ".": "..... ..... ..... ..... ..... .##.. .##..",
    ",": "..... ..... ..... ..... .##.. ..#.. .#...",
    ":": "..... .##.. .##.. ..... .##.. .##.. .....",
    ";": "..... .##.. .##.. ..... .##.. ..#.. .#...",
    "-": "..... ..... ..... .###. ..... ..... .....",
    "_": "..... ..... ..... ..... ..... ..... #####",
    "/": "....# ....# ...#. ..#.. .#... #.... #....",
    "\\": "#.... #.... .#... ..#.. ...#. ....# ....#",
    "(": "...#. ..#.. .#... .#... .#... ..#.. ...#.",
    ")": ".#... ..#.. ...#. ...#. ...#. ..#.. .#...",
    "[": ".###. .#... .#... .#... .#... .#... .###.",
    "]": ".###. ...#. ...#. ...#. ...#. ...#. .###.",
    "!": "..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..",
    "?": ".###. #...# ....# ...#. ..#.. ..... ..#..",
    "'": "..#.. ..#.. .#... ..... ..... ..... .....",
    '"': ".#.#. .#.#. ..... ..... ..... ..... .....",
    "#": ".#.#. .#.#. ##### .#.#. ##### .#.#. .#.#.",
    "@": ".###. #...# #.### #.#.# #.### #.... .####",
    "+": "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
    "=": "..... ..... ##### ..... ##### ..... .....",
    ">": ".#... ..#.. ...#. ....# ...#. ..#.. .#...",
    "<": "...#. ..#.. .#... #.... .#... ..#.. ...#.",
    "*": "..... ..#.. #.#.# .###. #.#.# ..#.. .....",
    "&": ".##.. #..#. #.#.. .#... #.#.# #..#. .##.#",
    "%": "##..# ##..# ...#. ..#.. .#... #..## #..##",
    "|": "..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "~": "..... ..... .#... #.#.# ...#. ..... .....",
    "·": "..... ..... ..... ..#.. ..... ..... .....",
    "$": "..#.. .#### #.#.. .###. ..#.# ####. ..#..",
    "^": "..#.. .#.#. #...# ..... ..... ..... .....",
    "►": "#.... ##... ###.. ####. ###.. ##... #....",
    "█": "##### ##### ##### ##### ##### ##### #####",
    "♥": "..... .#.#. ##### ##### .###. ..#.. .....",
}
FONT = {k: v.split() for k, v in _F.items()}


def tw(s: str, sc: float) -> float:
    """Pixel width of a string at scale sc."""
    return (len(s) * 6 - 1) * sc if s else 0


def _runs(rows):
    """Yield (col, row, length) horizontal runs of set pixels."""
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            if row[x] not in ".":
                start, ch = x, row[x]
                while x < len(row) and row[x] == ch:
                    x += 1
                yield start, y, x - start, ch
            else:
                x += 1


def _n(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def text_d(s: str, x: float, y: float, sc: float) -> str:
    """SVG path data for a string; (x, y) is the top-left corner."""
    out = []
    for i, ch in enumerate(s.upper()):
        rows = FONT.get(ch, FONT[" "])
        ox = x + i * 6 * sc
        for cx, cy, ln, _ in _runs(rows):
            out.append(
                f"M{_n(ox + cx * sc)} {_n(y + cy * sc)}h{_n(ln * sc)}v{_n(sc)}h-{_n(ln * sc)}z"
            )
    return "".join(out)


def T(s, x, y, sc, fill, extra="", anchor="start"):
    """A pixel-text <path>. anchor: start | middle | end."""
    if anchor == "middle":
        x -= tw(s, sc) / 2
    elif anchor == "end":
        x -= tw(s, sc)
    return f'<path d="{text_d(s, x, y, sc)}" fill="{fill}" {extra}/>'


def bitmap(rows, x, y, sc, palette, extra=""):
    """Draw a multi-colour bitmap; palette maps char -> colour."""
    by_col: dict[str, list[str]] = {}
    for cx, cy, ln, ch in _runs(rows):
        by_col.setdefault(ch, []).append(
            f"M{_n(x + cx * sc)} {_n(y + cy * sc)}h{_n(ln * sc)}v{_n(sc)}h-{_n(ln * sc)}z"
        )
    return "".join(
        f'<path d="{"".join(d)}" fill="{palette[ch]}" {extra}/>' for ch, d in by_col.items()
    )


# ───────────────────────────── CRT frame ─────────────────────────────
def appear(t: float, body: str, hide_at: float | None = None) -> str:
    s = f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
    if hide_at is not None:
        s += f'<set attributeName="opacity" to="0" begin="{hide_at:.2f}s" fill="freeze"/>'
    return s + body + "</g>"


def blink(dur=1.0) -> str:
    return (f'<animate attributeName="opacity" values="1;0" dur="{dur}s" '
            f'calcMode="discrete" repeatCount="indefinite"/>')


def cycle(i: int, n: int, period: float) -> str:
    """Make element i of n visible during its slice of a repeating period."""
    a, b = i / n, (i + 1) / n
    if n == 1:
        return ""
    if i == 0:
        vals, kts = "1;0", f"0;{b:.4f}"
    elif i == n - 1:
        vals, kts = "0;1", f"0;{a:.4f}"
    else:
        vals, kts = "0;1;0", f"0;{a:.4f};{b:.4f}"
    return (f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" '
            f'dur="{period}s" calcMode="discrete" repeatCount="indefinite"/>')


def crt(w: int, h: int, title: str, body: str, *, roll=True, glow=1.1) -> str:
    """Wrap content in a CRT screen: glow, scanlines, vignette, rolling bar."""
    roll_bar = (
        f'<rect x="0" y="-90" width="{w}" height="90" fill="url(#roll)">'
        f'<animate attributeName="y" values="-90;{h}" dur="7s" repeatCount="indefinite"/></rect>'
        if roll else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<defs>
<pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" fill="#000" fill-opacity=".35"/></pattern>
<radialGradient id="vig" cx="50%" cy="50%" r="72%"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".7"/></radialGradient>
<radialGradient id="tint" cx="50%" cy="45%" r="65%"><stop offset="0" stop-color="{GREEN}" stop-opacity=".07"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></radialGradient>
<linearGradient id="roll" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset=".5" stop-color="{GREEN}" stop-opacity=".05"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>
<filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="{glow}" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="screen"><rect width="{w}" height="{h}" rx="16"/></clipPath>
</defs>
<g clip-path="url(#screen)" shape-rendering="crispEdges">
<rect width="{w}" height="{h}" fill="{BG}"/>
<rect width="{w}" height="{h}" fill="url(#tint)"/>
<g filter="url(#glow)">
<animate attributeName="opacity" values="1;.96;1;1;.98;1" keyTimes="0;.02;.04;.6;.62;1" dur="4s" repeatCount="indefinite"/>
{body}
</g>
{roll_bar}
<rect width="{w}" height="{h}" fill="url(#scan)"/>
<rect width="{w}" height="{h}" fill="url(#vig)"/>
</g>
<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="15" fill="none" stroke="{DIM}" stroke-opacity=".6" stroke-width="3"/>
</svg>
"""


def dotted(left: str, right: str, width: int = 40) -> tuple[str, str]:
    left = left + " "
    dots = "." * max(2, width - len(left) - len(right) - 1)
    return left + dots + " ", right


# ───────────────────────────── hero ─────────────────────────────
def hero() -> str:
    W, H = 900, 420
    sc, lh, x0, y0 = 2, 24, 36, 34
    parts = [appear(0.15, T(f"ROOT BIOS V2.0.17   (C) 2017-{YEAR} THISISROOT", x0, y0, sc, AMBER))]

    t = 0.6
    for i, (left, right, rc) in enumerate(BOOT):
        y = y0 + (i + 1.5) * lh
        if "{mem}" in left:
            frames = [f"{m:06d}" for m in (0, 128, 256, 384, 512, 640)]
            for j, m in enumerate(frames):
                l, r = dotted(left.format(mem=m), right)
                last = j == len(frames) - 1
                body = T(l, x0, y, sc, GREEN) + (T(r, x0 + tw(l, sc) + 2 * sc, y, sc, rc) if last else "")
                parts.append(appear(t + j * 0.11, body, None if last else t + (j + 1) * 0.11))
            t += len(frames) * 0.11 + 0.25
        else:
            l, r = dotted(left, right)
            parts.append(appear(t, T(l, x0, y, sc, GREEN)))
            parts.append(appear(t + 0.25, T(r, x0 + tw(l, sc) + 2 * sc, y, sc, rc)))
            t += 0.42

    y = y0 + (len(BOOT) + 2) * lh
    parts.append(appear(t, T("BOOTING ROOT.SYS", x0, y, sc, WHITE)
                        + f'<g>{blink(0.5)}{T("█", x0 + tw("BOOTING ROOT.SYS ", sc), y, sc, WHITE)}</g>',
                        t + 0.9))
    parts.append(appear(t + 0.9, T("ROOT.SYS LOADED. WELCOME, PLAYER ONE.", x0, y, sc, DIM)))
    t += 1.0

    # emblem, top-right (like an old BIOS vendor logo)
    ex, ey, es = W - 36 - 132, 26, 132
    emblem = (
        f'<rect x="{ex}" y="{ey}" width="{es}" height="{es}" fill="none" stroke="{AMBER}" stroke-width="4"/>'
        f'<rect x="{ex + 8}" y="{ey + 8}" width="{es - 16}" height="{es - 16}" fill="{AMBER}" fill-opacity=".08"/>'
        + T("#", ex + es / 2, ey + 16, 9, AMBER, anchor="middle")
        + T("ROOT", ex + es / 2, ey + es - 26, 2, AMBER, anchor="middle")
    )
    parts.append(appear(0.15, emblem))

    # big title with chromatic aberration + glitch
    title, tsc = "THISISROOT", 11
    tx, ty = (W - tw(title, tsc)) / 2, 248
    layers = []
    for colour, dx, glitch, op in ((MAGENTA, -3, "-3 0;-3 0;-11 0;5 0;-3 0;-3 0", ".7"),
                                    (CYAN, 3, "3 0;3 0;10 -2;-4 0;3 0;3 0", ".7"),
                                    (GREEN, 0, None, "1")):
        letters = "".join(
            appear(t + i * 0.09, T(ch, tx + i * 6 * tsc, ty, tsc, colour))
            for i, ch in enumerate(title)
        )
        anim = (f'<animateTransform attributeName="transform" type="translate" values="{glitch}" '
                f'keyTimes="0;.9;.92;.94;.96;1" dur="5s" repeatCount="indefinite"/>' if glitch else "")
        tr = f' transform="translate({dx} 0)"' if dx else ""
        layers.append(f'<g opacity="{op}"{tr}>{anim}{letters}</g>')
    parts.append("".join(layers))
    t += len(title) * 0.09 + 0.3

    parts.append(appear(t, T(TAGLINE, W / 2, ty + 7 * tsc + 26, 2, AMBER, anchor="middle")))
    prompt = "► PRESS START"
    px = (W - tw(prompt + " █", 2)) / 2
    parts.append(appear(t + 0.4, T(prompt, px, H - 42, 2, WHITE)
                        + f'<g>{blink(1)}{T("█", px + tw(prompt + " ", 2), H - 42, 2, WHITE)}</g>'))
    return crt(W, H, "THISISROOT — retro BIOS boot screen", "\n".join(parts), glow=1.3)


# ───────────────────────────── banner ─────────────────────────────
def banner(label: str, colour: str = GREEN) -> str:
    W, H = 900, 64
    body = (
        T("►", 28, 25, 2, colour, extra=f'opacity="1"') .replace("/>", f">{blink(1)}</path>")
        + T(label, 52, 22, 3, colour)
        + f'<path d="M{52 + tw(label, 3) + 24} 32h{W - 52 - tw(label, 3) - 24 - 28}" stroke="{colour}" '
          f'stroke-opacity=".35" stroke-width="3" stroke-dasharray="6 6"/>'
    )
    return crt(W, H, label, body, roll=False)


# ───────────────────────────── whoami ─────────────────────────────
COMPUTER = [
    ".BBBBBBBBBBBBBBBB.",
    "BBDDDDDDDDDDDDDDBB",
    "BBDSSSSSSSSSSSSDBB",
    "BBDSGSSSSSSSSSSDBB",
    "BBDSSGSSSSSSSSSDBB",
    "BBDSGSSCCCSSSSSDBB",
    "BBDSSSSSSSSSSSSDBB",
    "BBDSSSSSSSSSSSSDBB",
    "BBDDDDDDDDDDDDDDBB",
    "BBBBBBBBBBBBBBRBBB",
    ".BBBBBBBBBBBBBBBB.",
    "....DDDDDDDDDD....",
    "..KKKKKKKKKKKKKK..",
    ".KLKLKLKLKLKLKLKK.",
    ".KKKKKKKKKKKKKKKK.",
]


def whoami() -> str:
    W = 900
    sc, lh = 2, 26
    top = 64
    H = top + len(WHOAMI) * lh + 70
    pal = {"B": "#C9C2A7", "D": "#8C866F", "S": "#06140A", "G": GREEN,
           "R": RED, "K": "#8C866F", "L": "#C9C2A7"}
    comp_rows = [r.replace("C", "S") for r in COMPUTER]
    cursor = ["." * 18] * 5 + ["......CCC........."] + ["." * 18] * 9
    cs = 9
    cx, cy = 48, top + 6
    art = (bitmap(comp_rows, cx, cy, cs, pal)
           + f'<g>{blink(0.8)}{bitmap(cursor, cx, cy, cs, {"C": GREEN})}</g>')

    # title bar
    bar = (f'<rect x="0" y="0" width="{W}" height="40" fill="{FAINT}"/>'
           f'<path d="M0 40h{W}" stroke="{DIM}" stroke-width="2"/>'
           + "".join(f'<rect x="{20 + i * 22}" y="14" width="12" height="12" fill="{c}"/>'
                     for i, c in enumerate((RED, AMBER, GREEN)))
           + T(f"ROOT@{USER}: ~ $ WHOAMI", W / 2, 13, 2, GREEN, anchor="middle"))

    rx = 260
    lines = [T(f"ROOT@{USER}", rx, top, 3, GREEN),
             f'<path d="M{rx} {top + 30}h{tw("ROOT@" + USER, 3)}" stroke="{DIM}" stroke-width="3" stroke-dasharray="9 3"/>']
    for i, (k, v) in enumerate(WHOAMI):
        y = top + 46 + i * lh
        lines.append(appear(0.2 + i * 0.12, T(f"{k:<8}", rx, y, sc, AMBER) + T(": " + v, rx + 8 * 12, y, sc, WHITE)))
    # neofetch colour blocks
    by = top + 46 + len(WHOAMI) * lh + 6
    lines.append("".join(f'<rect x="{rx + i * 30}" y="{by}" width="26" height="14" fill="{c}"/>'
                         for i, c in enumerate((BG, RED, GREEN, AMBER, CYAN, MAGENTA, "#7C6CFF", WHITE))))
    return crt(W, by + 40, f"whoami — {USER}", bar + art + "".join(lines))


# ───────────────────────────── cartridges ─────────────────────────────
LOCK = [".###.", "#...#", "#...#", "#####", "##.##", "##.##", "#####"]


def wrap(s: str, n: int) -> list[str]:
    out, cur = [], ""
    for word in s.split():
        if len(cur) + len(word) + (1 if cur else 0) > n:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    return out + ([cur] if cur else [])


def cartridge(i, slug, title, desc, lang, lcol, public) -> str:
    W, H = 440, 260
    accent = [GREEN, AMBER, CYAN, MAGENTA, RED, "#7C6CFF"][i % 6]
    if not public:
        accent = "#5C6B60"
    body_d = (f"M24 8H416l16 16V196l-14 14v34H22v-34l-14-14V24Z")
    grips = "".join(f'<path d="M{W / 2 - 60} {16 + k * 6}h120" stroke="#3C4A40" stroke-width="2"/>' for k in range(3))
    lx, ly, lw, lh = 38, 40, W - 76, 162
    label = (f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{PANEL}" stroke="{accent}" stroke-width="3"/>'
             f'<rect x="{lx}" y="{ly}" width="{lw}" height="22" fill="{accent}" fill-opacity=".9"/>'
             + T(f"SLOT {i + 1:02d}", lx + 10, ly + 4, 2, BG)
             + T("PUBLIC" if public else "PRIVATE", lx + lw - 10, ly + 4, 2, BG, anchor="end"))
    tsc = 4 if tw(title, 4) <= lw - 20 else 3
    label += T(title, lx + 12, ly + 34, tsc, WHITE if public else "#7D8C80")
    for j, line in enumerate(wrap(desc, (lw - 24) // 12)[:3]):
        label += T(line, lx + 12, ly + 76 + j * 22, 2, GREEN if public else "#4F6B57")
    fy = ly + lh - 20
    label += f'<rect x="{lx + 12}" y="{fy}" width="12" height="12" fill="{lcol}"/>'
    label += T(lang, lx + 32, fy, 2, AMBER if public else "#6A6A55")
    if public:
        label += f'<g>{blink(1.2)}{T("► PLAY", lx + lw - 10, fy, 2, WHITE, anchor="end")}</g>'
    else:
        label += bitmap(LOCK, lx + lw - 10 - 14 - tw(" LOCKED", 2), fy - 2, 2.3, {"#": AMBER})
        label += T(" LOCKED", lx + lw - 10, fy, 2, AMBER, anchor="end")
    pins = "".join(f'<rect x="{40 + k * 15}" y="222" width="9" height="20" fill="{GOLD}" fill-opacity=".8"/>'
                   for k in range(24))
    body = (f'<path d="{body_d}" fill="#1B221D" stroke="#3C4A40" stroke-width="3"/>'
            f'<path d="M22 214H418" stroke="#0C110E" stroke-width="4"/>' + grips + label + pins)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}: {escape(desc)}">
<title>{title} — {escape(desc)}</title>
<defs><filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation=".9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<g shape-rendering="crispEdges" filter="url(#glow)">{body}</g>
</svg>
"""


# ───────────────────────────── inventory ─────────────────────────────
def inventory() -> str:
    W = 900
    sw, sh, gap, x0, y0, rgap = 140, 52, 8, 136, 66, 12
    rows_h = len(INVENTORY) * (sh + rgap)
    H = y0 + rows_h + 100
    n_items = sum(len(it) for _, _, it in INVENTORY)
    parts = [T("INVENTORY", 32, 22, 3, WHITE),
             T(f"SLOTS {n_items}/{n_items}   GOLD 0   WEIGHT: LIGHT", W - 32, 26, 2, DIM, anchor="end")]
    for r, (cat, col, items) in enumerate(INVENTORY):
        y = y0 + r * (sh + rgap)
        parts.append(T(cat, 32, y + sh / 2 - 7, 2, col))
        for c, item in enumerate(items):
            x = x0 + c * (sw + gap)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{sw}" height="{sh}" fill="{PANEL}" stroke="{col}" stroke-opacity=".45" stroke-width="2"/>'
                f'<rect x="{x + 6}" y="{y + 6}" width="6" height="6" fill="{col}"/>'
                + T(item, x + sw / 2, y + sh / 2 - 7, 2, WHITE, anchor="middle"))

    # animated selector + description box cycling through FEATURED
    period = 2.6 * len(FEATURED)
    pos = ";".join(f"{x0 + c * (sw + gap) - 5} {y0 + r * (sh + rgap) - 5}" for r, c, *_ in FEATURED)
    kts = ";".join(f"{k / len(FEATURED):.4f}" for k in range(len(FEATURED)))
    parts.append(
        f'<g><animateTransform attributeName="transform" type="translate" values="{pos}" keyTimes="{kts}" '
        f'dur="{period}s" calcMode="discrete" repeatCount="indefinite"/>'
        f'<rect x="0" y="0" width="{sw + 10}" height="{sh + 10}" fill="none" stroke="{WHITE}" stroke-width="3">'
        f'<animate attributeName="stroke-opacity" values="1;.35;1" dur=".8s" repeatCount="indefinite"/></rect></g>')
    by = y0 + rows_h + 6
    parts.append(f'<rect x="32" y="{by}" width="{W - 64}" height="70" fill="{PANEL}" stroke="{DIM}" stroke-width="2"/>')
    for k, (_, _, l1, l2) in enumerate(FEATURED):
        parts.append(f'<g>{cycle(k, len(FEATURED), period)}'
                     + T(l1, 48, by + 16, 2, AMBER) + T(l2, 48, by + 42, 2, GREEN) + "</g>")
    return crt(W, H, "Inventory — languages, tools and protocols", "\n".join(parts))


# ───────────────────────────── footer ─────────────────────────────
COIN = [
    ["..YYYY..", ".YYYYYY.", "YYYOOYYY", "YYYOOYYY", "YYYOOYYY", "YYYOOYYY", ".YYYYYY.", "..YYYY.."],
    ["...YY...", "..YYYY..", "..YOYY..", "..YOYY..", "..YOYY..", "..YOYY..", "..YYYY..", "...YY..."],
    ["...YY...", "...YY...", "...OY...", "...OY...", "...OY...", "...OY...", "...YY...", "...YY..."],
]


def footer() -> str:
    W, H = 900, 170
    parts = [T("THANKS FOR PLAYING", W / 2, 30, 3, GREEN, anchor="middle")]
    msg = "INSERT COIN TO CONTINUE"
    mx = (W - tw(msg, 2)) / 2
    parts.append(f"<g>{blink(1.1)}{T(msg, mx, 78, 2, AMBER)}</g>")
    seq = [0, 1, 2, 1]
    for k, f in enumerate(seq):
        for side in (mx - 44, mx + tw(msg, 2) + 20):
            parts.append(f'<g>{cycle(k, len(seq), 0.8)}{bitmap(COIN[f], side, 74, 3, {"Y": GOLD, "O": "#A8741A"})}</g>')
    parts.append(T("CREDIT 00", 32, H - 36, 2, DIM))
    parts.append(T("LESS MAGIC. MORE OWNERSHIP.", W / 2, H - 36, 2, WHITE, anchor="middle"))
    parts.append(T(f"© {YEAR}".replace("©", "(C)"), W - 32, H - 36, 2, DIM, anchor="end"))
    return crt(W, H, "Thanks for playing — insert coin to continue", "\n".join(parts))


# ───────────────────────────── hi-score (live) ─────────────────────────────
def gql(query: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "root-arcade"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]


def fetch_stats(user: str, token: str) -> dict:
    u = gql(f"""{{ user(login: "{user}") {{
        createdAt followers {{ totalCount }}
        pullRequests {{ totalCount }}
        repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100, isFork: false) {{
          totalCount nodes {{ stargazerCount }} }}
        contributionsCollection {{
          contributionYears totalCommitContributions restrictedContributionsCount
          contributionCalendar {{ totalContributions }} }} }} }}""", token)["user"]
    years = u["contributionsCollection"]["contributionYears"]
    aliases = " ".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
        f'{{ contributionCalendar {{ totalContributions }} }}' for y in years)
    per_year = gql(f'{{ user(login: "{user}") {{ {aliases} }} }}', token)["user"]
    cc = u["contributionsCollection"]
    return {
        "ALL-TIME CONTRIBS": sum(v["contributionCalendar"]["totalContributions"] for v in per_year.values()),
        "CONTRIBS (1 YEAR)": cc["contributionCalendar"]["totalContributions"],
        "CLASSIFIED OPS": cc["restrictedContributionsCount"],
        "COMMITS (1 YEAR)": cc["totalCommitContributions"],
        "PULL REQUESTS": u["pullRequests"]["totalCount"],
        "STARS EARNED": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "PUBLIC REPOS": u["repositories"]["totalCount"],
        "FOLLOWERS": u["followers"]["totalCount"],
        "_since": int(u["createdAt"][:4]),
    }


def hiscore(stats: dict) -> str:
    W = 900
    since = stats.pop("_since", 2017)
    rows = sorted(stats.items(), key=lambda kv: -kv[1])
    top = max(v for _, v in rows) if rows else 0
    colours = [RED, AMBER, "#FFE14D", GREEN, CYAN, "#7C6CFF", MAGENTA, WHITE]
    sc, lh, y0 = 3, 34, 170
    H = y0 + len(rows) * lh + 64
    parts = [
        f'<g>{blink(0.9)}{T("1UP", 64, 22, 2, RED)}</g>', T(USER, 64, 44, 2, WHITE),
        T("HI-SCORE", W / 2, 22, 2, RED, anchor="middle"), T(f"{top:07d}", W / 2, 44, 2, WHITE, anchor="middle"),
        T("2UP", W - 64, 22, 2, DIM, anchor="end"),
        T(f"PLAYING SINCE {since}", W - 64, 44, 2, DIM, anchor="end"),
    ]
    title = "HIGH SCORES"
    title_cols = ";".join([RED, AMBER, "#FFE14D", GREEN, CYAN, MAGENTA])
    parts.append(T(title, W / 2, 84, 5, RED, anchor="middle").replace(
        "/>", f'><animate attributeName="fill" values="{title_cols}" dur="1.8s" calcMode="discrete" repeatCount="indefinite"/></path>'))
    cr, cs, cn = 110, 250, 440
    parts += [T("RANK", cr, 136, 2, CYAN), T("SCORE", cs, 136, 2, CYAN), T("NAME", cn, 136, 2, CYAN)]
    suffix = {1: "ST", 2: "ND", 3: "RD"}
    for i, (name, val) in enumerate(rows):
        y, c = y0 + i * lh, colours[i % len(colours)]
        rank = f"{i + 1}{suffix.get(i + 1, 'TH')}"
        parts.append(appear(0.3 + i * 0.18, T(rank, cr, y, sc, c) + T(f"{val:07d}", cs, y, sc, c) + T(name, cn, y, sc, c)))
    parts.append(T(f"UPDATED {dt.date.today().isoformat()}  ·  RESCORED DAILY BY GITHUB ACTIONS",
                   W / 2, H - 34, 2, DIM, anchor="middle"))
    return crt(W, H, f"High scores — live GitHub stats for {USER}", "\n".join(parts))


# ───────────────────────────── main ─────────────────────────────
def write(path: pathlib.Path, svg: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8", newline="\n")
    print(f"wrote {path} ({len(svg) // 1024} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["static", "hiscore"])
    ap.add_argument("--out", default="dist")
    a = ap.parse_args()
    if a.mode == "static":
        A = ROOT / "assets"
        write(A / "hero.svg", hero())
        write(A / "whoami.svg", whoami())
        write(A / "inventory.svg", inventory())
        write(A / "footer.svg", footer())
        for slug, label, col in (("carts", "SELECT A CARTRIDGE", GREEN),
                                 ("arcade", "SNAKE.EXE  -  EATING MY COMMITS", AMBER)):
            write(A / f"banner-{slug}.svg", banner(label, col))
        for i, c in enumerate(CARTS):
            write(A / "carts" / f"{c[0]}.svg", cartridge(i, *c))
    else:
        token = os.environ.get("GITHUB_TOKEN") or raise_(SystemExit("GITHUB_TOKEN is not set"))
        write(ROOT / a.out / "hiscore.svg", hiscore(fetch_stats(USER, token)))


def raise_(e):
    raise e


if __name__ == "__main__":
    main()
