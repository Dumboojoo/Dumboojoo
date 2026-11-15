#!/usr/bin/env python3
"""Zeichnet alle Bilder des GitHub-Profils nach assets/.

Stil wie Breath of Freedom (STIL.md im Spiel-Repo): flache Facetten, links hell und rechts dunkel,
nur Wichtiges leuchtet in Jade. Medaillen, Gleiter, Drache und Ei sind aus dem Wiki des Spiels
übernommen (wiki/symbole.js, wiki/gegner.js), damit Profil und Spiel gleich aussehen.

Alle Bilder sind SVG mit eingebauter Bewegung (CSS), ohne Skripte, fremde Schriften oder Dateien:
GitHub zeigt Bilder abgeschottet an, dort geht nur, was in der Datei selbst steht.
Wer im System "Bewegung reduzieren" eingestellt hat, sieht alles still.

Aufruf (Mac): python3 tools/zeichne_profil.py   (Windows: py tools\\zeichne_profil.py)
"""
import math
import random
from pathlib import Path

ZIEL = Path(__file__).resolve().parent.parent / "assets"

# ---------- Farben aus STIL.md ----------
JADE = "#7fdcb3"
JADE_HELL = "#d6fff0"
GOLD = "#e0b450"
TEXT = "#ece6d6"
GEDAEMPFT = "#a8a191"
GRUND = "#16141b"
RAND = "#2c2933"
KACHEL = "#1f1c25"
SELTEN = {"u": "#6fae5b", "s": "#5b8fd6", "ss": "#a774e0", "l": "#e0b450"}
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


def gem(cx, cy, r, hell, dunkel, glanz=None):
    k, h = r * 0.866, r / 2
    s = P(f"{z(cx)},{z(cy - r)} {z(cx - k)},{z(cy - h)} {z(cx - k)},{z(cy + h)} {z(cx)},{z(cy + r)}", hell)
    s += P(f"{z(cx)},{z(cy - r)} {z(cx + k)},{z(cy - h)} {z(cx + k)},{z(cy + h)} {z(cx)},{z(cy + r)}", dunkel)
    if glanz:
        s += P(f"{z(cx - k * .7)},{z(cy - h * .9)} {z(cx - k * .15)},{z(cy - r * .8)} {z(cx - k * .35)},{z(cy - h * .1)}", glanz)
    return s


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
VERLAEUFE = """<radialGradient id="glowJade"><stop offset="0" stop-color="#7fdcb3" stop-opacity=".7"/><stop offset="1" stop-color="#7fdcb3" stop-opacity="0"/></radialGradient>
<radialGradient id="glowAmber"><stop offset="0" stop-color="#ffcf6a" stop-opacity=".85"/><stop offset="1" stop-color="#ffcf6a" stop-opacity="0"/></radialGradient>
<radialGradient id="vig" cx="50%" cy="45%" r="60%"><stop offset="0" stop-color="#2c2735"/><stop offset="1" stop-color="#16141b"/></radialGradient>"""

GRUND_CSS = f"""
text {{ font-family: {SANS}; }}
@keyframes puls {{ 0%, 100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
.puls {{ animation: puls 4s ease-in-out infinite; }}
.puls2 {{ animation: puls 4s ease-in-out 2s infinite; }}
@keyframes zeichnen {{ from {{ stroke-dashoffset: 1.05; }} to {{ stroke-dashoffset: 0; }} }}
.zieh {{ stroke-dasharray: 1 1.1; animation: zeichnen 1s cubic-bezier(.6, 0, .3, 1) both; }}
@keyframes auf {{ from {{ opacity: 0; transform: translateY(10px) scale(.8); }} to {{ opacity: 1; transform: none; }} }}
.auf {{ animation: auf .7s cubic-bezier(.2, .8, .3, 1.25) both; transform-box: fill-box; transform-origin: center; }}
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


def panel(w, h, rx=12):
    """Dunkles Fenster wie im Spiel, mit Jade-Ecken der Builders (STIL.md 6)."""
    i, k = 10, 22
    ecken = (f"M{i} {i + k}V{i}H{i + k} M{w - i - k} {i}H{w - i}V{i + k} "
             f"M{w - i} {h - i - k}V{h - i}H{w - i - k} M{i + k} {h - i}H{i}V{h - i - k}")
    return (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="{GRUND}" stroke="{RAND}"/>'
            f'<path d="{ecken}" fill="none" stroke="{JADE}" stroke-width="1.6" stroke-linecap="square" opacity=".55"/>')


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


# ---------- Figuren und Symbole aus dem Wiki ----------
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


MEDAILLE = {
    "stone": ("#b7ae98", "#7d7564", "#d9d2c0"),
    "bronze": ("#d09a5e", "#8f5f32", "#e8b880"),
    "silver": ("#e3e6ea", "#9aa1a9", "#eef1f4"),
    "gold": ("#f0cf6e", "#b48a2c", "#ffe08a"),
    "jade": ("#e2d8bd", "#a99f86", "#7fdcb3"),
}


def mische(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def erfolg_zeichen(kat, c):
    """Zeichen je Erfolgs-Kategorie (erfolgZeichen im Wiki), um die Mitte (50, 50)."""
    dunkel = "#1f1c25"
    if kat == "explore":
        return (f'<ellipse cx="50" cy="58" rx="13" ry="4.5" fill="none" stroke="{c}" stroke-width="2.4"/>'
                + P("46,58 46,39 50,34 54,39 54,58", c) + L("M50 40 V54", dunkel, 1.2))
    if kat == "growth":
        return L("M39 64 L50 56 L61 64 M39 55 L50 47 L61 55", c, 3.4) + funkel(50, 38, 6, c)
    if kat == "collect":
        return (P("35,41 50,45 50,63 35,59", c) + P("50,45 65,41 65,59 50,63", c, 'opacity=".75"')
                + L("M39 47 L47 49 M39 52 L47 54 M53 49 L61 47 M53 54 L61 52", dunkel, 1.1))
    if kat == "boss":
        return (P("42,46 58,46 57,59 50,65 43,59", c) + P("42,49 34,34 46,45", c) + P("58,49 66,34 54,45", c)
                + P("44,51 48.5,52 48,55 44.5,54", dunkel) + P("56,51 51.5,52 52,55 55.5,54", dunkel))
    if kat == "secret":
        return f'<text x="50" y="62" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="30" fill="{c}">?</text>'
    return ""


def medaille(stufe, kat):
    """Medaille wie medaille() im Wiki: Ring aus 8 Builder-Steinen, viewBox 100 x 100."""
    hell, dunkel, zeichen = MEDAILLE[stufe]

    def pt(a, r):
        return f"{z(50 + r * math.cos(math.radians(a)))},{z(50 + r * math.sin(math.radians(a)))}"

    s = ""
    if stufe == "jade":
        s += C(50, 50, 46, "url(#glowJade)", 'class="puls"')
    elif stufe == "gold":
        s += C(50, 50, 44, "url(#glowAmber)", 'class="puls" opacity=".5"')
    s += C(51.5, 51.5, 41, "#0d0b10", 'opacity=".55"')
    for k in range(8):
        a0 = k * 45 - 112.5 + 2.2
        a1 = a0 + 45 - 4.4
        mitte = (a0 + a1) / 2
        t = (1 - math.cos(math.radians(mitte + 135))) / 2
        s += P(f"{pt(a0, 41)} {pt(a1, 41)} {pt(a1, 27)} {pt(a0, 27)}", mische(hell, dunkel, t))
        s += P(f"{pt(a0, 41)} {pt(a1, 41)} {pt(a1, 37.5)} {pt(a0, 37.5)}", "rgba(255,255,255,.18)")
        if stufe == "jade":
            s += f'<path d="M{pt(mitte - 9, 34)} L{pt(mitte + 9, 34)}" stroke="{JADE}" stroke-width="1.6" stroke-linecap="round"/>'
    s += C(50, 50, 25, "#1f1c25") + C(50, 50, 23, "none", f'stroke="{dunkel}" stroke-width="1.2" opacity=".8"')
    return s + erfolg_zeichen(kat, zeichen)


def ei(hell, dunkel, glanz, muster=""):
    return (P("50,14 42,17 35,26 30,40 28,56 31,71 39,83 50,88", hell)
            + P("50,14 58,17 65,26 70,40 72,56 69,71 61,83 50,88", dunkel) + P("37,30 44,20 43,34", glanz) + muster)


def ur_ei():
    """Ancient Egg (Update 3): dunkel, goldene Adern, pulsiert."""
    return (C(50, 52, 34, "url(#glowAmber)", 'class="puls"')
            + ei("#4d4458", "#352e3e", "#71667e", L("M40 26 Q44 44 38 60 Q44 72 46 84 M60 24 Q56 40 62 54 Q58 70 56 84 M44 46 L56 50", GOLD, 1.4))
            + C(50, 52, 3, "#ffcf6a", 'class="puls2"'))


def schwert():
    """Einfaches Schwert der Builders (schwert() im Wiki), schräg, viewBox 100 x 100."""
    k = P("45,62 45,20 50,12 50,62", "#e9e3d3") + P("50,62 50,12 55,20 55,62", "#b9b2a2")
    k += L("M50 20 L50 60", JADE, 1.4, 'class="puls"')
    k += P("37,62 63,62 63,66 37,66", "#6f6a66") + P("50,62 63,62 63,66 50,66", "rgba(0,0,0,.2)")
    k += P("47,66 53,66 53,82 47,82", "#7a5532") + L("M47 71 L53 73 M47 77 L53 79", "rgba(0,0,0,.35)", 1.2)
    k += gem(50, 86, 4.5, "#6f6a66", "rgba(0,0,0,.35)")
    return f'<g transform="rotate(45 50 50) translate(0 2)">{k}</g>'


def drache():
    """Wyvern (drache() im Wiki), von der Seite, Füße bei y = 0, Kopf nach rechts."""
    h, d, bauch, haut, auge = "#4f7a3c", "#3a5c2c", "#d9b052", "#7aa85a", "#ffe08a"
    g = P("44,-112 60,-2 18,-62", "#56803f", 'opacity=".85"') + L("M30 -74 L44 -112 L60 -2", d, 6)
    g += L("M-24 -56 L-10 -30 L-26 -10 L-10 0", d, 10)
    g += L("M-36 -62 Q-80 -70 -110 -52 Q-140 -34 -168 -40", h, 14) + L("M-110 -52 Q-140 -34 -168 -40", h, 8) + P("-168,-40 -190,-54 -186,-30", d)
    g += P("-46,-66 -20,-88 30,-90 44,-70 34,-52 -36,-48", h) + P("-36,-48 34,-52 26,-44 -30,-42", bauch)
    g += L("M-14 -58 L0 -30 L-16 -10 L2 0", h, 13) + P("-2,0 10,0 6,-6", "#e9e3d3")
    g += P("40,-118 64,-2 14,-66", haut, 'opacity=".9"') + L("M40 -118 L52 -60 M40 -118 L30 -70", "#3a5c2c", 2)
    g += L("M32 -78 L40 -118 L64 -2", h, 8) + C(64, -2, 4, "#e9e3d3")
    g += L("M34 -84 Q60 -110 70 -140 Q76 -160 92 -170", h, 16)
    for x, y in [(44, -100), (56, -118), (64, -136), (72, -154)]:
        g += P(f"{x - 4},{y} {x - 10},{y - 10} {x + 2},{y - 4}", d)
    g += P("86,-178 128,-170 132,-160 100,-156 86,-162", h) + P("100,-156 132,-160 126,-152 102,-150", bauch)
    g += P("90,-178 70,-192 80,-184 96,-176", "#e9e3d3") + P("96,-178 82,-196 92,-188 102,-176", "#d9cfb2")
    g += C(106, -169, 3, auge) + C(106, -169, 1.2, "#2a2018")
    return g


def kachel(selten, inhalt):
    """Item-Kachel wie tile() im Wiki, viewBox 100 x 100."""
    return (f'<rect x="2" y="2" width="96" height="96" rx="14" fill="url(#vig)" stroke="{SELTEN[selten]}" stroke-width="2.5"/>'
            f'<ellipse cx="50" cy="90" rx="30" ry="4" fill="#000" opacity=".35"/>{inhalt}')


def gluehwuermer(rnd, n, x0, x1, y0, y1):
    s = ""
    for i in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        farbe = JADE if i % 3 else "#ffe08a"
        s += (f'<g class="gw" style="animation-delay:-{rnd.uniform(0, 5):.1f}s;animation-duration:{rnd.uniform(4, 7):.1f}s">'
              f'{C(x, y, 4, farbe, "opacity=\".25\"")}{C(x, y, 1.4, farbe)}</g>')
    return s


# ---------- 1. Banner ----------
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


# ---------- 2. Woran ich baue ----------
MERKMALE = [
    ("u", "glide", "Glide anywhere", "jump off any peak"),
    ("s", "sword", "Beat bosses", "giants that hit hard"),
    ("l", "egg", "Hatch dragons", "find eggs, raise a wyvern"),
    ("ss", "medal", "Earn medals", "45 achievements, 32 titles"),
]


def spielkarte():
    W, H = 960, 332
    defs = """<linearGradient id="tag" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5f86ad"/><stop offset=".5" stop-color="#9fc0d8"/><stop offset="1" stop-color="#f1d7a0"/></linearGradient>
<linearGradient id="unten" x1="0" y1="0" x2="0" y2="1"><stop offset=".6" stop-color="#16141b" stop-opacity="0"/><stop offset="1" stop-color="#16141b" stop-opacity=".55"/></linearGradient>
<radialGradient id="licht"><stop offset="0" stop-color="#fff4d6" stop-opacity=".8"/><stop offset="1" stop-color="#fff4d6" stop-opacity="0"/></radialGradient>
<clipPath id="bild"><rect x="22" y="22" width="380" height="288" rx="8"/></clipPath>
<clipPath id="balken"><rect x="816" y="293" width="120" height="9" rx="4.5"/></clipPath>"""
    css = """
@keyframes laden { from { transform: translateX(-40px); } to { transform: translateX(130px); } }
.laden { animation: laden 2.4s ease-in-out infinite; }
@keyframes blinken { 0%, 100% { opacity: 1; } 50% { opacity: .25; } }
.live { animation: blinken 1.6s ease-in-out infinite; }
"""
    rnd = random.Random(3)
    s = [panel(W, H)]

    # Bild links: der Green Reach am Nachmittag, Drache auf der Klippe, Ancient Egg auf einem Builder-Stein
    b = [f'<rect x="22" y="22" width="380" height="288" fill="url(#tag)"/>', C(110, 80, 120, "url(#licht)")]
    b.append(f'<g class="treiben">{wolke(40, 70, 120, "#ffffff", "#e3ecf2", .7)}{wolke(250, 52, 90, "#ffffff", "#e3ecf2", .55)}</g>')
    fern = [(60, 150, 70), (140, 118, 80), (230, 142, 70), (320, 110, 90), (410, 146, 70)]
    b.append(kamm(fern, 215, "#8fa6bd", "#7890a8", 312, 125, ("#eef3f6", "#c9d4dc")))
    huegel = [(40, 196, 110), (170, 180, 110), (300, 200, 120), (430, 190, 100)]
    b.append(kamm(huegel, 262, "#9cc46a", "#6e9a48", 312))
    for x, h in [(140, 26), (158, 32), (176, 24), (64, 22), (80, 28)]:
        b.append(baum(x, kamm_y(x, huegel, 262) + 5, h, "#5f8a3c", "#4a7030"))
    b.append(P("22,268 120,262 240,270 402,264 402,312 22,312", "#7fa65a"))
    b.append(P("22,284 160,280 300,286 402,282 402,312 22,312", "#6e9a48"))
    # Klippe rechts
    b.append(P("287,192 262,240 250,312 302,312 308,232", "#a39a88"))
    b.append(P("287,192 308,232 302,312 402,312 402,186", "#857c6b"))
    b.append(P("282,193 402,186 402,195 302,201", "#7fa65a"))
    b.append(L("M318 214 L330 252 L322 290 M360 206 L352 240 L364 276", "#6f675a", 1.6))
    b.append(f'<g transform="translate(352 192) scale(-.42 .42)">{drache()}</g>')
    # Ancient Egg auf dem Stein der Builders
    b.append(P("94,300 120,300 120,284 99,284", "#e2d8bd") + P("120,300 146,300 141,284 120,284", "#b7ae98"))
    b.append(L("M108 296 H114 V288 H126", JADE, 1.4, 'class="puls"'))
    b.append(f'<g transform="translate({z(120 - 50 * .62)} {z(285 - 88 * .62)}) scale(.62)">{ur_ei()}</g>')
    b.append(f'<g transform="translate(160 66)"><g class="wiegen"><g transform="scale(.44)">{gleiter_mit_figur()}</g></g></g>')
    b.append('<rect x="22" y="22" width="380" height="288" fill="url(#unten)"/>')
    s.append(f'<g clip-path="url(#bild)">{"".join(b)}</g>')
    s.append(f'<rect x="22" y="22" width="380" height="288" rx="8" fill="none" stroke="{RAND}"/>')

    # Text rechts
    x0 = 432
    s.append(C(x0 + 4, 45.5, 4, JADE, 'class="live"'))
    s.append(text(x0 + 16, 50, "NOW BUILDING", 13, GEDAEMPFT, "start", 600, 3))
    s.append(builder("BREATH OF FREEDOM", x0, 64, 4.6, anker="start", start=.2, takt=.05, dicke=.46))
    s.append(text(x0, 128, "An open-world adventure for Roblox. Climb any cliff,", 15.5, TEXT, "start", 400, 0, 'opacity=".92"'))
    s.append(text(x0, 150, "glide from any peak, beat bosses and grow stronger.", 15.5, TEXT, "start", 400, 0, 'opacity=".92"'))
    for i, (selten, art, titel, unter) in enumerate(MERKMALE):
        tx, ty = x0 + (i % 2) * 256, 170 + (i // 2) * 58
        inhalt = {"glide": gleiter, "sword": schwert, "egg": ur_ei, "medal": lambda: medaille("gold", "boss")}[art]()
        s.append(f'<g transform="translate({tx} {ty}) scale(.48)"><g class="auf" style="animation-delay:{.4 + i * .12:.2f}s">{kachel(selten, inhalt)}</g></g>')
        s.append(text(tx + 60, ty + 21, titel, 15, TEXT, "start", 700))
        s.append(text(tx + 60, ty + 39, unter, 12.5, GEDAEMPFT))
    # Stand: Planung fertig, Bauen kommt als Nächstes
    s.append(text(x0, 302, "PLANNING", 12, GEDAEMPFT, "start", 600, 2))
    s.append(f'<rect x="516" y="293" width="160" height="9" rx="4.5" fill="{JADE}"/>')
    s.append(f'<rect x="516" y="293" width="160" height="9" rx="4.5" fill="{JADE}" filter="url(#weich)" class="puls" opacity=".6"/>')
    s.append(text(684, 302, "done", 12, JADE, "start", 700))
    s.append(text(732, 302, "BUILDING", 12, GEDAEMPFT, "start", 600, 2))
    s.append(f'<rect x="816" y="293" width="120" height="9" rx="4.5" fill="{KACHEL}" stroke="{RAND}"/>')
    s.append(f'<g clip-path="url(#balken)"><rect class="laden" x="816" y="293" width="34" height="9" rx="4.5" fill="{JADE}" opacity=".7"/></g>')
    css += """
@keyframes treiben { from { transform: translateX(0); } to { transform: translateX(-40px); } }
.treiben { animation: treiben 30s ease-in-out infinite alternate; }
"""
    del rnd
    return svg(W, H, "Now building: Breath of Freedom, an open-world adventure for Roblox", "\n".join(s), css, defs)


# ---------- 3. Werkzeuge ----------
def werkzeuge():
    W, H = 960, 72
    eintraege = [
        ("Roblox Studio", "building", "cube"),
        ("Luau", "scripting", "code"),
        ("Rojo", "syncing code", "sync"),
        ("Blender", "3D models", "mesh"),
        ("Git", "saving versions", "git"),
    ]

    def symbol(art):
        if art == "cube":
            return (P("18,4 32,11 18,18 4,11", "#e2d8bd") + P("4,11 18,18 18,33 4,26", "#b7ae98") + P("18,18 32,11 32,26 18,33", "#8f8470")
                    + L("M4 11 L18 18 L32 11", JADE, 1.4, 'class="puls"'))
        if art == "code":
            return L("M13 5 H9 V15 L5 18 L9 21 V31 H13 M23 5 H27 V15 L31 18 L27 21 V31 H23", JADE, 2.4)
        if art == "sync":
            return (f'<path d="M7 15 A11.5 11.5 0 0 1 28 11" fill="none" stroke="{TEXT}" stroke-width="2.6" stroke-linecap="round"/>'
                    + P("31,5 31,15 22,13", TEXT)
                    + f'<path d="M29 21 A11.5 11.5 0 0 1 8 25" fill="none" stroke="{JADE}" stroke-width="2.6" stroke-linecap="round"/>'
                    + P("5,31 5,21 14,23", JADE))
        if art == "mesh":
            return (gem(18, 18, 15, "#ffb24a", "#c97a2a", "#ffd9a0")
                    + L("M18 3 L5 10.5 L18 18 L31 10.5 M18 18 V33 M5 25.5 L18 18 L31 25.5", "#7a4a1a", 1, 'opacity=".55"'))
        if art == "git":
            return (L("M11 7 V29 M25 13 Q25 22 11 24", JADE, 2.4)
                    + C(11, 7, 3.6, GRUND, f'stroke="{JADE}" stroke-width="2.2"') + C(11, 29, 3.6, GRUND, f'stroke="{JADE}" stroke-width="2.2"')
                    + C(25, 13, 3.6, GRUND, f'stroke="{TEXT}" stroke-width="2.2"'))
        return ""

    s = []
    for i, (name, unter, art) in enumerate(eintraege):
        x = i * 195
        s.append(f'<g transform="translate({x} 4)"><g class="auf" style="animation-delay:{.1 + i * .1:.1f}s">'
                 f'<rect x=".5" y=".5" width="179" height="63" rx="10" fill="{GRUND}" stroke="{RAND}"/>'
                 f'<g transform="translate(14 14)">{symbol(art)}</g>'
                 f'{text(62, 30, name, 15, TEXT, "start", 700)}{text(62, 48, unter, 12.5, GEDAEMPFT)}</g></g>')
    return svg(W, H, "Toolbox: Roblox Studio, Luau, Rojo, Blender, Git", "\n".join(s))


# ---------- 4. Abschluss ----------
def abschluss():
    W, H = 960, 120
    rnd = random.Random(11)
    defs = f'<clipPath id="rahmen"><rect width="{W}" height="{H}" rx="12"/></clipPath>'
    css = """
@keyframes wind { 0%, 100% { transform: skewX(-5deg); } 50% { transform: skewX(5deg); } }
.wind { animation: wind 4s ease-in-out infinite; transform-box: fill-box; transform-origin: 50% 100%; }
.wind2 { animation: wind 4s ease-in-out -1.3s infinite; transform-box: fill-box; transform-origin: 50% 100%; }
.wind3 { animation: wind 4s ease-in-out -2.6s infinite; transform-box: fill-box; transform-origin: 50% 100%; }
"""
    s = [panel(W, H), f'<g clip-path="url(#rahmen)">']
    for i in range(30):
        s.append(C(rnd.uniform(20, 940), rnd.uniform(14, 60), rnd.choice([.6, .8, 1.1]), "#f3eee2", f'class="{["f1", "f2", "f3"][i % 3]}" opacity=".6"'))
    for gruppe, k in enumerate(["wind", "wind2", "wind3"]):
        halme = ""
        for _ in range(70):
            x, h = rnd.uniform(0, W), rnd.uniform(8, 22)
            farbe = rnd.choice(["#2f4a2e", "#3e5a3c", "#284026"])
            halme += P(f"{z(x - 2)},{H} {z(x + rnd.uniform(-3, 3))},{z(H - h)} {z(x + 2)},{H}", farbe)
        s.append(f'<g class="{k}">{halme}</g>')
    s.append(gluehwuermer(rnd, 10, 30, 930, 102, 114))  # unter dem Text, damit nichts ihn verdeckt
    s.append(f'<g transform="translate(110 104)">{waystone(1.25)}</g>')
    s.append("</g>")
    s.append(builder("WAYSTONE WOKEN", 500, 34, 3.4, start=.2, takt=.05, dicke=.5))
    s.append(text(500, 86, "Thanks for stopping by, traveler. You can fast travel back here anytime.", 14.5, GEDAEMPFT, "middle"))
    return svg(W, H, "Waystone woken. Thanks for stopping by, traveler.", "\n".join(s), css, defs)


# ---------- 5. Ei (Versteck) ----------
def versteck():
    W, H = 240, 220
    css = """
@keyframes wackeln { 0%, 76%, 100% { transform: rotate(0deg); } 80% { transform: rotate(-5deg); } 84% { transform: rotate(5deg); }
  88% { transform: rotate(-3deg); } 92% { transform: rotate(2deg); } }
.wackeln { animation: wackeln 5s ease-in-out 1s infinite; transform-box: fill-box; transform-origin: 50% 100%; }
"""
    s = [C(120, 112, 100, "url(#glowAmber)", 'class="puls" opacity=".55"')]
    s.append(P("70,206 120,206 120,180 78,180", "#e2d8bd") + P("120,206 170,206 162,180 120,180", "#b7ae98"))
    s.append(P("78,180 120,180 120,172 84,172", "#ece4cc") + P("120,180 162,180 156,172 120,172", "#c9bfa3"))
    s.append(L("M96 200 H110 V186 H132 V196 H146", JADE, 1.8, 'class="puls"'))
    s.append(f'<g transform="translate({z(120 - 50 * 1.7)} {z(174 - 88 * 1.7)}) scale(1.7)"><g class="wackeln">{ur_ei()}</g></g>')
    for x, y, g, k in [(52, 70, 7, "f1"), (190, 52, 6, "f2"), (200, 132, 5, "f3"), (40, 140, 4, "f2"), (150, 22, 4, "f3")]:
        s.append(funkel(x, y, g, "#ffe08a", f'class="{k}"'))
    return svg(W, H, "An Ancient Egg on a Builder stone, glowing", "\n".join(s), css)


if __name__ == "__main__":
    ZIEL.mkdir(exist_ok=True)
    for name, bild in [("banner", banner), ("now-building", spielkarte),
                       ("toolbox", werkzeuge), ("footer", abschluss), ("egg", versteck)]:
        inhalt = bild()
        (ZIEL / f"{name}.svg").write_text(inhalt, encoding="utf-8")
        print(f"assets/{name}.svg  {len(inhalt) // 1024} KB")
