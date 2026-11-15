#!/usr/bin/env python3
"""Zeichnet das Banner des GitHub-Profils nach assets/banner.svg.

Stil wie Breath of Freedom (STIL.md im Spiel-Repo): flache Facetten, links hell und rechts dunkel,
nur Wichtiges leuchtet in Jade. Gleiter, Waystone und Watchtower sind aus dem Wiki des Spiels
übernommen (wiki/symbole.js, wiki/karte.js), damit Profil und Spiel gleich aussehen.

Das Banner ist ein SVG mit eingebauter Bewegung (CSS), ohne Skripte, fremde Schriften oder Dateien:
GitHub zeigt Bilder abgeschottet an, dort geht nur, was in der Datei selbst steht.
Wer im System "Bewegung reduzieren" eingestellt hat, sieht alles still.

Aufruf (Mac): python3 tools/zeichne_profil.py   (Windows: py tools\\zeichne_profil.py)
"""
import random
from pathlib import Path

ZIEL = Path(__file__).resolve().parent.parent / "assets"

# ---------- Farben aus STIL.md ----------
JADE = "#7fdcb3"
JADE_HELL = "#d6fff0"
TEXT = "#ece6d6"
GRUND = "#16141b"
SANS = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"


def z(v):
    """Kurze Zahl fürs SVG (2 Nachkommastellen, ohne Nullen am Ende)."""
    return f"{v:.2f}".rstrip("0").rstrip(".")


# ---------- Grundformen wie im Wiki ----------
def P(pts, c, extra=""):
    return f'<polygon points="{pts}" fill="{c}" {extra}/>'


def L(d, c, w=2, extra=""):
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def C(x, y, r, c, extra=""):
    return f'<circle cx="{z(x)}" cy="{z(y)}" r="{z(r)}" fill="{c}" {extra}/>'


def funkel(x, y, s, c, extra=""):
    q = s * 0.22
    return P(f"{z(x)},{z(y - s)} {z(x + q)},{z(y - q)} {z(x + s)},{z(y)} {z(x + q)},{z(y + q)} "
             f"{z(x)},{z(y + s)} {z(x - q)},{z(y + q)} {z(x - s)},{z(y)} {z(x - q)},{z(y - q)}", c, extra)


# ---------- Schrift der Builders ----------
# Gerade Linien mit rechtwinkligen Ecken und 45°-Kanten, wie die Jade-Linien an den Bauten im Spiel.
# Raster: 4 Einheiten breit, 6 hoch (y nach unten). Wert: (Breite, Pfad).
GLYPHEN = {
    "A": (4, "M0 6V1L1 0H3L4 1V6M0 3.4H4"),
    "B": (4, "M0 0H3L4 1V2L3 3L4 4V5L3 6H0ZM0 3H3"),
    "C": (4, "M4 0H1L0 1V5L1 6H4"),
    "D": (4, "M0 0H3L4 1V5L3 6H0Z"),
    "E": (4, "M4 0H0V6H4M0 3H3"),
    "F": (4, "M4 0H0V6M0 3H3"),
    "G": (4, "M4 0H1L0 1V5L1 6H4V3H2"),
    "H": (4, "M0 0V6M4 0V6M0 3H4"),
    "I": (2, "M1 0V6M0 0H2M0 6H2"),
    "J": (4, "M2 0H4V5L3 6H1L0 5"),
    "K": (4, "M0 0V6M4 0L1 3H0M1 3L4 6"),
    "L": (4, "M0 0V6H4"),
    "M": (4, "M0 6V0L2 2L4 0V6"),
    "N": (4, "M0 6V0L4 6V0"),
    "O": (4, "M1 0H3L4 1V5L3 6H1L0 5V1Z"),
    "P": (4, "M0 6V0H3L4 1V2L3 3H0"),
    "R": (4, "M0 6V0H3L4 1V2L3 3H0M2 3L4 5V6"),
    "S": (4, "M4 0H1L0 1V2L1 3H3L4 4V5L3 6H0"),
    "T": (4, "M0 0H4M2 0V6"),
    "U": (4, "M0 0V5L1 6H3L4 5V0"),
    "V": (4, "M0 0V4L2 6L4 4V0"),
    "W": (4, "M0 0V6L2 4L4 6V0"),
    "X": (4, "M0 0L4 6M4 0L0 6"),
    "Y": (4, "M0 0V2L2 4L4 2V0M2 4V6"),
    "Z": (4, "M0 0H4V1L0 5V6H4"),
}
ABSTAND, LEER = 1.5, 2.6


def builder_breite(text, e):
    lauf = 0.0
    for ch in text:
        lauf += LEER if ch == " " else GLYPHEN[ch][0] + ABSTAND
    return (lauf - ABSTAND) * e


def builder(text, x, y, e, anker="mitte", start=0.0, takt=0.08, dicke=0.42):
    """Schreibt text in Builder-Schrift. e = eine Raster-Einheit in px (Buchstaben sind 6 e hoch).
    Jeder Buchstabe zieht sich nacheinander auf (start, takt in Sekunden), danach pulsiert das Leuchten."""
    teile, lauf = [], 0.0
    for ch in text:
        if ch == " ":
            lauf += LEER
            continue
        b, d = GLYPHEN[ch]
        teile.append((lauf, d))
        lauf += b + ABSTAND
    x0 = x - builder_breite(text, e) / 2 if anker == "mitte" else x

    def schicht(klasse="zieh"):
        return "".join(
            f'<path d="{d}" transform="translate({z(x0 + lx * e)} {z(y)}) scale({z(e)})" pathLength="1" '
            f'class="{klasse}" style="animation-delay:{start + i * takt:.2f}s"/>'
            for i, (lx, d) in enumerate(teile))

    zug = 'fill="none" stroke-linecap="square" stroke-linejoin="miter"'
    return (f'<g {zug} stroke="#0d0b10" stroke-width="{z(dicke * 2.6)}" opacity=".55">{schicht()}</g>'
            f'<g class="puls"><g {zug} filter="url(#weich)" stroke="{JADE}" stroke-width="{z(dicke * 2.4)}">{schicht()}</g></g>'
            f'<g {zug} stroke="{JADE}" stroke-width="{z(dicke)}">{schicht()}</g>'
            f'<g {zug} stroke="{JADE_HELL}" stroke-width="{z(dicke * .34)}" opacity=".9">{schicht()}</g>')


# ---------- Gemeinsame Teile aller Bilder ----------
VERLAEUFE = """<radialGradient id="glowJade"><stop offset="0" stop-color="#7fdcb3" stop-opacity=".7"/><stop offset="1" stop-color="#7fdcb3" stop-opacity="0"/></radialGradient>"""

GRUND_CSS = f"""
text {{ font-family: {SANS}; }}
@keyframes puls {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
.puls {{ animation: puls 4s ease-in-out infinite; }}
@keyframes zeichnen {{ from {{ stroke-dashoffset: 1.05; }} to {{ stroke-dashoffset: 0; }} }}
.zieh {{ stroke-dasharray: 1 1.1; animation: zeichnen 1s cubic-bezier(.6, 0, .3, 1) both; }}
@keyframes wiegen {{ 0%, 100% {{ transform: translateY(0) rotate(-2deg); }} 50% {{ transform: translateY(5px) rotate(2deg); }} }}
.wiegen {{ animation: wiegen 3.4s ease-in-out infinite; transform-box: fill-box; transform-origin: 50% 20%; }}
@keyframes schweben {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-4px); }} }}
.schweben {{ animation: schweben 3s ease-in-out infinite; }}
@keyframes funkeln {{ 0%, 100% {{ opacity: .95; }} 50% {{ opacity: .15; }} }}
.f1 {{ animation: funkeln 3.1s ease-in-out infinite; }}
.f2 {{ animation: funkeln 4.3s ease-in-out 1.1s infinite; }}
.f3 {{ animation: funkeln 5.7s ease-in-out 2.3s infinite; }}
@keyframes gluehwurm {{ 0%, 100% {{ transform: translate(0, 0); opacity: .1; }} 50% {{ transform: translate(7px, -12px); opacity: 1; }} }}
.gw {{ animation: gluehwurm 5s ease-in-out infinite; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
"""


def svg(w, h, titel, inhalt, css="", defs=""):
    weich = (f'<filter id="weich" filterUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">'
             f'<feGaussianBlur stdDeviation="3.2"/></filter>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{titel}">\n'
            f'<title>{titel}</title>\n<style>{GRUND_CSS}{css}</style>\n'
            f'<defs>{VERLAEUFE}{weich}{defs}</defs>\n{inhalt}\n</svg>\n')


def text(x, y, inhalt, groesse=14, farbe=TEXT, anker="start", gewicht=400, abstand=0, extra=""):
    ab = f' letter-spacing="{abstand}"' if abstand else ""
    return (f'<text x="{z(x)}" y="{z(y)}" font-size="{groesse}" fill="{farbe}" text-anchor="{anker}" '
            f'font-weight="{gewicht}"{ab} {extra}>{inhalt}</text>')


# ---------- Landschaft ----------
def berg(x, oben, hb, basis, hell, dunkel, schnee=None):
    """Berg aus zwei Facetten: links hell, rechts dunkel. schnee = (hell, dunkel) für die Kappe."""
    k = x + hb * 0.12
    s = P(f"{z(x - hb)},{z(basis)} {z(x)},{z(oben)} {z(k)},{z(basis)}", hell)
    s += P(f"{z(x)},{z(oben)} {z(x + hb)},{z(basis)} {z(k)},{z(basis)}", dunkel)
    if schnee:
        t = (basis - oben) * 0.24
        s += P(f"{z(x)},{z(oben)} {z(x - hb * .24)},{z(oben + t)} {z(x - hb * .1)},{z(oben + t * .7)} "
               f"{z(x + hb * .03)},{z(oben + t)}", schnee[0])
        s += P(f"{z(x)},{z(oben)} {z(x + hb * .03)},{z(oben + t)} {z(x + hb * .13)},{z(oben + t * .75)} "
               f"{z(x + hb * .24)},{z(oben + t)}", schnee[1])
    return s


def kamm(gipfel, basis, hell, dunkel, unten, schnee_bis=None, schnee=None):
    """Bergkette: Gipfel (x, oben, halbe Breite) und eine Fläche darunter, damit keine Lücken bleiben."""
    s = "".join(berg(x, o, hb, basis, hell, dunkel, schnee if schnee_bis and o <= schnee_bis else None)
                for x, o, hb in gipfel)
    return s + f'<rect x="-20" y="{z(basis - .5)}" width="2000" height="{z(unten - basis + 1)}" fill="{dunkel}"/>'


def kamm_y(x, gipfel, basis):
    """Höhe der Kette an der Stelle x (kleinster y-Wert aller Berg-Flanken)."""
    y = basis
    for gx, o, hb in gipfel:
        if abs(x - gx) < hb:
            y = min(y, o + (basis - o) * abs(x - gx) / hb)
    return y


def baum(x, unten, h, hell, dunkel):
    b = h * 0.32
    return (P(f"{z(x - b)},{z(unten)} {z(x)},{z(unten - h)} {z(x)},{z(unten)}", hell)
            + P(f"{z(x)},{z(unten - h)} {z(x + b)},{z(unten)} {z(x)},{z(unten)}", dunkel))


def wolke(x, y, w, hell, dunkel, deckung=1.0):
    h = w * 0.2
    oben = (f"{z(x)},{z(y)} {z(x + w * .12)},{z(y - h * .55)} {z(x + w * .3)},{z(y - h * .8)} {z(x + w * .42)},{z(y - h * 1.15)} "
            f"{z(x + w * .6)},{z(y - h * .9)} {z(x + w * .78)},{z(y - h * .95)} {z(x + w * .9)},{z(y - h * .45)} {z(x + w)},{z(y)}")
    return (f'<g opacity="{deckung}">{P(oben, hell)}'
            f'{P(f"{z(x + w * .06)},{z(y)} {z(x + w * .94)},{z(y)} {z(x + w * .86)},{z(y - h * .28)} {z(x + w * .14)},{z(y - h * .28)}", dunkel)}</g>')


def turm(farbe_hell, farbe_dunkel):
    """Watchtower der Builders, Fuß bei (0, 0): Sockel, schlanker Schaft, Plattform, schwebender Jade-Ring."""
    h, d = farbe_hell, farbe_dunkel
    s = P("-22,0 0,0 0,-14 -18,-14", h) + P("0,0 22,0 18,-14 0,-14", d)
    s += P("-12,-14 0,-14 0,-108 -9,-108", h) + P("0,-14 12,-14 9,-108 0,-108", d)
    s += P("-19,-108 0,-108 0,-118 -16,-118", h) + P("0,-108 19,-108 16,-118 0,-118", d)
    s += P("-17,-118 -11,-118 -11,-127 -17,-127", h) + P("11,-118 17,-118 17,-127 11,-127", d)
    s += C(0, -146, 34, "url(#glowJade)", 'class="puls"')
    s += L("M-4 -22 V-50 H3 V-78 H-3 V-102", JADE, 1.6, 'class="puls"')
    s += f'<g class="schweben">{C(0, -146, 13, "none", f"stroke=\"{JADE}\" stroke-width=\"3\"")}' \
         f'{C(0, -146, 13, "none", "stroke=\"#d6fff0\" stroke-width=\"1\" opacity=\".8\"")}</g>'
    return s


def waystone(gross=1.0):
    """Waystone wie auf der Karte: heller Steinblock, darüber schwebt ein Jade-Ring. Fuß bei (0, 0)."""
    s = P("-13,0 0,0 0,-16 -11,-16", "#d9d2c0") + P("0,0 13,0 11,-16 0,-16", "#a99f86")
    s += P("-9,-16 0,-16 0,-21 -7,-21", "#e2d8bd") + P("0,-16 9,-16 7,-21 0,-21", "#b7ae98")
    s += L("M0 -3 V-14", JADE, 1.4, 'class="puls"')
    s += C(0, -32, 22, "url(#glowJade)", 'class="puls"')
    s += (f'<g class="schweben"><ellipse cx="0" cy="-32" rx="15" ry="5" fill="none" stroke="{JADE}" stroke-width="2.4"/>'
          f'<ellipse cx="0" cy="-32" rx="15" ry="5" fill="none" stroke="{JADE_HELL}" stroke-width=".8" opacity=".8"/></g>')
    return f'<g transform="scale({gross})">{s}</g>'


# ---------- Gleiter aus dem Wiki ----------
def gleiter():
    """Gleiter von vorne (SYMBOLE.glider), viewBox 100 x 100."""
    return (P("12,40 30,22 50,18 50,40", "#c9a46a") + P("50,18 70,22 88,40 50,40", "#a8834e") + P("12,40 88,40 84,46 16,46", "#8a5a2c")
            + C(50, 30, 5, "none", f'stroke="{JADE}" stroke-width="1.8"')
            + L("M16 46 L40 74 M84 46 L60 74 M38 46 L44 74 M62 46 L56 74", "#e6dcc4", 1)
            + P("38,74 62,74 62,78 38,78", "#6b4a2b"))


JACKE = ("#b08a5a", "#8f6c42")
HAUT = ("#e0c49a", "#c4a67a")
HOSE = ("#4a505c", "#3c414b")
LEDER = ("#6b4a2b", "#563b22")


def gleiter_mit_figur():
    """Gleiter mit der Spielfigur darunter, Arme hoch am Griff; dahinter Wind-Striche."""
    s = L("M14 41 L-34 38 M86 41 L40 36 M20 46 L-22 47", "#ffffff", 1, 'opacity=".28"')
    s += gleiter()
    s += P("40,77 45,77 46,94 41,94", JACKE[0]) + P("55,77 60,77 59,94 54,94", JACKE[1])
    s += P("44,82 50,82 50,93 44,93", HAUT[0]) + P("50,82 56,82 56,93 50,93", HAUT[1]) + P("44,82 56,82 56,85 44,85", LEDER[0])
    s += P("42,93 50,93 50,111 42,111", JACKE[0]) + P("50,93 58,93 58,111 50,111", JACKE[1])
    s += P("43,111 49,111 49,126 43,126", HOSE[0]) + P("51,111 57,111 57,126 51,126", HOSE[1])
    s += P("43,122 49,122 49,126 43,126", LEDER[0]) + P("51,122 57,122 57,126 51,126", LEDER[1])
    return s


def gluehwuermer(rnd, n, x0, x1, y0, y1):
    s = ""
    for i in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        farbe = JADE if i % 3 else "#ffe08a"
        s += (f'<g class="gw" style="animation-delay:-{rnd.uniform(0, 5):.1f}s;animation-duration:{rnd.uniform(4, 7):.1f}s">'
              f'{C(x, y, 4, farbe, "opacity=\".25\"")}{C(x, y, 1.4, farbe)}</g>')
    return s


# ---------- Banner ----------
def banner():
    W, H = 960, 330
    rnd = random.Random(7)
    defs = f"""<linearGradient id="himmel" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#110f20"/><stop offset=".3" stop-color="#231c3d"/><stop offset=".5" stop-color="#3d2e57"/>
<stop offset=".63" stop-color="#6b4563"/><stop offset=".73" stop-color="#ad626a"/><stop offset=".8" stop-color="#df8e62"/><stop offset=".87" stop-color="#f3b86f"/></linearGradient>
<radialGradient id="sonne"><stop offset="0" stop-color="#ffd9a0" stop-opacity=".9"/><stop offset=".35" stop-color="#ffb46a" stop-opacity=".35"/><stop offset="1" stop-color="#ff9a5a" stop-opacity="0"/></radialGradient>
<linearGradient id="dunst" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3b86f" stop-opacity="0"/><stop offset="1" stop-color="#f3b86f" stop-opacity=".32"/></linearGradient>
<clipPath id="rahmen"><rect width="{W}" height="{H}" rx="14"/></clipPath>"""
    css = """
@keyframes flug { from { transform: translate(-120px, 192px); } to { transform: translate(1080px, 236px); } }
.flug { animation: flug 30s linear -9s infinite; }
@keyframes treiben { from { transform: translateX(0); } to { transform: translateX(-70px); } }
.treiben { animation: treiben 38s ease-in-out infinite alternate; }
.treiben2 { animation: treiben 52s ease-in-out -20s infinite alternate-reverse; }
@keyframes wachsen { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.linie { animation: wachsen 1.3s cubic-bezier(.5, 0, .2, 1) 1.1s both; transform-origin: 480px 154px; }
@keyframes einblenden { from { opacity: 0; } to { opacity: 1; } }
.ein { animation: einblenden 1.2s ease-out both; }
"""
    s = [f'<g clip-path="url(#rahmen)">', f'<rect width="{W}" height="{H}" fill="url(#himmel)"/>']

    # Sterne, oben dichter
    for i in range(85):
        x, y = rnd.uniform(8, W - 8), 8 + 175 * rnd.random() ** 1.5
        r = rnd.choice([.6, .7, .9, 1.1, 1.4])
        k = ["f1", "f2", "f3", ""][i % 4]
        s.append(C(x, y, r, "#f3eee2", f'class="{k}" opacity="{z(1 - y / 260)}"'))
    for x, y, g, k in [(92, 40, 5, "f2"), (858, 58, 6, "f1"), (640, 30, 4, "f3"), (300, 92, 4, "f1")]:
        s.append(funkel(x, y, g, "#f3eee2", f'class="{k}"'))

    # tief stehende Sonne links, Licht kommt wie überall im Spiel von links
    s.append(C(175, 262, 150, "url(#sonne)"))
    s.append(C(175, 256, 24, "#ffe2b0"))

    # hohe Wolken an den Rändern, ziehen langsam
    s.append(f'<g class="treiben">{wolke(40, 112, 150, "#5a4670", "#4a3a60", .7)}{wolke(770, 96, 170, "#5a4670", "#4a3a60", .6)}</g>')

    # ferne Kette, rosa im Abendlicht, die höchsten Gipfel mit Schnee
    fern = [(60, 214, 120), (190, 198, 110), (320, 222, 120), (450, 206, 130), (590, 218, 120), (720, 196, 130), (860, 212, 120), (990, 204, 110)]
    s.append(kamm(fern, 274, "#8e6a86", "#6e5270", H, 200, ("#f0cfc8", "#c9a0aa")))
    s.append(f'<rect x="0" y="196" width="{W}" height="80" fill="url(#dunst)"/>')
    s.append(f'<g class="treiben2">{wolke(250, 236, 180, "#f2b38e", "#d98f7a", .55)}{wolke(560, 228, 140, "#f2b38e", "#d98f7a", .45)}</g>')

    # mittlere Kette
    mitte = [(0, 248, 140), (140, 232, 120), (300, 252, 140), (420, 238, 110), (560, 254, 150), (700, 238, 120), (830, 250, 130), (960, 242, 120)]
    s.append(kamm(mitte, 302, "#5d5470", "#463f58", H))

    # nahe Hügel mit Bäumen und dem Watchtower
    nah = [(80, 284, 190), (300, 294, 200), (520, 286, 180), (770, 262, 170), (990, 290, 190)]
    s.append(kamm(nah, 345, "#3e5a3c", "#2f4730", H))
    for x, h in [(214, 24), (236, 30), (256, 22), (590, 26), (612, 32), (634, 24), (884, 28), (906, 22), (40, 26), (62, 20)]:
        s.append(baum(x, kamm_y(x, nah, 345) + 4, h, "#2f4a2e", "#243a24"))
    s.append(f'<g transform="translate(770 {z(kamm_y(770, nah, 345) + 2)}) scale(.92)">{turm("#b9a98a", "#857a66")}</g>')

    # Vordergrund mit Waystone
    s.append(P(f"0,316 120,308 260,316 420,312 600,318 760,310 960,317 960,{H} 0,{H}", "#24341f"))
    s.append(P(f"0,324 200,320 380,325 560,321 760,326 960,322 960,{H} 0,{H}", "#1c2a1d"))
    s.append(f'<g transform="translate(118 314)">{waystone(1.05)}</g>')
    s.append(gluehwuermer(rnd, 14, 20, 940, 268, 318))

    # Gleiter fliegt einmal quer durchs Bild
    s.append(f'<g class="flug" transform="translate(620 214)"><g class="wiegen"><g transform="scale(.62)">{gleiter_mit_figur()}</g></g></g>')

    # Titel wie der Banner bei einem neuen Ort im Spiel: klein darüber, groß der Name, Jade-Linie darunter
    s.append(text(480, 56, "ROBLOX DEVELOPER", 14, "#efe3cc", "middle", 600, 5, 'class="ein" opacity=".85"'))
    s.append(builder("DUMBOOJOO", 480, 72, 10, start=.15, takt=.09))
    s.append(f'<g class="linie"><path d="M330 149 V154 H630 V149" fill="none" stroke="{JADE}" stroke-width="2" stroke-linecap="square"/>'
             f'<path d="M330 154 H630" stroke="{JADE}" stroke-width="7" opacity=".25" filter="url(#weich)"/></g>')
    s.append(text(480, 182, "Building open worlds in Roblox", 17, TEXT, "middle", 400, .5, 'class="ein" style="animation-delay:1.4s" opacity=".92"'))

    s.append("</g>")
    s.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="#ffffff" stroke-opacity=".08"/>')
    return svg(W, H, "Dumboojoo: Roblox developer, building open worlds", "\n".join(s), css, defs)


if __name__ == "__main__":
    ZIEL.mkdir(exist_ok=True)
    inhalt = banner()
    (ZIEL / "banner.svg").write_text(inhalt, encoding="utf-8")
    print(f"assets/banner.svg  {len(inhalt) // 1024} KB")
