from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, Line, Polygon, String, Circle, PolyLine
from reportlab.graphics import renderPDF
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import math

# ── Color Palette ──────────────────────────────────────────────────────────────
DARK_BG     = colors.HexColor("#0D1B2A")
ACCENT      = colors.HexColor("#00D4FF")
ACCENT2     = colors.HexColor("#FF6B35")
GOLD        = colors.HexColor("#FFD700")
GREEN_BULL  = colors.HexColor("#00E676")
RED_BEAR    = colors.HexColor("#FF1744")
LIGHT_TEXT  = colors.HexColor("#E0E0E0")
MID_GRAY    = colors.HexColor("#607080")
PANEL_BG    = colors.HexColor("#111F2E")
WHITE       = colors.white

W, H = A4   # 595 x 842 pts

# ── Styles ─────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def style(name, **kw):
    s = ParagraphStyle(name, **kw)
    return s

TITLE_STYLE = style("CourseTitle", fontSize=32, leading=38, textColor=ACCENT,
                    fontName="Helvetica-Bold", alignment=TA_CENTER)
SUBTITLE_STYLE = style("CourseSubtitle", fontSize=16, leading=22,
                       textColor=LIGHT_TEXT, fontName="Helvetica", alignment=TA_CENTER)
H1 = style("H1", fontSize=20, leading=26, textColor=ACCENT,
           fontName="Helvetica-Bold", spaceAfter=8)
H2 = style("H2", fontSize=15, leading=20, textColor=GOLD,
           fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=12)
H3 = style("H3", fontSize=12, leading=16, textColor=ACCENT2,
           fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=8)
BODY = style("Body", fontSize=10, leading=15, textColor=LIGHT_TEXT,
             fontName="Helvetica", spaceAfter=6, alignment=TA_JUSTIFY)
BULLET = style("Bullet", fontSize=10, leading=14, textColor=LIGHT_TEXT,
               fontName="Helvetica", leftIndent=16, spaceAfter=3,
               firstLineIndent=-12)
CAPTION = style("Caption", fontSize=8, leading=11, textColor=MID_GRAY,
                fontName="Helvetica-Oblique", alignment=TA_CENTER)
CALLOUT = style("Callout", fontSize=10, leading=15, textColor=GOLD,
                fontName="Helvetica-Bold", alignment=TA_CENTER)
TOC_STYLE = style("TOC", fontSize=11, leading=18, textColor=LIGHT_TEXT,
                  fontName="Helvetica")
TOC_NUM   = style("TOCNum", fontSize=11, leading=18, textColor=ACCENT,
                  fontName="Helvetica-Bold")

# ── Helper: dark background page canvas ───────────────────────────────────────
def dark_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # subtle grid lines
    canvas.setStrokeColor(colors.HexColor("#1A2E42"))
    canvas.setLineWidth(0.3)
    for x in range(0, int(W), 40):
        canvas.line(x, 0, x, H)
    for y in range(0, int(H), 40):
        canvas.line(0, y, W, y)
    # footer bar
    canvas.setFillColor(PANEL_BG)
    canvas.rect(0, 0, W, 22, fill=1, stroke=0)
    canvas.setFillColor(MID_GRAY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(30, 7, "Elliott Wave & MACD Divergences — Complete Trading Course")
    canvas.drawRightString(W - 30, 7, f"Page {doc.page}")
    canvas.restoreState()

def cover_page(canvas, doc):
    canvas.saveState()
    # deep gradient simulation — two rects
    canvas.setFillColor(colors.HexColor("#050D18"))
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0A1628"))
    canvas.rect(0, H*0.3, W, H*0.7, fill=1, stroke=0)
    # accent bar top
    canvas.setFillColor(ACCENT)
    canvas.rect(0, H - 6, W, 6, fill=1, stroke=0)
    # accent bar bottom
    canvas.setFillColor(ACCENT2)
    canvas.rect(0, 0, W, 6, fill=1, stroke=0)
    canvas.restoreState()

# ── Flowable: Horizontal rule ──────────────────────────────────────────────────
def hr(color=ACCENT, width=1):
    return HRFlowable(width="100%", thickness=width, color=color, spaceAfter=6, spaceBefore=6)

# ── Flowable: colored box (callout) ───────────────────────────────────────────
class ColorBox(Flowable):
    def __init__(self, text, bg=PANEL_BG, border=ACCENT, width=None, pad=10):
        super().__init__()
        self.text = text
        self.bg = bg
        self.border = border
        self._w = width or (W - 80)
        self.pad = pad

    def wrap(self, availW, availH):
        self._w = availW
        return self._w, 50

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self._w, 44, 6, fill=1, stroke=0)
        c.setStrokeColor(self.border)
        c.setLineWidth(1.5)
        c.roundRect(0, 0, self._w, 44, 6, fill=0, stroke=1)
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(12, 27, "⚡ KEY POINT")
        c.setFillColor(LIGHT_TEXT)
        c.setFont("Helvetica", 9)
        # simple text wrap
        words = self.text.split()
        line, lines = "", []
        for w in words:
            test = line + " " + w if line else w
            if c.stringWidth(test, "Helvetica", 9) < self._w - 28:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
        y = 16
        for l in lines[:1]:
            c.drawString(12, y, l)
        c.restoreState()

# ── Chart: Elliott Wave impulse diagram ───────────────────────────────────────
class ElliottImpulseChart(Flowable):
    def __init__(self, w=440, h=200):
        super().__init__()
        self._w, self._h = w, h

    def wrap(self, aw, ah):
        return self._w, self._h

    def draw(self):
        c = self.canv
        c.saveState()
        # background
        c.setFillColor(PANEL_BG)
        c.roundRect(0, 0, self._w, self._h, 8, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(0, 0, self._w, self._h, 8, fill=0, stroke=1)

        # wave points (x, y) normalized to chart
        pts = [(30,40),(100,140),(150,80),(230,170),(280,110),(340,190),(395,85)]
        labels = ["0","1","2","3","4","5","A"]
        wave_colors = [GREEN_BULL, RED_BEAR, GREEN_BULL, RED_BEAR, GREEN_BULL, RED_BEAR]

        for i in range(len(pts)-1):
            x1,y1 = pts[i]; x2,y2 = pts[i+1]
            col = wave_colors[i] if i < len(wave_colors) else MID_GRAY
            c.setStrokeColor(col)
            c.setLineWidth(2.5)
            c.line(x1, y1, x2, y2)

        # dots and labels
        for i,(x,y) in enumerate(pts):
            c.setFillColor(WHITE)
            c.circle(x, y, 4, fill=1, stroke=0)
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 9)
            offset_y = -14 if i % 2 == 0 else 8
            c.drawCentredString(x, y + offset_y, labels[i])

        # annotation arrows for waves 1,3,5
        c.setFillColor(GREEN_BULL)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(65, 155, "Wave 1")
        c.drawCentredString(195, 185, "Wave 3 (Longest)")
        c.drawCentredString(365, 195, "Wave 5")
        c.setFillColor(RED_BEAR)
        c.drawCentredString(128, 68, "Wave 2")
        c.drawCentredString(308, 98, "Wave 4")

        # title
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self._w/2, self._h - 14, "Elliott Wave Impulse Structure (5-Wave Motive)")
        c.restoreState()


# ── Chart: Elliott Wave corrective (ABC) ──────────────────────────────────────
class ElliottCorrectiveChart(Flowable):
    def __init__(self, w=440, h=200):
        super().__init__()
        self._w, self._h = w, h

    def wrap(self, aw, ah):
        return self._w, self._h

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(PANEL_BG)
        c.roundRect(0, 0, self._w, self._h, 8, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(0, 0, self._w, self._h, 8, fill=0, stroke=1)

        pts = [(30,160),(160,60),(250,130),(380,30)]
        labels = ["0","A","B","C"]
        wave_colors = [RED_BEAR, GREEN_BULL, RED_BEAR]

        for i in range(len(pts)-1):
            x1,y1 = pts[i]; x2,y2 = pts[i+1]
            col = wave_colors[i]
            c.setStrokeColor(col)
            c.setLineWidth(2.5)
            c.line(x1, y1, x2, y2)

        for i,(x,y) in enumerate(pts):
            c.setFillColor(WHITE)
            c.circle(x, y, 4, fill=1, stroke=0)
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 9)
            offset_y = 10 if i in [0,2] else -14
            c.drawCentredString(x, y + offset_y, labels[i])

        c.setFillColor(RED_BEAR)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(95, 95, "Wave A (Down)")
        c.drawCentredString(380, 100, "Wave C (Down)")
        c.setFillColor(GREEN_BULL)
        c.drawCentredString(210, 125, "Wave B (Up)")

        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self._w/2, self._h - 14, "Elliott Wave Corrective Structure (A-B-C Flat/Zigzag)")
        c.restoreState()

# ── Chart: MACD Divergence diagram ────────────────────────────────────────────
class MACDDivergenceChart(Flowable):
    def __init__(self, w=440, h=260, bull=True):
        super().__init__()
        self._w, self._h = w, h
        self.bull = bull

    def wrap(self, aw, ah):
        return self._w, self._h

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(PANEL_BG)
        c.roundRect(0, 0, self._w, self._h, 8, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(0, 0, self._w, self._h, 8, fill=0, stroke=1)

        price_h = 140
        macd_h  = 80
        macd_y  = 20
        price_y = macd_y + macd_h + 16
        sep_y   = macd_y + macd_h + 8

        # separator
        c.setStrokeColor(MID_GRAY)
        c.setLineWidth(0.5)
        c.setDash([4, 3])
        c.line(20, sep_y, self._w - 20, sep_y)
        c.setDash([])

        if self.bull:
            # Bullish divergence: price makes lower lows, MACD makes higher lows
            price_pts = [(30,price_y+30),(90,price_y+90),(160,price_y+45),(230,price_y+100),(310,price_y+55),(380,price_y+105)]
            macd_bars_h  = [-28, -38, -22, -16, -12, -6]  # bars heights (negative = below zero)
            title = "Bullish Divergence: Price Lower Lows, MACD Higher Lows"
            div_color = GREEN_BULL
        else:
            # Bearish divergence: price makes higher highs, MACD makes lower highs
            price_pts = [(30,price_y+90),(90,price_y+30),(160,price_y+70),(230,price_y+20),(310,price_y+60),(380,price_y+15)]
            macd_bars_h  = [28, 38, 22, 16, 12, 6]
            title = "Bearish Divergence: Price Higher Highs, MACD Lower Highs"
            div_color = RED_BEAR

        # Draw price candles (simplified as line)
        c.setStrokeColor(LIGHT_TEXT)
        c.setLineWidth(1.8)
        for i in range(len(price_pts)-1):
            x1,y1 = price_pts[i]; x2,y2 = price_pts[i+1]
            c.line(x1, y1, x2, y2)

        # Mark the divergence pivot lows/highs
        pivot_idx = [1, 3, 5] if self.bull else [1, 3, 5]
        for i in pivot_idx:
            x,y = price_pts[i]
            c.setFillColor(div_color)
            c.circle(x, y, 4, fill=1, stroke=0)

        # Draw MACD histogram bars
        zero_line = macd_y + macd_h // 2
        bar_xs = [30, 90, 160, 230, 310, 380]
        for i, (bx, bh) in enumerate(zip(bar_xs, macd_bars_h)):
            col = GREEN_BULL if bh > 0 else RED_BEAR
            c.setFillColor(col)
            bar_rect_h = abs(bh)
            if bh < 0:
                c.rect(bx-10, zero_line - bar_rect_h, 20, bar_rect_h, fill=1, stroke=0)
            else:
                c.rect(bx-10, zero_line, 20, bar_rect_h, fill=1, stroke=0)

        # Zero line for MACD
        c.setStrokeColor(MID_GRAY)
        c.setLineWidth(0.8)
        c.line(20, zero_line, self._w-20, zero_line)

        # Divergence trendlines on price and MACD
        if self.bull:
            px = [price_pts[1][0], price_pts[5][0]]
            py = [price_pts[1][1], price_pts[5][1]]
            mx = [bar_xs[1], bar_xs[5]]
            my = [zero_line - abs(macd_bars_h[1]), zero_line - abs(macd_bars_h[5])]
        else:
            px = [price_pts[1][0], price_pts[5][0]]
            py = [price_pts[1][1], price_pts[5][1]]
            mx = [bar_xs[1], bar_xs[5]]
            my = [zero_line + macd_bars_h[1], zero_line + macd_bars_h[5]]

        c.setStrokeColor(div_color)
        c.setLineWidth(1.5)
        c.setDash([5, 3])
        c.line(px[0], py[0], px[1], py[1])
        c.line(mx[0], my[0], mx[1], my[1])
        c.setDash([])

        # Labels
        c.setFillColor(LIGHT_TEXT)
        c.setFont("Helvetica", 7)
        c.drawString(22, price_y + price_h - 5, "PRICE")
        c.drawString(22, macd_y + macd_h - 5, "MACD")

        # Title
        c.setFillColor(div_color)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(self._w/2, self._h - 12, title)
        c.restoreState()

# ── Chart: Wave + MACD combo (integration) ────────────────────────────────────
class WaveMACDComboChart(Flowable):
    def __init__(self, w=440, h=300):
        super().__init__()
        self._w, self._h = w, h

    def wrap(self, aw, ah):
        return self._w, self._h

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(PANEL_BG)
        c.roundRect(0, 0, self._w, self._h, 8, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(0, 0, self._w, self._h, 8, fill=0, stroke=1)

        # Layout
        macd_h = 85
        price_h = 170
        macd_y = 18
        price_y = macd_y + macd_h + 12
        zero_macd = macd_y + macd_h // 2

        # Separator
        c.setStrokeColor(MID_GRAY)
        c.setLineWidth(0.5)
        c.setDash([4,3])
        c.line(20, price_y - 6, self._w - 20, price_y - 6)
        c.setDash([])

        # Elliott wave on price panel (full 5-wave + ABC)
        wave_pts = [
            (25, price_y+30),   # 0
            (80, price_y+110),  # 1
            (120, price_y+70),  # 2
            (195, price_y+160), # 3
            (240, price_y+115), # 4
            (305, price_y+185), # 5
            (350, price_y+135), # A
            (385, price_y+155), # B
            (415, price_y+95),  # C
        ]
        wave_labels = ["0","1","2","3","4","5","A","B","C"]
        wave_cols   = [GREEN_BULL,RED_BEAR,GREEN_BULL,RED_BEAR,GREEN_BULL,RED_BEAR,GREEN_BULL,RED_BEAR]

        for i in range(len(wave_pts)-1):
            c.setStrokeColor(wave_cols[i])
            c.setLineWidth(2)
            c.line(wave_pts[i][0], wave_pts[i][1], wave_pts[i+1][0], wave_pts[i+1][1])

        for i,(x,y) in enumerate(wave_pts):
            c.setFillColor(WHITE)
            c.circle(x, y, 3, fill=1, stroke=0)
            c.setFillColor(GOLD)
            c.setFont("Helvetica-Bold", 8)
            off = -12 if i % 2 == 0 else 8
            c.drawCentredString(x, y + off, wave_labels[i])

        # MACD histogram synced with waves
        bar_xs    = [25, 80, 120, 195, 240, 305, 350, 385, 415]
        macd_vals = [-8, 22, 8, 36, 14, 28, -18, -8, -30]

        for bx, bv in zip(bar_xs, macd_vals):
            col = GREEN_BULL if bv > 0 else RED_BEAR
            c.setFillColor(col)
            bh = abs(bv) * 0.9
            if bv < 0:
                c.rect(bx-9, zero_macd - bh, 18, bh, fill=1, stroke=0)
            else:
                c.rect(bx-9, zero_macd, 18, bh, fill=1, stroke=0)

        # MACD zero line
        c.setStrokeColor(MID_GRAY)
        c.setLineWidth(0.8)
        c.line(20, zero_macd, self._w-20, zero_macd)

        # Divergence on wave 5 vs wave 3
        c.setStrokeColor(ACCENT2)
        c.setLineWidth(1.5)
        c.setDash([5, 3])
        # price: wave 3 high to wave 5 high → higher high
        c.line(195, wave_pts[3][1], 305, wave_pts[5][1])
        # MACD: bar at 3 lower than bar at 1 → lower high (bearish div)
        m3y = zero_macd + 36 * 0.9
        m5y = zero_macd + 28 * 0.9
        c.line(195, m3y, 305, m5y)
        c.setDash([])

        c.setFillColor(ACCENT2)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(200, price_y + price_h - 8, "⚠ Bearish Div: Wave 5 top confirmation")

        # Labels
        c.setFillColor(LIGHT_TEXT)
        c.setFont("Helvetica", 7)
        c.drawString(22, price_y + price_h - 1, "PRICE (Elliott Wave)")
        c.drawString(22, macd_y + macd_h - 2, "MACD Histogram")

        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(self._w/2, self._h - 12, "Elliott Wave + MACD Divergence Integration")
        c.restoreState()

# ── Chart: Fibonacci levels on wave ───────────────────────────────────────────
class FibChart(Flowable):
    def __init__(self, w=440, h=200):
        super().__init__()
        self._w, self._h = w, h

    def wrap(self, aw, ah):
        return self._w, self._h

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(PANEL_BG)
        c.roundRect(0, 0, self._w, self._h, 8, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(0, 0, self._w, self._h, 8, fill=0, stroke=1)

        # Simple wave from low to high, fib retracement lines
        low_y  = 30
        high_y = 170
        wave_x1 = 50
        wave_x2 = 200
        retrace_x = 370

        total_range = high_y - low_y  # in pts

        fibs = [
            (0.0,   "0.0%",   GOLD),
            (0.236, "23.6%",  MID_GRAY),
            (0.382, "38.2%",  GREEN_BULL),
            (0.5,   "50.0%",  ACCENT),
            (0.618, "61.8%",  ACCENT2),
            (0.786, "78.6%",  MID_GRAY),
            (1.0,   "100%",   GOLD),
        ]

        # up wave
        c.setStrokeColor(GREEN_BULL)
        c.setLineWidth(2.5)
        c.line(wave_x1, low_y, wave_x2, high_y)

        # fib horizontal lines
        for ratio, label, col in fibs:
            y = high_y - ratio * total_range
            c.setStrokeColor(col)
            c.setLineWidth(0.8 if ratio not in [0, 1] else 1.5)
            c.setDash([4,3] if ratio not in [0,1] else [])
            c.line(wave_x2, y, retrace_x + 30, y)
            c.setDash([])
            c.setFillColor(col)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(retrace_x + 35, y - 4, label)

        # retracement arrow down
        c.setStrokeColor(RED_BEAR)
        c.setLineWidth(2)
        ret_y = high_y - 0.618 * total_range
        c.line(wave_x2, high_y, retrace_x, ret_y)
        c.setFillColor(RED_BEAR)
        c.circle(retrace_x, ret_y, 4, fill=1, stroke=0)

        c.setFillColor(ACCENT2)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(270, ret_y + 6, "Wave 2 retraces ~61.8%")

        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self._w/2, self._h - 12, "Fibonacci Retracement Levels in Elliott Waves")
        c.restoreState()


# ── Chart: Risk/Reward trade setup ────────────────────────────────────────────
class TradeSetupChart(Flowable):
    def __init__(self, w=440, h=200):
        super().__init__()
        self._w, self._h = w, h

    def wrap(self, aw, ah):
        return self._w, self._h

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(PANEL_BG)
        c.roundRect(0, 0, self._w, self._h, 8, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(0, 0, self._w, self._h, 8, fill=0, stroke=1)

        # price context
        entry_y  = 100
        sl_y     = 70
        tp1_y    = 130
        tp2_y    = 155
        tp3_y    = 175

        line_x1 = 60
        line_x2 = self._w - 30

        # zones
        c.setFillColor(colors.HexColor("#FF17441A"))
        c.rect(line_x1, sl_y, line_x2 - line_x1, entry_y - sl_y, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#00E6761A"))
        c.rect(line_x1, entry_y, line_x2 - line_x1, tp3_y - entry_y, fill=1, stroke=0)

        for y, label, col in [
            (entry_y, "ENTRY", GOLD),
            (sl_y,    "STOP LOSS", RED_BEAR),
            (tp1_y,   "TP1  1:1", GREEN_BULL),
            (tp2_y,   "TP2  1:2", GREEN_BULL),
            (tp3_y,   "TP3  1:3", GREEN_BULL),
        ]:
            c.setStrokeColor(col)
            c.setLineWidth(1.2)
            c.setDash([5, 3] if "TP" in label else [])
            c.line(line_x1, y, line_x2, y)
            c.setDash([])
            c.setFillColor(col)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(line_x1 - 58, y - 4, label)

        # price candles (simplified)
        candle_xs = [90, 130, 170, 215, 260, 305, 350, 390]
        candle_ys = [90, 85, 95, 88, 97, 100, 108, 118]
        c.setStrokeColor(LIGHT_TEXT)
        c.setLineWidth(1.5)
        for i in range(len(candle_xs)-1):
            c.line(candle_xs[i], candle_ys[i], candle_xs[i+1], candle_ys[i+1])

        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self._w/2, self._h - 12, "Trade Setup: Entry, Stop Loss & Take Profit Levels")
        c.restoreState()

# ── Content builder helpers ────────────────────────────────────────────────────
def b(text): return f"<b>{text}</b>"
def it(text): return f"<i>{text}</i>"
def accent(text): return f'<font color="#00D4FF">{text}</font>'
def gold(text): return f'<font color="#FFD700">{text}</font>'
def red(text): return f'<font color="#FF1744">{text}</font>'
def green(text): return f'<font color="#00E676">{text}</font>'

def p(text, sty=None): return Paragraph(text, sty or BODY)
def h1(text): return Paragraph(text, H1)
def h2(text): return Paragraph(text, H2)
def h3(text): return Paragraph(text, H3)
def sp(n=6): return Spacer(1, n)
def bullet(text): return Paragraph(f"• {text}", BULLET)

def table2(rows, col_widths=None):
    col_widths = col_widths or [220, 220]
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1A3048")),
        ("TEXTCOLOR",  (0,0), (-1,0), ACCENT),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0), 9),
        ("BACKGROUND", (0,1), (-1,-1), PANEL_BG),
        ("TEXTCOLOR",  (0,1), (-1,-1), LIGHT_TEXT),
        ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",   (0,1), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[PANEL_BG, colors.HexColor("#0F1E2E")]),
        ("GRID",       (0,0), (-1,-1), 0.4, MID_GRAY),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",(0,0), (-1,-1), 8),
    ]))
    return t

def summary_box(items):
    rows = [[Paragraph(b(accent("✔ Chapter Summary")), BODY)]]
    for item in items:
        rows.append([Paragraph(f"  • {item}", BODY)])
    t = Table(rows, colWidths=[W - 80])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,0),  colors.HexColor("#1A3048")),
        ("BACKGROUND",  (0,1),(-1,-1), PANEL_BG),
        ("BOX",         (0,0),(-1,-1), 1.5, ACCENT),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING", (0,0),(-1,-1), 10),
    ]))
    return t

# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════
def build_cover():
    elems = []
    elems.append(Spacer(1, 80))
    elems.append(Paragraph("ELLIOTT WAVE", TITLE_STYLE))
    elems.append(Paragraph("&amp;", style("amp", fontSize=24, leading=30,
                 textColor=ACCENT2, fontName="Helvetica-Bold", alignment=TA_CENTER)))
    elems.append(Paragraph("MACD DIVERGENCES", TITLE_STYLE))
    elems.append(sp(12))
    elems.append(hr(ACCENT2, 2))
    elems.append(sp(10))
    elems.append(Paragraph("Complete Professional Trading Course", SUBTITLE_STYLE))
    elems.append(sp(6))
    elems.append(Paragraph("Master Wave Theory, Divergence Trading &amp; High-Probability Setups", SUBTITLE_STYLE))
    elems.append(sp(40))
    elems.append(Paragraph(gold("─── COURSE MODULES ───"), style("mod", fontSize=11, leading=18,
                 textColor=GOLD, fontName="Helvetica-Bold", alignment=TA_CENTER)))
    elems.append(sp(10))
    modules = [
        "Module 1 — Elliott Wave Theory Foundations",
        "Module 2 — Advanced Wave Structures",
        "Module 3 — MACD Indicator Deep Dive",
        "Module 4 — Divergence Trading Strategies",
        "Module 5 — Integrating Waves with MACD",
        "Module 6 — Entry, Exit &amp; Risk Management",
        "Module 7 — Multi-Timeframe Analysis",
        "Module 8 — Live Trade Examples &amp; Checklists",
    ]
    for m in modules:
        elems.append(Paragraph(m, style("moditem", fontSize=10, leading=16,
                     textColor=LIGHT_TEXT, fontName="Helvetica", alignment=TA_CENTER)))
    elems.append(sp(40))
    elems.append(hr(ACCENT, 1))
    elems.append(sp(8))
    elems.append(Paragraph("Advanced Technical Analysis Series  |  2026 Edition",
                 style("edition", fontSize=9, leading=13, textColor=MID_GRAY,
                       fontName="Helvetica", alignment=TA_CENTER)))
    elems.append(PageBreak())
    return elems

# ══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ══════════════════════════════════════════════════════════════════════════════
def build_toc():
    elems = []
    elems.append(sp(20))
    elems.append(h1("Table of Contents"))
    elems.append(hr())
    elems.append(sp(10))

    toc_items = [
        ("Module 1", "Elliott Wave Theory Foundations", "3"),
        ("  1.1", "History & R.N. Elliott's Discovery", "3"),
        ("  1.2", "The Principle of Waves", "3"),
        ("  1.3", "Motive Waves (Impulse) — 5-Wave Structure", "4"),
        ("  1.4", "Corrective Waves — A-B-C Patterns", "4"),
        ("  1.5", "Wave Degree & Labeling", "5"),
        ("Module 2", "Advanced Wave Structures", "6"),
        ("  2.1", "Wave Extensions", "6"),
        ("  2.2", "Diagonal Triangles", "6"),
        ("  2.3", "Complex Corrections (WXY, WXYXZ)", "7"),
        ("  2.4", "Fibonacci Relationships in Waves", "7"),
        ("Module 3", "MACD Indicator Deep Dive", "8"),
        ("  3.1", "MACD Construction & Settings", "8"),
        ("  3.2", "Signal Line & Histogram", "8"),
        ("  3.3", "MACD Zero-Line Crossovers", "9"),
        ("  3.4", "Momentum Reading with MACD", "9"),
        ("Module 4", "Divergence Trading Strategies", "10"),
        ("  4.1", "What is Divergence?", "10"),
        ("  4.2", "Regular Bullish Divergence", "10"),
        ("  4.3", "Regular Bearish Divergence", "11"),
        ("  4.4", "Hidden Divergence", "11"),
        ("  4.5", "Divergence Strength & Reliability", "12"),
        ("Module 5", "Integrating Elliott Waves with MACD", "13"),
        ("  5.1", "Confirming Wave 3 with MACD", "13"),
        ("  5.2", "Spotting Wave 5 Failure via Bearish Divergence", "13"),
        ("  5.3", "Wave C Bottom via Bullish Divergence", "14"),
        ("Module 6", "Entry, Exit & Risk Management", "15"),
        ("  6.1", "Entry Triggers & Confirmation", "15"),
        ("  6.2", "Stop Loss Placement", "15"),
        ("  6.3", "Take Profit & Targets", "16"),
        ("  6.4", "Position Sizing", "16"),
        ("Module 7", "Multi-Timeframe Analysis", "17"),
        ("  7.1", "Top-Down Wave Counting", "17"),
        ("  7.2", "Aligning MACD Across Timeframes", "17"),
        ("Module 8", "Trade Examples & Checklists", "18"),
        ("  8.1", "Bullish Setup Example", "18"),
        ("  8.2", "Bearish Setup Example", "18"),
        ("  8.3", "Master Trading Checklist", "19"),
        ("Appendix", "Quick Reference — Rules & Guidelines", "20"),
    ]

    for num, title, pg in toc_items:
        is_module = num.startswith("Module") or num == "Appendix"
        row_style = TOC_NUM if is_module else TOC_STYLE
        txt = f"{b(num)}  {b(title)}" if is_module else f"{num}  {title}"
        row = [[Paragraph(txt, row_style), Paragraph(pg, style("pgnum", fontSize=11,
                leading=18, textColor=ACCENT if is_module else MID_GRAY,
                fontName="Helvetica-Bold" if is_module else "Helvetica", alignment=TA_CENTER))]]
        t = Table(row, colWidths=[W-110, 30])
        t.setStyle(TableStyle([
            ("TOPPADDING",(0,0),(-1,-1), 2),
            ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ]))
        elems.append(t)

    elems.append(PageBreak())
    return elems

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 1 — Elliott Wave Foundations
# ══════════════════════════════════════════════════════════════════════════════
def build_module1():
    e = []
    e.append(sp(10))
    e.append(h1("Module 1 — Elliott Wave Theory Foundations"))
    e.append(hr())

    e.append(h2("1.1  History & R.N. Elliott's Discovery"))
    e.append(p("Ralph Nelson Elliott (1871–1948) was an American accountant who, while recovering from illness, devoted years to studying stock market data. In 1938 he published " + it("The Wave Principle") + ", proposing that financial markets move in predictable, repetitive patterns driven by collective investor psychology."))
    e.append(p("Elliott observed that market price action alternates between " + b(green("impulsive")) + " (trend-following) and " + b(red("corrective")) + " (counter-trend) phases. These patterns nest fractally — the same patterns appear on minute, hourly, daily, and yearly charts."))
    e.append(bullet(b("1938") + " — " + it("The Wave Principle") + " published"))
    e.append(bullet(b("1939") + " — Series of 12 articles in " + it("Financial World") + " magazine"))
    e.append(bullet(b("1946") + " — Final work: " + it("Nature's Law — The Secret of the Universe")))
    e.append(bullet("Robert Prechter revived and popularized Elliott Wave in the 1970s–1980s"))
    e.append(sp(8))

    e.append(h2("1.2  The Principle of Waves"))
    e.append(p("The core idea is that market prices move in " + b("waves") + " — directional movements that can be identified, classified, and used to forecast future price behavior. Three fundamental concepts underpin the theory:"))
    rows = [
        [b("Concept"), b("Meaning")],
        ["Pattern", "Price traces identifiable wave shapes (5-wave impulse, 3-wave correction)"],
        ["Ratio", "Fibonacci ratios describe wave relationships in time and price"],
        ["Time", "Waves may take equal or Fibonacci-related periods to complete"],
    ]
    e.append(table2(rows))
    e.append(sp(8))

    e.append(h2("1.3  Motive Waves — The 5-Wave Impulse"))
    e.append(p("An " + b(green("impulse wave")) + " has 5 sub-waves labeled 1-2-3-4-5, where waves 1, 3, and 5 move in the direction of the larger trend, while waves 2 and 4 are counter-trend corrections."))
    e.append(ElliottImpulseChart(W - 80, 210))
    e.append(sp(4))
    e.append(p("", CAPTION))
    e.append(sp(6))

    e.append(h3("The Three Unbreakable Rules of Impulse Waves"))
    e.append(bullet(b("Rule 1:") + "  Wave 2 " + red("cannot retrace more than 100%") + " of Wave 1. If it does, the count is invalid."))
    e.append(bullet(b("Rule 2:") + "  Wave 3 " + red("is never the shortest") + " among waves 1, 3, and 5."))
    e.append(bullet(b("Rule 3:") + "  Wave 4 " + red("cannot overlap") + " into the price territory of Wave 1 (in non-leveraged markets)."))
    e.append(sp(8))

    e.append(h3("Guidelines (Not Rules)"))
    e.append(bullet("Wave 3 is most often the " + b(gold("longest and strongest")) + " wave"))
    e.append(bullet("Wave 2 typically retraces 50%–61.8% of Wave 1"))
    e.append(bullet("Wave 4 typically retraces 38.2%–50% of Wave 3"))
    e.append(bullet("Wave 5 often equals Wave 1 in length, or 61.8% of Waves 1+3"))
    e.append(sp(8))

    e.append(h2("1.4  Corrective Waves — A-B-C Patterns"))
    e.append(p("After every 5-wave impulse, a " + b(red("3-wave correction")) + " follows. The most common corrective structures are:"))
    e.append(ElliottCorrectiveChart(W - 80, 210))
    e.append(sp(6))

    rows = [
        [b("Pattern"), b("Structure"), b("Description")],
        ["Zigzag",    "5-3-5",  "Sharp correction; Wave B shallow, Wave C equals or exceeds Wave A"],
        ["Flat",      "3-3-5",  "Sideways correction; Wave B retraces ~100% of Wave A"],
        ["Triangle",  "3-3-3-3-3", "5 sub-waves contracting; usually precedes final wave"],
        ["Double/Triple Three", "3-3 or 3-3-3", "Two or three corrective patterns linked by X waves"],
    ]
    e.append(table2(rows, [120, 80, 238]))
    e.append(sp(8))

    e.append(h2("1.5  Wave Degree & Labeling"))
    e.append(p("Elliott named " + b("nine degrees") + " of waves, from the Grand Supercycle (spanning centuries) down to the Subminuette (minutes). Traders use standard notation:"))
    rows = [
        [b("Degree"),       b("Motive Labels"), b("Corrective Labels")],
        ["Grand Supercycle","[I] [II] [III] [IV] [V]",  "[A] [B] [C]"],
        ["Supercycle",      "(I) (II) (III) (IV) (V)",  "(A) (B) (C)"],
        ["Cycle",           "I  II  III  IV  V",         "A  B  C"],
        ["Primary",         "[1] [2] [3] [4] [5]",       "[a] [b] [c]"],
        ["Intermediate",    "(1) (2) (3) (4) (5)",       "(a) (b) (c)"],
        ["Minor",           "1  2  3  4  5",              "a  b  c"],
        ["Minute",          "i  ii  iii  iv  v",          "a  b  c  (lower)"],
    ]
    e.append(table2(rows, [150, 170, 118]))
    e.append(sp(12))

    e.append(summary_box([
        "Elliott Wave alternates between 5-wave impulses (motive) and 3-wave corrections",
        "Three unbreakable rules govern valid impulse wave counts",
        "Wave 3 is never the shortest; Wave 2 never retraces 100%+ of Wave 1",
        "Corrections take Zigzag, Flat, or Triangle forms",
        "Wave degree allows nesting the same patterns across all timeframes",
    ]))
    e.append(PageBreak())
    return e

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 — Advanced Wave Structures
# ══════════════════════════════════════════════════════════════════════════════
def build_module2():
    e = []
    e.append(sp(10))
    e.append(h1("Module 2 — Advanced Wave Structures"))
    e.append(hr())

    e.append(h2("2.1  Wave Extensions"))
    e.append(p("An " + b(accent("extension")) + " occurs when one of the three motive waves (1, 3, or 5) elongates significantly beyond its counterparts. Extensions are common and change the overall wave count."))
    e.append(bullet(b("Most common:") + "  Wave 3 extension — produces the most powerful and momentum-driven move"))
    e.append(bullet(b("Wave 5 extension:") + "  Less common; often seen in commodity markets and crypto"))
    e.append(bullet(b("Wave 1 extension:") + "  Rare; usually occurs at the start of new major trends"))
    e.append(bullet("Extended waves subdivide into 9 waves of the same degree instead of 5"))
    e.append(bullet("Rule: only " + b("one") + " wave among 1, 3, or 5 extends in any given impulse"))
    e.append(sp(8))

    e.append(h2("2.2  Diagonal Triangles"))
    e.append(p("Diagonals are impulse waves that have a wedge shape. All sub-waves overlap and move in the direction of the larger trend."))
    rows = [
        [b("Type"), b("Position"), b("Internal Structure"), b("Key Feature")],
        ["Leading Diagonal",  "Wave 1 or Wave A", "5-3-5-3-5", "Starts a new trend; sub-waves overlap"],
        ["Ending Diagonal",   "Wave 5 or Wave C", "3-3-3-3-3", "Exhaustion signal; strong reversal follows"],
    ]
    e.append(table2(rows, [120, 100, 100, 118]))
    e.append(sp(4))
    e.append(p(b(gold("Trading tip:")) + "  An ending diagonal in Wave 5 combined with " + b(red("bearish MACD divergence")) + " is one of the highest-probability reversal setups in technical analysis."))
    e.append(sp(8))

    e.append(h2("2.3  Complex Corrections"))
    e.append(p("When markets consolidate for an extended period, simple A-B-C corrections combine into " + b("double") + " or " + b("triple") + " three patterns, connected by linking waves called " + b(accent("X waves")) + "."))
    rows = [
        [b("Pattern"),      b("Structure"),    b("Typical Duration")],
        ["Double Three",    "W-X-Y",           "Medium consolidation phase"],
        ["Triple Three",    "W-X-Y-X-Z",       "Extended sideways period"],
        ["Running Flat",    "3-3-5 (B > A)",   "Bullish continuation correction"],
        ["Expanded Flat",   "3-3-5 (B > A, C > A)", "Common before explosive Wave 3"],
    ]
    e.append(table2(rows, [130, 140, 168]))
    e.append(sp(8))

    e.append(h2("2.4  Fibonacci Relationships in Waves"))
    e.append(p("Fibonacci ratios are the mathematical backbone of Elliott Wave theory. Markets naturally gravitate toward these levels because they reflect collective psychological decision points."))
    e.append(FibChart(W - 80, 210))
    e.append(sp(6))

    e.append(h3("Key Fibonacci Ratios by Wave"))
    rows = [
        [b("Wave"),   b("Retracement/Projection"),  b("Most Common Fibonacci Level")],
        ["Wave 2",    "Retraces Wave 1",             "50% or 61.8%"],
        ["Wave 3",    "Projects from end of Wave 2", "161.8% of Wave 1"],
        ["Wave 4",    "Retraces Wave 3",             "38.2%"],
        ["Wave 5",    "Projects from Wave 4 end",    "Equal to Wave 1, or 61.8% of Waves 1–3"],
        ["Wave A",    "Retraces impulse",            "23.6%–38.2% of full 5-wave move"],
        ["Wave B",    "Retraces Wave A",             "50%–78.6% of Wave A"],
        ["Wave C",    "Projects from Wave B end",    "100% or 161.8% of Wave A"],
    ]
    e.append(table2(rows, [70, 170, 198]))
    e.append(sp(8))

    e.append(h3("Fibonacci Clusters — High-Value Zones"))
    e.append(p("A " + b(gold("Fibonacci cluster")) + " occurs when multiple Fibonacci projections/retracements from different waves converge on the same price zone. These are the strongest support/resistance areas and the best places to anticipate reversals, especially when confirmed by MACD divergence."))
    e.append(bullet("Identify Wave 1 end, Wave 2 end, and Wave 3 end"))
    e.append(bullet("Project 100%, 138.2%, 161.8% of Wave 1 from Wave 2 end"))
    e.append(bullet("Project 61.8%, 100% of Wave 3 from Wave 4 end"))
    e.append(bullet("Where multiple projections overlap → high-probability reversal zone"))
    e.append(sp(12))

    e.append(summary_box([
        "Extensions elongate one motive wave — wave 3 extensions are the most powerful",
        "Ending diagonals signal exhaustion — best combined with MACD divergence",
        "Complex corrections (WXY) require patience; often form before explosive moves",
        "Fibonacci clusters are the strongest reversal zones in wave analysis",
        "Wave 2 retraces 50–61.8%; Wave 4 retraces 38.2%; Wave 3 targets 161.8%",
    ]))
    e.append(PageBreak())
    return e

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — MACD Deep Dive
# ══════════════════════════════════════════════════════════════════════════════
def build_module3():
    e = []
    e.append(sp(10))
    e.append(h1("Module 3 — MACD Indicator Deep Dive"))
    e.append(hr())

    e.append(h2("3.1  MACD Construction & Settings"))
    e.append(p("The " + b(accent("Moving Average Convergence Divergence")) + " (MACD) was developed by Gerald Appel in the late 1970s. It measures momentum by comparing two exponential moving averages."))

    rows = [
        [b("Component"),         b("Calculation"),                           b("Default Setting")],
        ["MACD Line",            "EMA(Fast Period) − EMA(Slow Period)",      "EMA(12) − EMA(26)"],
        ["Signal Line",          "EMA of MACD Line",                         "EMA(9) of MACD Line"],
        ["Histogram",            "MACD Line − Signal Line",                  "Bar chart of difference"],
    ]
    e.append(table2(rows, [120, 240, 78]))
    e.append(sp(6))

    e.append(h3("Alternative MACD Settings"))
    e.append(p("While 12-26-9 is the default, different markets and timeframes benefit from adjusted settings:"))
    rows = [
        [b("Market / Timeframe"),      b("Settings"),      b("Rationale")],
        ["Crypto (fast markets)",       "8-17-9",           "Faster signals; less lag"],
        ["Forex (scalping, M5-M15)",    "5-13-5",           "Very responsive"],
        ["Stocks (swing trading)",      "12-26-9",          "Standard balanced setting"],
        ["Futures (position trading)", "24-52-18",         "Slower, filters noise"],
    ]
    e.append(table2(rows, [170, 100, 168]))
    e.append(sp(8))

    e.append(h2("3.2  Signal Line & Histogram Dynamics"))
    e.append(p("The " + b(gold("histogram")) + " is the most important component for divergence analysis. It represents the " + b("acceleration") + " of momentum — not momentum itself."))
    e.append(bullet(b(green("Rising histogram")) + "  →  momentum is accelerating in the direction of the MACD line"))
    e.append(bullet(b(red("Falling histogram")) + "  →  momentum is decelerating (early warning of slowdown)"))
    e.append(bullet("When histogram crosses zero from below → " + b(green("bullish momentum confirmed"))))
    e.append(bullet("When histogram crosses zero from above → " + b(red("bearish momentum confirmed"))))
    e.append(bullet(b(gold("Peak/trough in histogram")) + "  is more important than the zero crossover for divergence"))
    e.append(sp(8))

    e.append(h2("3.3  MACD Zero-Line Crossovers"))
    e.append(p("The MACD line itself crossing the zero level indicates a change in the " + b("medium-term trend") + ":"))
    rows = [
        [b("Signal"),                     b("Interpretation"),              b("Wave Context")],
        ["MACD Line crosses above 0",     "Bullish trend begins/resumes",   "Often at start of Wave 3 up"],
        ["MACD Line crosses below 0",     "Bearish trend begins/resumes",   "Often at Wave A break down"],
        ["Signal line cross above MACD",  "Short-term buy signal",          "Wave 3 or Wave C bottom confirmation"],
        ["Signal line cross below MACD",  "Short-term sell signal",         "Wave 5 or Wave B exhaustion"],
    ]
    e.append(table2(rows, [150, 160, 128]))
    e.append(sp(8))

    e.append(h2("3.4  Momentum Reading with MACD"))
    e.append(p("Understanding MACD as a " + b("momentum gauge") + " is critical for wave analysis:"))
    e.append(bullet(b("Wave 1:") + "  MACD turns up from oversold; histogram turns from negative to positive"))
    e.append(bullet(b("Wave 2:") + "  MACD pulls back but stays mostly above zero; histogram dips slightly negative"))
    e.append(bullet(b("Wave 3:") + "  MACD surges to new highs; histogram reaches maximum peak — " + b(gold("strongest bars"))))
    e.append(bullet(b("Wave 4:") + "  MACD corrects but holds above zero; histogram shrinks significantly"))
    e.append(bullet(b("Wave 5:") + "  MACD rises but " + b(red("does NOT")) + " reach the Wave 3 peak — " + b(red("classic bearish divergence"))))
    e.append(bullet(b("Wave A/B/C:") + "  MACD oscillates; Wave C bottom often shows " + b(green("bullish divergence"))))
    e.append(sp(12))

    e.append(summary_box([
        "MACD = EMA(12) − EMA(26); Signal = EMA(9); Histogram = MACD − Signal",
        "The histogram measures momentum acceleration — key for divergence spotting",
        "Adjust MACD settings to market speed: faster settings for crypto/scalping",
        "MACD zero-line crossovers align with Elliott Wave transitions (Wave 1→2, 3→4, A→B)",
        "Wave 3 produces the strongest MACD histogram peak — look for divergence on Wave 5",
    ]))
    e.append(PageBreak())
    return e

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 — Divergence Trading
# ══════════════════════════════════════════════════════════════════════════════
def build_module4():
    e = []
    e.append(sp(10))
    e.append(h1("Module 4 — Divergence Trading Strategies"))
    e.append(hr())

    e.append(h2("4.1  What is Divergence?"))
    e.append(p("A " + b(accent("divergence")) + " occurs when the " + b("direction of price") + " and the " + b("direction of the MACD indicator") + " disagree. This disagreement signals that the current trend is " + b(red("losing momentum")) + " and a reversal or major correction is likely."))
    e.append(p("Divergences are not timing tools on their own — they show " + b("momentum weakness") + ". Confirmation is always required via price action, candlestick patterns, or wave structure completion."))
    rows = [
        [b("Type"),              b("Price Action"),              b("MACD Action"),          b("Signal")],
        ["Regular Bullish",      "Lower Lows",                   "Higher Lows",             "Bullish reversal"],
        ["Regular Bearish",      "Higher Highs",                 "Lower Highs",             "Bearish reversal"],
        ["Hidden Bullish",       "Higher Lows",                  "Lower Lows",              "Bullish continuation"],
        ["Hidden Bearish",       "Lower Highs",                  "Higher Highs",            "Bearish continuation"],
    ]
    e.append(table2(rows, [120, 120, 120, 78]))
    e.append(sp(8))

    e.append(h2("4.2  Regular Bullish Divergence"))
    e.append(p(b(green("Regular bullish divergence")) + " forms when price makes a " + b("lower low") + " while MACD makes a " + b(green("higher low")) + ". This indicates that even though price fell to a new low, the selling momentum is weakening."))
    e.append(MACDDivergenceChart(W - 80, 270, bull=True))
    e.append(sp(6))

    e.append(h3("How to Trade Regular Bullish Divergence"))
    e.append(bullet(b("Step 1:") + "  Identify two price lows — the second lower than the first"))
    e.append(bullet(b("Step 2:") + "  Confirm MACD histogram made a " + b("higher low") + " on the second price low"))
    e.append(bullet(b("Step 3:") + "  Draw trendlines on both sets of lows — they should slope in opposite directions"))
    e.append(bullet(b("Step 4:") + "  Wait for a bullish trigger: breakout candle, hammer/engulfing, MACD cross above signal"))
    e.append(bullet(b("Step 5:") + "  Enter long; place stop below the lower low; target previous swing high"))
    e.append(sp(8))

    e.append(h2("4.3  Regular Bearish Divergence"))
    e.append(p(b(red("Regular bearish divergence")) + " forms when price makes a " + b("higher high") + " while MACD makes a " + b(red("lower high")) + ". This shows that despite new price highs, upside momentum is fading."))
    e.append(MACDDivergenceChart(W - 80, 270, bull=False))
    e.append(sp(6))

    e.append(h3("How to Trade Regular Bearish Divergence"))
    e.append(bullet(b("Step 1:") + "  Identify two price peaks — the second higher than the first"))
    e.append(bullet(b("Step 2:") + "  Confirm MACD histogram shows a " + b("lower high") + " at the second peak"))
    e.append(bullet(b("Step 3:") + "  Draw connecting trendlines — price sloping up, MACD sloping down"))
    e.append(bullet(b("Step 4:") + "  Wait for a bearish trigger: shooting star, bearish engulfing, MACD cross below signal"))
    e.append(bullet(b("Step 5:") + "  Enter short; place stop above the higher high; target previous swing low"))
    e.append(PageBreak())

    e.append(h2("4.4  Hidden Divergence"))
    e.append(p(b(gold("Hidden divergence")) + " is the " + b("opposite") + " of regular divergence — it signals " + b("trend continuation") + ", not reversal. It forms during corrections within a trend."))
    rows = [
        [b("Type"),            b("Price Action"),       b("MACD Action"),     b("Meaning")],
        ["Hidden Bullish",     "Higher Low (pullback)", "Lower Low on MACD",  "Uptrend resuming after pullback"],
        ["Hidden Bearish",     "Lower High (bounce)",   "Higher High on MACD","Downtrend resuming after bounce"],
    ]
    e.append(table2(rows, [100, 140, 140, 58]))
    e.append(sp(6))
    e.append(p(b("Hidden bullish divergence") + " is particularly powerful when it aligns with Elliott Wave corrections (Wave 2 or Wave 4 pullbacks). It confirms the corrective wave is complete and the trend will resume."))
    e.append(bullet(b("In an uptrend:") + "  Price makes higher low (Wave 2 or 4) → MACD makes lower low → " + b(green("buy the pullback"))))
    e.append(bullet(b("In a downtrend:") + "  Price makes lower high (Wave B) → MACD makes higher high → " + b(red("sell the bounce"))))
    e.append(sp(8))

    e.append(h2("4.5  Divergence Strength & Reliability"))
    e.append(p("Not all divergences are equal. Several factors affect the probability and strength of a divergence signal:"))
    rows = [
        [b("Factor"),              b("Higher Reliability"),              b("Lower Reliability")],
        ["Timeframe",              "Daily, Weekly charts",               "1-minute, 5-minute charts"],
        ["Pivot spacing",          "Pivots far apart (5+ bars each)",    "Pivots adjacent (1-2 bars)"],
        ["Trend alignment",        "Against minor trend, with major",    "Against major trend"],
        ["MACD component",         "Histogram divergence",               "MACD line divergence only"],
        ["Confirmation",           "Candlestick pattern present",        "No confirmation signal"],
        ["Wave context",           "At wave completion zones",           "Mid-wave occurrence"],
    ]
    e.append(table2(rows, [120, 180, 138]))
    e.append(sp(12))

    e.append(summary_box([
        "Regular divergence = trend reversal signal; hidden divergence = continuation signal",
        "Always draw trendlines on BOTH price pivots and MACD pivots to visualize divergence",
        "Confirm with price action: candlestick patterns, breakouts, or MACD line crossovers",
        "Higher timeframes produce more reliable divergence signals",
        "Hidden bullish divergence during Wave 2/4 is a high-probability continuation entry",
    ]))
    e.append(PageBreak())
    return e

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 5 — Integration
# ══════════════════════════════════════════════════════════════════════════════
def build_module5():
    e = []
    e.append(sp(10))
    e.append(h1("Module 5 — Integrating Elliott Waves with MACD"))
    e.append(hr())

    e.append(p("Combining Elliott Wave counting with MACD divergence analysis creates a powerful synergy: waves tell you " + b(accent("where")) + " price is in the cycle, while MACD divergence tells you " + b(gold("when")) + " momentum is shifting. Together they produce high-probability, well-timed trade entries."))
    e.append(sp(8))

    e.append(WaveMACDComboChart(W - 80, 310))
    e.append(sp(8))

    e.append(h2("5.1  Confirming Wave 3 with MACD"))
    e.append(p("Wave 3 is the most powerful wave in an Elliott sequence. The MACD provides two key confirmations:"))
    e.append(bullet(b("MACD histogram peak:") + "  The highest histogram bar should occur during Wave 3 — confirms maximum momentum"))
    e.append(bullet(b("MACD zero-line crossover:") + "  MACD crossing above zero during Wave 3 confirms new bullish trend"))
    e.append(bullet(b("Signal line breakout:") + "  MACD line crossing above signal line as Wave 3 begins — entry trigger"))
    e.append(bullet(b("No divergence on Wave 3:") + "  If MACD " + b(red("shows divergence during Wave 3")) + ", the count is likely wrong"))
    e.append(sp(6))
    e.append(p(b(gold("Key Rule:")) + "  In a valid Wave 3, the MACD histogram should reach its " + b("highest point") + " in the entire impulse. If the MACD during the supposed Wave 3 is lower than during Wave 1, re-examine your wave count."))
    e.append(sp(8))

    e.append(h2("5.2  Spotting Wave 5 Failure via Bearish Divergence"))
    e.append(p("The most classic and high-probability setup in this course is the " + b(red("Wave 5 bearish divergence")) + " reversal:"))
    rows = [
        [b("Step"), b("Action"), b("What to Look For")],
        ["1", "Complete Wave 3", "Strongest MACD histogram peak; highest price in impulse"],
        ["2", "Count Wave 4", "MACD corrects; histogram shrinks; price holds above Wave 1 top"],
        ["3", "Identify Wave 5 candidate", "Price pushes above Wave 3; new price high forming"],
        ["4", "Check MACD histogram", "Histogram peak is LOWER than Wave 3 peak → bearish divergence"],
        ["5", "Wait for reversal trigger", "Ending diagonal? Shooting star? MACD cross below signal?"],
        ["6", "Enter short after Wave 5 top", "Stop above Wave 5 high; target Wave 4 low initially"],
    ]
    e.append(table2(rows, [25, 140, 273]))
    e.append(sp(6))
    e.append(p(b("Why it works:") + "  Wave 5 completes the 5-wave impulse. Once Wave 5 ends, a full A-B-C correction must follow. Bearish MACD divergence at the Wave 5 top provides both a timing signal (when the wave is complete) and directional confirmation (momentum exhaustion)."))
    e.append(sp(8))

    e.append(h2("5.3  Wave C Bottom via Bullish Divergence"))
    e.append(p("After a 5-wave impulse, price corrects in A-B-C. The end of Wave C is where the next major impulse begins — and " + b(green("bullish MACD divergence")) + " at Wave C is the confirmation signal:"))
    e.append(bullet(b("Wave A down:") + "  MACD drops sharply; histogram deeply negative"))
    e.append(bullet(b("Wave B up:") + "  MACD recovers partially; histogram turns slightly positive"))
    e.append(bullet(b("Wave C down:") + "  Price makes new low below Wave A end — this is the " + b("divergence trigger")))
    e.append(bullet("MACD histogram makes a " + b(green("higher low")) + " compared to Wave A's low → " + b(green("bullish divergence"))))
    e.append(bullet(b("Entry:") + "  First bullish candle after Wave C low, confirmed by MACD crossing above signal line"))
    e.append(sp(6))

    rows = [
        [b("Setup"), b("Wave Position"), b("Divergence Type"), b("Trade Direction")],
        ["Wave 5 Top", "End of 5-wave impulse", "Bearish divergence", "Short (sell)"],
        ["Wave C Bottom", "End of A-B-C correction", "Bullish divergence", "Long (buy)"],
        ["Wave 2 Low", "Pullback after Wave 1", "Hidden bullish", "Long (continuation)"],
        ["Wave 4 Low", "Pullback after Wave 3", "Hidden bullish", "Long (continuation)"],
        ["Wave B High", "Bounce in correction", "Hidden bearish", "Short (continuation)"],
    ]
    e.append(table2(rows, [100, 130, 130, 78]))
    e.append(sp(12))

    e.append(summary_box([
        "Wave 3 = MACD histogram peak: if no MACD peak, the wave count may be wrong",
        "Wave 5 + bearish MACD divergence = highest-probability sell setup in this course",
        "Wave C bottom + bullish MACD divergence = highest-probability buy setup",
        "Hidden divergence at Wave 2/4 confirms trend continuation entries",
        "Always combine wave structure completion with a price action trigger",
    ]))
    e.append(PageBreak())
    return e

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 6 — Entry, Exit & Risk Management
# ══════════════════════════════════════════════════════════════════════════════
def build_module6():
    e = []
    e.append(sp(10))
    e.append(h1("Module 6 — Entry, Exit &amp; Risk Management"))
    e.append(hr())

    e.append(h2("6.1  Entry Triggers & Confirmation"))
    e.append(p("A divergence signal alone is " + b(red("never enough")) + " to enter a trade. You need a " + b(gold("trigger")) + " — a price action event that confirms the reversal has begun. Waiting for confirmation dramatically improves your win rate."))
    rows = [
        [b("Trigger Type"),              b("Description"),                        b("Strength")],
        ["MACD cross above/below signal","MACD line crosses signal line",          "★★★"],
        ["Bullish/Bearish engulfing",    "Candle engulfs prior candle's body",     "★★★★"],
        ["Hammer / Shooting Star",       "Long wick reversal candle",              "★★★"],
        ["Break of corrective trendline","Price breaks the correction channel",    "★★★★"],
        ["Close above/below pivot",      "Candle closes past a key level",         "★★★★★"],
        ["RSI/Stoch confirmation",       "Second oscillator also shows divergence","★★★★★"],
    ]
    e.append(table2(rows, [160, 200, 78]))
    e.append(sp(8))

    e.append(h2("6.2  Stop Loss Placement"))
    e.append(p("Stop loss placement must be " + b("logical") + " — placed where the trade idea is " + b("definitively wrong") + ", not where it merely hurts."))
    e.append(bullet(b("Wave 5 short:") + "  Stop above the Wave 5 high (new all-time/swing high)"))
    e.append(bullet(b("Wave C long:") + "  Stop below the Wave C low (the divergence pivot)"))
    e.append(bullet(b("Wave 2/4 long:") + "  Stop below Wave 2 low / Wave 4 low — if this breaks, wave count is wrong"))
    e.append(bullet(b("Minimum distance:") + "  Stop must clear the divergence pivot by at least 1 ATR to avoid noise"))
    e.append(bullet(b("Never move stop against position:") + "  Only trail in your favor as trade develops"))
    e.append(sp(8))

    e.append(h2("6.3  Take Profit & Target Levels"))
    e.append(TradeSetupChart(W - 80, 210))
    e.append(sp(6))
    e.append(bullet(b("TP1 (1:1 R/R):") + "  Closest swing high/low; partial profit + move stop to breakeven"))
    e.append(bullet(b("TP2 (1:2 R/R):") + "  Fibonacci extension or measured move target"))
    e.append(bullet(b("TP3 (1:3+ R/R):") + "  Full wave projection (e.g., 161.8% extension for Wave 3 target)"))
    e.append(bullet(b("Scaling out:") + "  Close 30–40% at TP1, 30–40% at TP2, trail remaining to TP3+"))
    e.append(sp(8))

    e.append(h2("6.4  Position Sizing"))
    e.append(p("Professional traders never risk more than " + b(gold("1–2% of account")) + " on a single trade. The formula:"))
    rows = [
        [b("Formula Component"),       b("Value / Calculation")],
        ["Risk per trade",             "Account size × Risk % (e.g., $10,000 × 1% = $100)"],
        ["Risk per unit",              "Entry price − Stop loss price (in points/pips)"],
        ["Position size",              "Risk per trade ÷ Risk per unit"],
        ["Example",                    "Risk $100; SL = 50 pips; Size = 100 ÷ 50 = 2 mini lots (forex)"],
    ]
    e.append(table2(rows, [180, 258]))
    e.append(sp(6))
    e.append(p(b(gold("Golden Rule:")) + "  If the stop is far (large R per unit), reduce size. If the stop is tight (small R per unit), you can increase size. " + b("Risk amount stays constant; position size varies.")))
    e.append(sp(8))

    e.append(h3("Risk Management Principles"))
    e.append(bullet("Never risk more than 2% per trade — protect capital above all else"))
    e.append(bullet("Only take setups with minimum " + b("1:2 R/R ratio") + " — ideally 1:3 or better"))
    e.append(bullet("After 3 consecutive losses, reduce size by 50% until back to breakeven"))
    e.append(bullet("Keep a trade journal — review every trade for wave count accuracy"))
    e.append(bullet("Divergence + wave alignment + trigger = full 3-condition checklist before entry"))
    e.append(sp(12))

    e.append(summary_box([
        "Never enter on divergence alone — always wait for a confirmed trigger",
        "Best triggers: price close beyond pivot, candlestick reversal, MACD line cross",
        "Stop loss goes where the trade idea is wrong — behind the divergence pivot",
        "Scale out profits: 1:1 → 1:2 → trail remainder to wave projection target",
        "Fixed-risk position sizing: never more than 1-2% of account per trade",
    ]))
    e.append(PageBreak())
    return e

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 7 — Multi-Timeframe Analysis
# ══════════════════════════════════════════════════════════════════════════════
def build_module7():
    e = []
    e.append(sp(10))
    e.append(h1("Module 7 — Multi-Timeframe Analysis"))
    e.append(hr())

    e.append(h2("7.1  Top-Down Wave Counting"))
    e.append(p("The most reliable Elliott Wave analysis starts " + b(accent("top-down")) + " — from the highest timeframe to the lowest. The higher timeframe defines the " + b("dominant wave degree") + " and trend direction, while the lower timeframe provides the entry timing."))
    rows = [
        [b("Step"), b("Timeframe"),     b("Purpose"),                                b("Wave Degree")],
        ["1", "Monthly / Weekly",       "Identify Grand Supercycle or Supercycle position", "Grand Supercycle"],
        ["2", "Daily",                  "Confirm Cycle/Primary wave position",              "Primary"],
        ["3", "4H / 1H",               "Intermediate wave structure & divergence zones",    "Intermediate"],
        ["4", "30m / 15m",             "Entry timing & trigger confirmation",               "Minor"],
        ["5", "5m",                     "Fine-tune entry, stop, position size",              "Minute"],
    ]
    e.append(table2(rows, [25, 90, 225, 98]))
    e.append(sp(6))
    e.append(p(b("Key principle:") + "  Only take trades " + b(green("in the direction of the higher-timeframe wave")) + ". If the daily chart is in a Wave 3 up, only look for long entries on the 4H/1H. Never fight the higher-timeframe wave."))
    e.append(sp(8))

    e.append(h2("7.2  Aligning MACD Across Timeframes"))
    e.append(p("MACD divergence becomes " + b(gold("significantly more powerful")) + " when it appears on multiple timeframes simultaneously."))
    e.append(bullet(b("Single-timeframe divergence:") + "  Moderate signal — may be overridden by higher-TF momentum"))
    e.append(bullet(b("Two-timeframe divergence:") + "  Strong signal — high probability reversal"))
    e.append(bullet(b("Three-timeframe divergence:") + "  Very strong signal — often marks major market turning points"))
    e.append(sp(6))

    rows = [
        [b("Scenario"),                          b("TF1"),     b("TF2"),    b("Action")],
        ["Wave 5 top (bearish)",                 "Daily: bearish div", "4H: bearish div", "Strong sell setup"],
        ["Wave C bottom (bullish)",              "Daily: bullish div", "4H: bullish div", "Strong buy setup"],
        ["Wave 2 correction (hidden bull)",      "4H: hidden bull",    "1H: hidden bull", "Buy the pullback"],
        ["B-wave bounce (hidden bear)",          "Daily: hidden bear", "4H: bearish div", "Sell the bounce"],
    ]
    e.append(table2(rows, [170, 120, 120, 28]))
    e.append(sp(8))

    e.append(h3("Practical Multi-TF Workflow"))
    e.append(bullet(b("Weekly chart:") + "  Am I in an uptrend or downtrend at the macro level? What wave degree?"))
    e.append(bullet(b("Daily chart:") + "  Which specific wave is forming? Look for divergence signals"))
    e.append(bullet(b("4H chart:") + "  Confirm divergence; check wave sub-structure completion"))
    e.append(bullet(b("1H chart:") + "  Identify exact entry trigger; measure stop loss distance"))
    e.append(bullet(b("Rule:") + "  If higher-TF MACD is still trending strongly, reduce position size on counter-trend trades"))
    e.append(sp(8))

    e.append(h3("Common Multi-TF Mistakes to Avoid"))
    e.append(bullet(b(red("Mistake 1:")) + "  Trading lower-TF divergence against a strong higher-TF wave 3"))
    e.append(bullet(b(red("Mistake 2:")) + "  Switching timeframes mid-trade to justify a losing position"))
    e.append(bullet(b(red("Mistake 3:")) + "  Counting waves on a timeframe that is too low for the analysis (too much noise)"))
    e.append(bullet(b(red("Mistake 4:")) + "  Ignoring that wave degree changes the meaning of divergence signals"))
    e.append(sp(12))

    e.append(summary_box([
        "Always work top-down: Weekly → Daily → 4H → 1H → Entry",
        "Only trade in the direction of the dominant higher-timeframe wave",
        "Multi-timeframe MACD divergence dramatically increases trade probability",
        "Three-timeframe divergence alignment often marks major turning points",
        "Never fight the higher-timeframe wave 3 — the trend is your friend",
    ]))
    e.append(PageBreak())
    return e


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 8 — Live Examples & Checklists
# ══════════════════════════════════════════════════════════════════════════════
def build_module8():
    e = []
    e.append(sp(10))
    e.append(h1("Module 8 — Trade Examples &amp; Checklists"))
    e.append(hr())

    e.append(h2("8.1  Bullish Setup Example — Wave C Bottom"))
    e.append(p("The following step-by-step example illustrates a " + b(green("Wave C bottom with bullish MACD divergence")) + " setup:"))
    rows = [
        [b("Step"), b("Action"),                    b("Observation")],
        ["1", "Weekly chart analysis",               "Market in long-term uptrend (Cycle Wave III up); currently in Intermediate (II) correction"],
        ["2", "Daily chart — count correction",      "Wave A down complete; Wave B up complete; Wave C down underway"],
        ["3", "Daily MACD check",                    "Wave C low: price below Wave A low; MACD histogram higher low → bullish divergence confirmed"],
        ["4", "4H chart — sub-wave count",           "Wave C shows 5 sub-waves complete; wave (v) = wave (i) in length"],
        ["4H MACD", "Confirm divergence on 4H",      "4H MACD also showing bullish divergence at same price level"],
        ["5", "Wait for trigger on 1H",              "1H chart: bullish engulfing candle above prior swing low; MACD crosses above signal"],
        ["6", "Entry",                               "Enter long at close of trigger candle"],
        ["7", "Stop loss",                           "Below Wave C low minus 1 ATR"],
        ["8", "Target calculation",                  "TP1 = 38.2% retrace of full A-B-C; TP2 = 61.8% retrace; TP3 = Wave B high (full correction end)"],
        ["9", "Risk/Reward",                         "Typical R/R = 1:2.5 to 1:4 on this setup"],
    ]
    e.append(table2(rows, [60, 140, 238]))
    e.append(sp(8))

    e.append(h2("8.2  Bearish Setup Example — Wave 5 Top"))
    e.append(p("This example shows a " + b(red("Wave 5 top with bearish MACD divergence")) + " — the signature reversal setup of this course:"))
    rows = [
        [b("Step"), b("Action"),                    b("Observation")],
        ["1", "Daily chart — full impulse count",    "5 waves up from major low clearly labeled 1-2-3-4-5"],
        ["2", "Wave 3 MACD check",                  "Wave 3 high: MACD histogram at absolute peak for this move"],
        ["3", "Wave 4 correction",                  "MACD pulls back; stays above zero; price holds above Wave 1 top → count valid"],
        ["4", "Wave 5 underway",                    "New price high above Wave 3; price makes higher high"],
        ["5", "MACD divergence confirmed",           "MACD histogram at Wave 5 high is LOWER than Wave 3 high → bearish divergence"],
        ["6", "Structure check",                    "Wave 5 = Wave 1 in length (Fibonacci equality); possible ending diagonal forming"],
        ["7", "4H confirmation",                    "4H chart: also shows bearish divergence; shooting star candle at resistance"],
        ["8", "Entry",                              "Enter short after shooting star confirmation close"],
        ["9", "Stop loss",                          "Above Wave 5 high + 0.5 ATR"],
        ["10", "Targets",                           "TP1 = Wave 4 low; TP2 = Wave 2 low (full A-B-C correction expected)"],
    ]
    e.append(table2(rows, [60, 140, 238]))
    e.append(PageBreak())

    e.append(h2("8.3  Master Trading Checklist"))
    e.append(p("Use this checklist before " + b("every") + " trade. All checked boxes = higher-probability setup."))

    check_sections = [
        ("WAVE STRUCTURE", [
            "Higher-timeframe wave direction identified (up or down)",
            "Current wave position clearly labeled (which wave am I in?)",
            "Wave count satisfies all three Elliott Wave rules",
            "Wave is at a logical completion zone (Fibonacci extension/retracement)",
            "No alternative wave count is significantly more likely",
        ]),
        ("MACD DIVERGENCE", [
            "Divergence type identified (regular / hidden)",
            "Divergence visible on at least two timeframes",
            "Trendlines drawn on both price pivots and MACD pivots",
            "Divergence aligns with expected wave completion point",
            "MACD histogram — not just MACD line — shows divergence",
        ]),
        ("ENTRY TRIGGER", [
            "Price action trigger present (engulfing, hammer, break of trendline)",
            "MACD signal line crossover confirms direction",
            "Entry candle has closed (not entering mid-candle)",
            "Volume spike or expansion supports the move (if data available)",
        ]),
        ("RISK MANAGEMENT", [
            "Stop loss placed at logical invalidation level",
            "Risk per trade ≤ 2% of account capital",
            "Risk/Reward ratio ≥ 1:2",
            "TP1, TP2, TP3 levels pre-calculated and set",
            "Position size calculated using fixed-risk formula",
        ]),
    ]

    for section_title, checks in check_sections:
        e.append(h3(section_title))
        for item in checks:
            row = [[Paragraph(f"☐  {item}", BODY)]]
            t = Table(row, colWidths=[W - 80])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0),(-1,-1), PANEL_BG),
                ("TOPPADDING", (0,0),(-1,-1), 4),
                ("BOTTOMPADDING", (0,0),(-1,-1), 4),
                ("LEFTPADDING", (0,0),(-1,-1), 12),
                ("BOX", (0,0),(-1,-1), 0.3, MID_GRAY),
            ]))
            e.append(t)
            e.append(sp(2))
        e.append(sp(6))
    e.append(PageBreak())
    return e

# ══════════════════════════════════════════════════════════════════════════════
# APPENDIX — Quick Reference
# ══════════════════════════════════════════════════════════════════════════════
def build_appendix():
    e = []
    e.append(sp(10))
    e.append(h1("Appendix — Quick Reference Guide"))
    e.append(hr())

    e.append(h2("Elliott Wave Rules — Absolute Laws"))
    rows = [
        [b("Rule"),                      b("Requirement"),                                       b("If Broken")],
        ["Wave 2 Rule",                  "Wave 2 cannot retrace more than 100% of Wave 1",       "Recount from scratch"],
        ["Wave 3 Rule",                  "Wave 3 is never the shortest of Waves 1, 3, 5",        "Recount or re-label"],
        ["Wave 4 Rule",                  "Wave 4 cannot overlap Wave 1 territory",               "May be diagonal or wrong count"],
    ]
    e.append(table2(rows, [100, 240, 98]))
    e.append(sp(8))

    e.append(h2("Elliott Wave Guidelines — Strong Tendencies"))
    rows = [
        [b("Guideline"),                 b("Typical Behavior")],
        ["Wave 2 depth",                 "Retraces 50%–61.8% of Wave 1"],
        ["Wave 3 length",                "161.8% of Wave 1 (most common extension)"],
        ["Wave 4 depth",                 "Retraces 38.2% of Wave 3"],
        ["Wave 5 length",                "Equal to Wave 1, or 61.8% of Waves 1+3"],
        ["Alternation",                  "If Wave 2 is simple, Wave 4 is complex (and vice versa)"],
        ["Wave B retracement",           "50%–78.6% of Wave A"],
        ["Wave C length",                "100% or 161.8% of Wave A"],
        ["Channel guideline",            "Waves 2 and 4 connect via a parallel channel"],
    ]
    e.append(table2(rows, [180, 258]))
    e.append(sp(8))

    e.append(h2("MACD Settings Reference"))
    rows = [
        [b("Market Type"),        b("Fast"), b("Slow"), b("Signal"), b("Notes")],
        ["Standard (default)",    "12",      "26",       "9",        "Best for daily stocks/FX"],
        ["Crypto scalping",       "8",       "17",       "9",        "Fast markets, short TF"],
        ["Forex scalping M5",     "5",       "13",       "5",        "Very fast; more signals"],
        ["Swing trading",         "12",      "26",       "9",        "Daily/4H standard"],
        ["Position trading",      "24",      "52",       "18",       "Weekly charts"],
    ]
    e.append(table2(rows, [130, 50, 50, 55, 153]))
    e.append(sp(8))

    e.append(h2("Divergence Quick Reference"))
    rows = [
        [b("Type"),              b("Price"),        b("MACD"),        b("Signal"),         b("Wave Context")],
        ["Regular Bullish",      "Lower Low",       "Higher Low",     "Buy reversal",      "Wave C bottom"],
        ["Regular Bearish",      "Higher High",     "Lower High",     "Sell reversal",     "Wave 5 top"],
        ["Hidden Bullish",       "Higher Low",      "Lower Low",      "Buy continuation",  "Wave 2/4 pullback"],
        ["Hidden Bearish",       "Lower High",      "Higher High",    "Sell continuation", "Wave B bounce"],
    ]
    e.append(table2(rows, [100, 75, 75, 85, 103]))
    e.append(sp(8))

    e.append(h2("Risk Management Quick Reference"))
    rows = [
        [b("Parameter"),            b("Rule")],
        ["Max risk per trade",       "1–2% of total account capital"],
        ["Minimum R/R ratio",        "1:2 (take profit = 2× stop loss distance)"],
        ["Ideal R/R ratio",          "1:3 or better"],
        ["Stop loss location",       "Behind divergence pivot + 0.5–1 ATR buffer"],
        ["Scaling out",              "30% at 1:1, 40% at 1:2, trail 30% to target"],
        ["Loss streak rule",         "After 3 losses, halve position size temporarily"],
        ["Position size formula",    "Size = (Account × Risk%) ÷ (Entry − Stop in $)"],
    ]
    e.append(table2(rows, [200, 238]))
    e.append(sp(8))

    e.append(h2("High-Probability Setup Matrix"))
    rows = [
        [b("Setup Name"),                        b("Wave"),    b("MACD"),         b("R/R"),   b("Win Rate Est.")],
        ["Wave 5 Bearish Reversal",              "5 top",      "Bearish reg. div","1:3+",     "60–70%"],
        ["Wave C Bullish Reversal",              "C bottom",   "Bullish reg. div","1:3+",     "60–70%"],
        ["Wave 2 Hidden Bull Continuation",      "2 low",      "Hidden bull div", "1:2–1:4",  "65–75%"],
        ["Wave 4 Hidden Bull Continuation",      "4 low",      "Hidden bull div", "1:2–1:3",  "60–65%"],
        ["Ending Diagonal + Bearish Div",        "5 (diag.)", "Bearish reg. div","1:4+",     "70–80%"],
        ["Multi-TF Divergence Confirmation",     "Any",        "2–3 TF aligned",  "1:3+",     "70–80%"],
    ]
    e.append(table2(rows, [165, 60, 95, 55, 63]))
    e.append(sp(12))

    e.append(h2("Recommended Study Path"))
    e.append(bullet(b("Week 1–2:") + "  Master Module 1 & 2 — practice counting waves on historical charts"))
    e.append(bullet(b("Week 3:") + "  Study Module 3 — learn to read MACD momentum; identify histogram peaks"))
    e.append(bullet(b("Week 4:") + "  Study Module 4 — find and draw at least 20 divergences on past charts"))
    e.append(bullet(b("Week 5–6:") + "  Study Module 5 — combine wave counts + MACD; paper trade setups"))
    e.append(bullet(b("Week 7:") + "  Study Modules 6 & 7 — apply multi-TF analysis to paper trading"))
    e.append(bullet(b("Week 8+:") + "  Apply Module 8 checklist to every live paper trade; review journal weekly"))
    e.append(sp(4))
    e.append(p(b(gold("Final advice:")) + "  The best traders are not those who find every setup — they are those who wait for setups where " + b("waves + divergence + trigger + R/R") + " all align perfectly. Patience is your most valuable tool."))
    e.append(sp(16))
    e.append(hr(ACCENT2))
    e.append(sp(6))
    e.append(Paragraph("Elliott Wave &amp; MACD Divergences — Complete Trading Course  |  2026 Edition",
             style("footer_txt", fontSize=8, leading=12, textColor=MID_GRAY, alignment=TA_CENTER)))
    e.append(Paragraph("For educational purposes only. Past performance is not indicative of future results.",
             style("disclaimer", fontSize=7, leading=10, textColor=MID_GRAY, alignment=TA_CENTER)))
    return e

# ══════════════════════════════════════════════════════════════════════════════
# MAIN — build the document
# ══════════════════════════════════════════════════════════════════════════════
def build_pdf():
    output_path = "Elliott_Wave_MACD_Divergences_Course.pdf"
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=40, rightMargin=40,
        topMargin=40,  bottomMargin=35,
        title="Elliott Wave & MACD Divergences — Complete Trading Course",
        author="Advanced Technical Analysis Series",
        subject="Elliott Wave Theory, MACD Divergence, Trading Strategies",
    )

    story = []

    # Cover (uses special canvas)
    story += build_cover()
    story += build_toc()
    story += build_module1()
    story += build_module2()
    story += build_module3()
    story += build_module4()
    story += build_module5()
    story += build_module6()
    story += build_module7()
    story += build_module8()
    story += build_appendix()

    # First page = cover, rest = dark_page
    def page_template(canvas, doc):
        if doc.page == 1:
            cover_page(canvas, doc)
        else:
            dark_page(canvas, doc)

    doc.build(story, onFirstPage=page_template, onLaterPages=page_template)
    print(f"✅  PDF created: {output_path}")
    return output_path

if __name__ == "__main__":
    build_pdf()
