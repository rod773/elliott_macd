"""
Elliott Wave & MACD Divergences — Course Video Generator
Renders each scene as animated frames (matplotlib) + TTS audio (pyttsx3),
then stitches everything into a final MP4 (moviepy).
"""
import os, sys, time, textwrap, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import matplotlib.patheffects as pe
from moviepy.editor import (
    ImageSequenceClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, ColorClip, TextClip
)
import pyttsx3

# ── Output config ──────────────────────────────────────────────────────────────
OUT_DIR    = "video_output"
FRAMES_DIR = os.path.join(OUT_DIR, "frames")
AUDIO_DIR  = os.path.join(OUT_DIR, "audio")
FINAL_VIDEO = os.path.join(OUT_DIR, "Elliott_Wave_MACD_Course.mp4")
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR,  exist_ok=True)

FPS        = 24
W_PX, H_PX = 1920, 1080
DPI        = 96
FIG_W      = W_PX / DPI
FIG_H      = H_PX / DPI

# ── Color palette ──────────────────────────────────────────────────────────────
BG     = "#0D1B2A"
ACCENT = "#00D4FF"
GOLD   = "#FFD700"
ORANGE = "#FF6B35"
GREEN  = "#00E676"
RED    = "#FF1744"
LGRAY  = "#E0E0E0"
MGRAY  = "#607080"
PANEL  = "#111F2E"
WHITE  = "#FFFFFF"

# ── TTS engine ─────────────────────────────────────────────────────────────────
def init_tts():
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    # prefer a clear English voice
    for v in voices:
        if "english" in v.name.lower() or "zira" in v.name.lower() or "david" in v.name.lower():
            engine.setProperty("voice", v.id)
            break
    engine.setProperty("rate", 155)
    engine.setProperty("volume", 1.0)
    return engine

TTS = init_tts()

def speak(text, filename):
    """Save narration to WAV file, return duration in seconds."""
    path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(path):
        TTS.save_to_file(text, path)
        TTS.runAndWait()
    # estimate duration by word count if file exists
    words = len(text.split())
    return max(3.0, words / 2.5)

# ── Figure helpers ─────────────────────────────────────────────────────────────
def new_fig():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off")
    # subtle grid
    for x in range(0, 101, 5):
        ax.axvline(x, color="#1A2E42", lw=0.3, zorder=0)
    for y in range(0, 101, 5):
        ax.axhline(y, color="#1A2E42", lw=0.3, zorder=0)
    return fig, ax

def add_footer(ax, text="Elliott Wave & MACD Divergences — Complete Trading Course"):
    ax.add_patch(mpatches.Rectangle((0, 0), 100, 3, color=PANEL, zorder=5))
    ax.text(50, 1.3, text, color=MGRAY, fontsize=7, ha="center", va="center",
            fontfamily="monospace", zorder=6)

def add_header_bar(ax, title, subtitle=""):
    ax.add_patch(mpatches.Rectangle((0, 91), 100, 9, color=PANEL, zorder=5))
    ax.plot([0, 100], [90.5, 90.5], color=ACCENT, lw=1.5, zorder=6)
    ax.text(50, 95.5, title, color=ACCENT, fontsize=18, ha="center", va="center",
            fontweight="bold", zorder=7)
    if subtitle:
        ax.text(50, 92.3, subtitle, color=GOLD, fontsize=10, ha="center", va="center", zorder=7)

def save_frame(fig, path):
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0,
                facecolor=BG, edgecolor="none")
    plt.close(fig)

def frames_to_clip(frame_paths, audio_path, duration):
    """Create a video clip from frame list + audio."""
    clip = ImageSequenceClip(frame_paths, fps=FPS)
    clip = clip.set_duration(duration)
    if os.path.exists(audio_path):
        audio = AudioFileClip(audio_path).subclip(0, min(duration, AudioFileClip(audio_path).duration))
        clip = clip.set_audio(audio)
    return clip

def still_frames(fig_path, duration, fps=FPS):
    """Repeat a single frame for <duration> seconds."""
    n = max(1, int(duration * fps))
    return [fig_path] * n

# ══════════════════════════════════════════════════════════════════════════════
# SCENE RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

# ── INTRO ─────────────────────────────────────────────────────────────────────
def render_intro():
    print("  Rendering INTRO...")
    narration = (
        "Welcome to the complete course on Elliott Wave Theory and MACD Divergence trading. "
        "In this course you will master wave counting, divergence identification, "
        "and how to combine both into high-probability trading setups "
        "across any market and timeframe. Let's get started."
    )
    audio_path = os.path.join(AUDIO_DIR, "intro.wav")
    dur = speak(narration, "intro.wav")

    frames = []
    n_frames = int(dur * FPS)
    modules = [
        "Module 1 — Elliott Wave Theory Foundations",
        "Module 2 — Advanced Wave Structures",
        "Module 3 — MACD Indicator Deep Dive",
        "Module 4 — Divergence Trading Strategies",
        "Module 5 — Integrating Waves with MACD",
        "Module 6 — Entry, Exit & Risk Management",
        "Module 7 — Multi-Timeframe Analysis",
        "Module 8 — Trade Examples & Checklists",
    ]
    for i in range(n_frames):
        t = i / FPS
        fig, ax = new_fig()
        # animated wave line in background
        xs = np.linspace(0, 100, 300)
        wave_pts = [20,38,28,55,42,70,55,82,65,88]  # simplified wave
        ys = np.interp(xs, np.linspace(0,100,len(wave_pts)), wave_pts)
        progress = min(1.0, t / (dur * 0.3))
        visible = int(progress * len(xs))
        if visible > 1:
            ax.plot(xs[:visible], ys[:visible], color=ACCENT, lw=1.5, alpha=0.25, zorder=1)

        # title fade in
        title_alpha = min(1.0, t / 1.5)
        ax.text(50, 72, "ELLIOTT WAVE", color=ACCENT, fontsize=38, ha="center",
                fontweight="bold", alpha=title_alpha, zorder=3)
        ax.text(50, 63, "&", color=ORANGE, fontsize=22, ha="center",
                fontweight="bold", alpha=title_alpha, zorder=3)
        ax.text(50, 54, "MACD DIVERGENCES", color=ACCENT, fontsize=38, ha="center",
                fontweight="bold", alpha=title_alpha, zorder=3)
        # divider line
        if t > 1.5:
            ax.plot([15, 85], [50, 50], color=ORANGE, lw=2, zorder=3)
        # subtitle
        sub_alpha = min(1.0, max(0, (t - 1.8) / 1.0))
        ax.text(50, 46, "Complete Professional Trading Course", color=LGRAY,
                fontsize=14, ha="center", alpha=sub_alpha, zorder=3)
        # module list fade in
        for j, m in enumerate(modules):
            m_alpha = min(1.0, max(0, (t - 2.5 - j * 0.3) / 0.5))
            ax.text(50, 40 - j * 3.5, m, color=LGRAY, fontsize=9,
                    ha="center", alpha=m_alpha, zorder=3)
        # disclaimer
        ax.text(50, 5.5, "For educational purposes only. Not financial advice.",
                color=MGRAY, fontsize=7, ha="center", zorder=3)
        add_footer(ax)
        path = os.path.join(FRAMES_DIR, f"intro_{i:05d}.png")
        save_frame(fig, path)
        frames.append(path)

    clip = ImageSequenceClip(frames, fps=FPS).set_duration(dur)
    if os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        clip = clip.set_audio(audio.subclip(0, min(dur, audio.duration)))
    return clip


# ── MODULE 1 — Elliott Wave Foundations ───────────────────────────────────────
def render_module1():
    print("  Rendering Module 1...")
    clips = []

    # --- Scene 1.1: History ---
    narration1 = (
        "Ralph Nelson Elliott discovered that financial markets move in predictable, "
        "repetitive wave patterns driven by collective investor psychology. "
        "In 1938 he published The Wave Principle, laying the foundation for what "
        "we now call Elliott Wave Theory. The core insight: markets alternate between "
        "impulsive trend-following waves and corrective counter-trend waves."
    )
    dur1 = speak(narration1, "m1_history.wav")
    fig, ax = new_fig()
    add_header_bar(ax, "Module 1 — Elliott Wave Foundations", "1.1 History & Discovery")
    ax.text(50, 70, "R.N. Elliott — 1871 to 1948", color=GOLD, fontsize=18, ha="center", fontweight="bold")
    ax.text(50, 63, "1938 — The Wave Principle published", color=LGRAY, fontsize=12, ha="center")
    ax.text(50, 58, "1939 — 12 articles in Financial World magazine", color=LGRAY, fontsize=12, ha="center")
    ax.text(50, 53, "1946 — Nature's Law: The Secret of the Universe", color=LGRAY, fontsize=12, ha="center")
    ax.text(50, 44, "Markets move in WAVES driven by crowd psychology", color=ACCENT,
            fontsize=14, ha="center", fontweight="bold")
    ax.text(50, 37, "Impulse Waves → move WITH the trend (5 waves)",
            color=GREEN, fontsize=11, ha="center")
    ax.text(50, 32, "Corrective Waves → move AGAINST the trend (3 waves)",
            color=RED, fontsize=11, ha="center")
    ax.text(50, 22, "Patterns are FRACTAL — same structure on all timeframes",
            color=ORANGE, fontsize=11, ha="center", style="italic")
    add_footer(ax)
    p = os.path.join(FRAMES_DIR, "m1_hist.png"); save_frame(fig, p)
    frm = still_frames(p, dur1)
    c = ImageSequenceClip(frm, fps=FPS).set_duration(dur1)
    if os.path.exists(os.path.join(AUDIO_DIR, "m1_history.wav")):
        a = AudioFileClip(os.path.join(AUDIO_DIR, "m1_history.wav"))
        c = c.set_audio(a.subclip(0, min(dur1, a.duration)))
    clips.append(c)

    # --- Scene 1.2: 5-Wave Impulse animated ---
    narration2 = (
        "An impulse wave has five sub-waves. Waves one, three, and five move in the "
        "direction of the trend, while waves two and four are counter-trend corrections. "
        "Three absolute rules govern every valid impulse: "
        "Wave two cannot retrace more than one hundred percent of wave one. "
        "Wave three is never the shortest of waves one, three, and five. "
        "And wave four cannot overlap into wave one price territory."
    )
    dur2 = speak(narration2, "m1_impulse.wav")
    n2 = int(dur2 * FPS)
    wave_x = [10, 25, 35, 55, 65, 82]
    wave_y = [20, 52, 34, 72, 50, 78]
    labels  = ["0", "1", "2", "3", "4", "5"]
    colors  = [GREEN, RED, GREEN, RED, GREEN]
    frames2 = []
    for i in range(n2):
        t = i / FPS
        fig, ax = new_fig()
        add_header_bar(ax, "Module 1 — Elliott Wave Foundations", "1.2 The 5-Wave Impulse")
        progress = min(5, int(t / (dur2 / 6) * 5))
        for seg in range(min(progress, 5)):
            ax.annotate("", xy=(wave_x[seg+1], wave_y[seg+1]),
                        xytext=(wave_x[seg], wave_y[seg]),
                        arrowprops=dict(arrowstyle="-|>", color=colors[seg], lw=2.5,
                                        mutation_scale=15))
        for pt in range(min(progress+1, 6)):
            ax.plot(wave_x[pt], wave_y[pt], "o", color=GOLD, ms=8, zorder=5)
            ax.text(wave_x[pt], wave_y[pt] + (4 if pt%2==0 else -6),
                    labels[pt], color=GOLD, fontsize=11, ha="center", fontweight="bold")
        # wave labels
        mid_labels = [
            (17.5, 44, "Wave 1", GREEN), (30, 26, "Wave 2", RED),
            (45, 62, "Wave 3\n(Longest)", GREEN), (60, 38, "Wave 4", RED),
            (73, 68, "Wave 5", GREEN)
        ]
        for mx, my, ml, mc in mid_labels[:progress]:
            ax.text(mx, my, ml, color=mc, fontsize=8, ha="center",
                    fontweight="bold", alpha=0.85)
        # rules box
        rules = ["Rule 1: Wave 2 cannot retrace 100%+ of Wave 1",
                 "Rule 2: Wave 3 is NEVER the shortest wave",
                 "Rule 3: Wave 4 cannot overlap Wave 1 territory"]
        for ri, rule in enumerate(rules):
            ralpha = min(1.0, max(0, (t - dur2*0.5 - ri*1.5) / 1.0))
            ax.text(50, 17 - ri*5, rule, color=ORANGE, fontsize=9,
                    ha="center", alpha=ralpha, fontweight="bold")
        add_footer(ax)
        fp = os.path.join(FRAMES_DIR, f"m1_imp_{i:05d}.png"); save_frame(fig, fp)
        frames2.append(fp)
    c2 = ImageSequenceClip(frames2, fps=FPS).set_duration(dur2)
    ap2 = os.path.join(AUDIO_DIR, "m1_impulse.wav")
    if os.path.exists(ap2):
        a2 = AudioFileClip(ap2)
        c2 = c2.set_audio(a2.subclip(0, min(dur2, a2.duration)))
    clips.append(c2)

    # --- Scene 1.3: A-B-C Correction ---
    narration3 = (
        "After every five-wave impulse, a three-wave correction follows. "
        "The most common is the A-B-C structure. Wave A moves against the prior trend. "
        "Wave B partially retraces wave A. Wave C then completes the correction, "
        "often reaching one hundred percent or one-sixty-one-point-eight percent of wave A. "
        "Common corrective forms include zigzags, flats, and triangles."
    )
    dur3 = speak(narration3, "m1_abc.wav")
    fig3, ax3 = new_fig()
    add_header_bar(ax3, "Module 1 — Elliott Wave Foundations", "1.3 A-B-C Corrective Waves")
    abc_x = [15, 40, 55, 80]
    abc_y = [68, 32, 52, 18]
    abc_l = ["0", "A", "B", "C"]
    abc_c = [RED, GREEN, RED]
    for i in range(3):
        ax3.annotate("", xy=(abc_x[i+1], abc_y[i+1]), xytext=(abc_x[i], abc_y[i]),
                     arrowprops=dict(arrowstyle="-|>", color=abc_c[i], lw=2.5, mutation_scale=15))
    for i in range(4):
        ax3.plot(abc_x[i], abc_y[i], "o", color=GOLD, ms=8, zorder=5)
        off = 5 if i in [0,2] else -7
        ax3.text(abc_x[i], abc_y[i]+off, abc_l[i], color=GOLD, fontsize=12, ha="center", fontweight="bold")
    ax3.text(27, 42, "Wave A\n(Down)", color=RED, fontsize=9, ha="center", fontweight="bold")
    ax3.text(48, 58, "Wave B\n(Up)", color=GREEN, fontsize=9, ha="center", fontweight="bold")
    ax3.text(68, 27, "Wave C\n(Down)", color=RED, fontsize=9, ha="center", fontweight="bold")
    types = [("Zigzag  5-3-5", 22), ("Flat  3-3-5", 17), ("Triangle  3-3-3-3-3", 12)]
    ax3.text(50, 26, "Corrective Pattern Types:", color=GOLD, fontsize=10, ha="center", fontweight="bold")
    for lbl, y in types:
        ax3.text(50, y, lbl, color=LGRAY, fontsize=9, ha="center")
    add_footer(ax3)
    p3 = os.path.join(FRAMES_DIR, "m1_abc.png"); save_frame(fig3, p3)
    frm3 = still_frames(p3, dur3)
    c3 = ImageSequenceClip(frm3, fps=FPS).set_duration(dur3)
    ap3 = os.path.join(AUDIO_DIR, "m1_abc.wav")
    if os.path.exists(ap3):
        a3 = AudioFileClip(ap3)
        c3 = c3.set_audio(a3.subclip(0, min(dur3, a3.duration)))
    clips.append(c3)

    return concatenate_videoclips(clips)

# ── MODULE 2 — Advanced Structures ────────────────────────────────────────────
def render_module2():
    print("  Rendering Module 2...")
    clips = []

    # Scene 2.1 Extensions + Fibonacci
    narration1 = (
        "Wave extensions occur when one of the motive waves elongates significantly. "
        "Wave three extensions are the most common and most powerful, "
        "often reaching one-sixty-one-point-eight percent of wave one. "
        "Fibonacci ratios are the mathematical backbone of Elliott Wave theory. "
        "Wave two typically retraces fifty to sixty-one-point-eight percent of wave one. "
        "Wave three targets one-sixty-one-point-eight percent of wave one. "
        "Wave four retraces thirty-eight-point-two percent of wave three. "
        "When multiple Fibonacci projections converge on the same zone, "
        "that cluster is a high-probability reversal area."
    )
    dur1 = speak(narration1, "m2_fib.wav")
    fig, ax = new_fig()
    add_header_bar(ax, "Module 2 — Advanced Wave Structures", "Fibonacci Levels & Extensions")
    # Draw wave with fib retracements
    low_x, low_y  = 12, 18
    high_x, high_y = 55, 72
    ax.annotate("", xy=(high_x, high_y), xytext=(low_x, low_y),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=3, mutation_scale=18))
    # Fib lines
    fibs = [(0.0,"0.0%",GOLD),(0.236,"23.6%",MGRAY),(0.382,"38.2%",GREEN),
            (0.5,"50.0%",ACCENT),(0.618,"61.8%",ORANGE),(0.786,"78.6%",MGRAY),(1.0,"100%",GOLD)]
    rng = high_y - low_y
    for ratio, lbl, col in fibs:
        y = high_y - ratio * rng
        ax.axhline(y, xmin=0.52, xmax=0.88, color=col, lw=0.9 if ratio not in [0,1] else 1.5,
                   linestyle="--" if ratio not in [0,1] else "-", alpha=0.8)
        ax.text(90, y, lbl, color=col, fontsize=8, va="center", fontweight="bold")
    # Retracement arrow
    ret_y = high_y - 0.618 * rng
    ax.annotate("", xy=(80, ret_y), xytext=(high_x, high_y),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=2, mutation_scale=14))
    ax.text(68, ret_y + 3, "Wave 2\n~61.8%", color=ORANGE, fontsize=8, ha="center", fontweight="bold")
    # Extension box
    ax.add_patch(mpatches.FancyBboxPatch((5, 4), 42, 28,
                 boxstyle="round,pad=0.5", linewidth=1.5, edgecolor=ACCENT, facecolor=PANEL))
    ext_data = [
        ("Wave 2 retraces:", "50% – 61.8% of Wave 1"),
        ("Wave 3 targets:", "161.8% of Wave 1"),
        ("Wave 4 retraces:", "38.2% of Wave 3"),
        ("Wave 5 targets:", "Equal to Wave 1"),
        ("Wave C targets:", "100% – 161.8% of Wave A"),
    ]
    ax.text(26, 30, "Key Fibonacci Relationships", color=GOLD, fontsize=10,
            ha="center", fontweight="bold")
    for j, (k, v) in enumerate(ext_data):
        ax.text(9, 26 - j*4.5, k, color=ACCENT, fontsize=8, fontweight="bold")
        ax.text(30, 26 - j*4.5, v, color=LGRAY, fontsize=8)
    add_footer(ax)
    p = os.path.join(FRAMES_DIR, "m2_fib.png"); save_frame(fig, p)
    frm = still_frames(p, dur1)
    c = ImageSequenceClip(frm, fps=FPS).set_duration(dur1)
    ap = os.path.join(AUDIO_DIR, "m2_fib.wav")
    if os.path.exists(ap):
        a = AudioFileClip(ap); c = c.set_audio(a.subclip(0, min(dur1, a.duration)))
    clips.append(c)

    # Scene 2.2 Ending Diagonal
    narration2 = (
        "Ending diagonals are wedge-shaped wave fives. "
        "All sub-waves overlap and the pattern contracts toward a point. "
        "An ending diagonal signals exhaustion of the trend. "
        "When combined with bearish MACD divergence, it creates one of the "
        "highest-probability reversal setups in all of technical analysis."
    )
    dur2 = speak(narration2, "m2_diag.wav")
    fig2, ax2 = new_fig()
    add_header_bar(ax2, "Module 2 — Advanced Wave Structures", "Ending Diagonal Triangle")
    # Draw wedge
    upper = [(20,45),(34,60),(48,55),(62,68),(76,63)]
    lower = [(20,45),(34,48),(48,42),(62,52),(76,47)]
    ax2.plot([p[0] for p in upper], [p[1] for p in upper], color=GREEN, lw=2, label="Upper trendline")
    ax2.plot([p[0] for p in lower], [p[1] for p in lower], color=GREEN, lw=2, linestyle="--")
    for i in range(len(upper)-1):
        ax2.plot([upper[i][0], lower[i+1][0]], [upper[i][1], lower[i+1][1]],
                 color=GREEN if i%2==0 else RED, lw=2)
    ax2.text(48, 72, "ENDING DIAGONAL (Wave 5)", color=ORANGE, fontsize=11,
             ha="center", fontweight="bold")
    ax2.text(48, 68, "Wedge shape — all waves overlap", color=LGRAY, fontsize=9, ha="center")
    ax2.annotate("", xy=(82, 42), xytext=(76, 63),
                 arrowprops=dict(arrowstyle="-|>", color=RED, lw=3, mutation_scale=18))
    ax2.text(85, 50, "REVERSAL\nAHEAD", color=RED, fontsize=11, ha="center",
             fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.3", facecolor=PANEL, edgecolor=RED))
    ax2.text(48, 22, "⚡  Ending Diagonal + MACD Bearish Divergence = HIGHEST PROBABILITY SELL",
             color=GOLD, fontsize=9, ha="center", fontweight="bold")
    add_footer(ax2)
    p2 = os.path.join(FRAMES_DIR, "m2_diag.png"); save_frame(fig2, p2)
    frm2 = still_frames(p2, dur2)
    c2 = ImageSequenceClip(frm2, fps=FPS).set_duration(dur2)
    ap2 = os.path.join(AUDIO_DIR, "m2_diag.wav")
    if os.path.exists(ap2):
        a2 = AudioFileClip(ap2); c2 = c2.set_audio(a2.subclip(0, min(dur2, a2.duration)))
    clips.append(c2)

    return concatenate_videoclips(clips)


# ── MODULE 3 — MACD Deep Dive ──────────────────────────────────────────────────
def render_module3():
    print("  Rendering Module 3...")
    clips = []

    narration1 = (
        "The MACD indicator was created by Gerald Appel in the nineteen seventies. "
        "It consists of three components: the MACD line, which is the twelve-period EMA "
        "minus the twenty-six-period EMA; the signal line, which is the nine-period EMA "
        "of the MACD line; and the histogram, which shows the difference between the "
        "MACD and signal lines. The histogram is the most important component for "
        "divergence analysis because it measures momentum acceleration, not just direction."
    )
    dur1 = speak(narration1, "m3_macd.wav")
    fig, ax = new_fig()
    add_header_bar(ax, "Module 3 — MACD Indicator Deep Dive", "Construction & Components")
    # Simulated price and MACD
    xs = np.linspace(0, 100, 150)
    price = 50 + 15*np.sin(xs/10) + 5*np.sin(xs/4) + xs/10
    price = (price - price.min()) / (price.max()-price.min()) * 35 + 52
    macd_line = 5*np.sin(xs/10 - 0.5)
    signal_line = 4*np.sin(xs/10 - 1.2)
    hist = macd_line - signal_line
    # Price panel
    ax.plot(xs*0.65+5, price, color=LGRAY, lw=1.5, label="Price")
    ax.text(5, 90, "PRICE", color=LGRAY, fontsize=8, fontweight="bold")
    # MACD panel
    ax2 = ax.twinx()
    ax2.axis("off")
    ax2.set_xlim(0, 100); ax2.set_ylim(0, 100)
    macd_ys = (macd_line / macd_line.max()) * 12 + 33
    sig_ys  = (signal_line / macd_line.max()) * 12 + 33
    hist_ys = (hist / abs(hist).max()) * 8
    zero_y = 33
    ax2.axhline(zero_y, color=MGRAY, lw=0.8, xmin=0.05, xmax=0.7)
    for j in range(len(xs)-1):
        col = GREEN if hist[j] >= 0 else RED
        ax2.bar(xs[j]*0.65+5, hist_ys[j], width=0.4, bottom=zero_y,
                color=col, alpha=0.7)
    ax2.plot(xs*0.65+5, macd_ys, color=ACCENT, lw=1.5)
    ax2.plot(xs*0.65+5, sig_ys,  color=ORANGE, lw=1.2, linestyle="--")
    ax2.text(5, 48, "MACD", color=ACCENT, fontsize=8, fontweight="bold")
    # Legend box
    ax.add_patch(mpatches.FancyBboxPatch((68, 30), 29, 42,
                 boxstyle="round,pad=0.5", linewidth=1.5, edgecolor=ACCENT, facecolor=PANEL))
    items = [
        ("MACD Line", "EMA(12) − EMA(26)", ACCENT),
        ("Signal Line", "EMA(9) of MACD", ORANGE),
        ("Histogram", "MACD − Signal", GOLD),
        ("Default", "12  /  26  /  9", LGRAY),
    ]
    ax.text(82, 70, "MACD Components", color=GOLD, fontsize=9, ha="center", fontweight="bold")
    for j, (k, v, col) in enumerate(items):
        ax.text(70, 64-j*7, k+":", color=col, fontsize=8, fontweight="bold")
        ax.text(70, 60-j*7, v, color=LGRAY, fontsize=7.5)
    add_footer(ax)
    p = os.path.join(FRAMES_DIR, "m3_macd.png"); save_frame(fig, p)
    frm = still_frames(p, dur1)
    c = ImageSequenceClip(frm, fps=FPS).set_duration(dur1)
    ap = os.path.join(AUDIO_DIR, "m3_macd.wav")
    if os.path.exists(ap):
        a = AudioFileClip(ap); c = c.set_audio(a.subclip(0, min(dur1, a.duration)))
    clips.append(c)

    # MACD by wave
    narration2 = (
        "Understanding MACD momentum by wave is critical. "
        "During wave one, the MACD turns up from oversold. "
        "During wave three, the MACD reaches its absolute peak — the strongest histogram bars. "
        "During wave four, MACD corrects but holds above zero. "
        "And during wave five, the MACD rises again but fails to reach the wave three peak. "
        "This failure is the bearish divergence signal that confirms wave five is ending."
    )
    dur2 = speak(narration2, "m3_waves.wav")
    fig2, ax2_m = new_fig()
    add_header_bar(ax2_m, "Module 3 — MACD Deep Dive", "MACD Momentum by Elliott Wave")
    wx = [12, 25, 35, 52, 63, 78]
    wy = [22, 48, 32, 68, 50, 72]
    wl = ["0","1","2","3","4","5"]
    wc = [GREEN,RED,GREEN,RED,GREEN]
    for i in range(5):
        ax2_m.annotate("", xy=(wx[i+1],wy[i+1]), xytext=(wx[i],wy[i]),
                       arrowprops=dict(arrowstyle="-|>", color=wc[i], lw=2.5, mutation_scale=14))
    for i in range(6):
        ax2_m.plot(wx[i], wy[i], "o", color=GOLD, ms=7, zorder=5)
        ax2_m.text(wx[i], wy[i]+(4 if i%2==0 else -5), wl[i], color=GOLD,
                   fontsize=10, ha="center", fontweight="bold")
    # MACD bars below
    bar_xs = wx
    bar_h  = [0, 14, 5, 30, 12, 20]  # bar heights
    zero_b = 14
    for j, (bx, bh) in enumerate(zip(bar_xs, bar_h)):
        col = GREEN if bh > 0 else RED
        ax2_m.add_patch(mpatches.Rectangle((bx-2, zero_b), 4, bh, color=col, alpha=0.8))
    ax2_m.axhline(zero_b, color=MGRAY, lw=0.8, xmin=0.05, xmax=0.85)
    ax2_m.text(10, 14+31, "MACD PEAK\n(Wave 3)", color=GOLD, fontsize=8,
               ha="center", fontweight="bold",
               bbox=dict(boxstyle="round", facecolor=PANEL, edgecolor=GOLD))
    # divergence arrow
    ax2_m.annotate("", xy=(78, zero_b+20), xytext=(52, zero_b+30),
                   arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.5, linestyle="dashed",
                                   mutation_scale=12))
    ax2_m.text(65, zero_b+27, "Lower high\n= Bearish Div", color=RED,
               fontsize=7.5, ha="center",
               bbox=dict(boxstyle="round", facecolor=PANEL, edgecolor=RED, alpha=0.8))
    ax2_m.text(85, 14, "MACD", color=ACCENT, fontsize=8, fontweight="bold")
    add_footer(ax2_m)
    p2 = os.path.join(FRAMES_DIR, "m3_waves.png"); save_frame(fig2, p2)
    frm2 = still_frames(p2, dur2)
    c2 = ImageSequenceClip(frm2, fps=FPS).set_duration(dur2)
    ap2 = os.path.join(AUDIO_DIR, "m3_waves.wav")
    if os.path.exists(ap2):
        a2 = AudioFileClip(ap2); c2 = c2.set_audio(a2.subclip(0, min(dur2, a2.duration)))
    clips.append(c2)

    return concatenate_videoclips(clips)

# ── MODULE 4 — Divergence ─────────────────────────────────────────────────────
def render_module4():
    print("  Rendering Module 4...")
    clips = []

    def divergence_scene(bull, narration, audio_file, scene_id):
        dur = speak(narration, audio_file)
        n = int(dur * FPS)
        frames = []
        price_pts_bull  = [(12,38),(28,28),(48,42),(68,22),(85,32)]
        price_pts_bear  = [(12,35),(28,55),(48,40),(68,68),(85,58)]
        macd_bull_h     = [-22, -30, -15, -10, -6]
        macd_bear_h     = [ 20,  28,  14,  10,  7]

        price_pts = price_pts_bull if bull else price_pts_bear
        macd_h    = macd_bull_h    if bull else macd_bear_h
        div_color = GREEN if bull else RED
        title_txt = "Regular Bullish Divergence" if bull else "Regular Bearish Divergence"
        sub_txt   = "Price: Lower Lows  |  MACD: Higher Lows" if bull else "Price: Higher Highs  |  MACD: Lower Highs"

        for i in range(n):
            t = i / FPS
            fig, ax = new_fig()
            add_header_bar(ax, "Module 4 — Divergence Trading", title_txt)
            ax.text(50, 87, sub_txt, color=GOLD, fontsize=10, ha="center", fontweight="bold")

            # Price panel
            ax.text(8, 82, "PRICE", color=LGRAY, fontsize=9, fontweight="bold")
            progress = min(len(price_pts)-1, int(t / (dur*0.5) * (len(price_pts)-1)))
            for j in range(progress):
                ax.plot([price_pts[j][0], price_pts[j+1][0]],
                        [price_pts[j][1]+30, price_pts[j+1][1]+30],
                        color=LGRAY, lw=2)
            # pivot dots
            pivot_idx = [1, 3]
            for pi in pivot_idx:
                if pi <= progress:
                    ax.plot(price_pts[pi][0], price_pts[pi][1]+30, "o",
                            color=div_color, ms=8, zorder=5)
            # MACD panel
            zero_y = 22
            ax.axhline(zero_y, color=MGRAY, lw=0.8, xmin=0.05, xmax=0.9)
            ax.text(8, 26, "MACD", color=ACCENT, fontsize=9, fontweight="bold")
            for j, (bx, bh) in enumerate(zip([p[0] for p in price_pts], macd_h)):
                if j > progress: break
                col = GREEN if bh > 0 else RED
                bhr = abs(bh) * 0.55
                if bh < 0:
                    ax.add_patch(mpatches.Rectangle((bx-4, zero_y-bhr), 8, bhr,
                                                    color=col, alpha=0.8))
                else:
                    ax.add_patch(mpatches.Rectangle((bx-4, zero_y), 8, bhr,
                                                    color=col, alpha=0.8))

            # Draw divergence trendlines after enough progress
            if progress >= 3 and t > dur * 0.55:
                p1 = price_pts[1]; p2 = price_pts[3]
                m1y = zero_y - abs(macd_h[1])*0.55 if bull else zero_y + macd_h[1]*0.55
                m2y = zero_y - abs(macd_h[3])*0.55 if bull else zero_y + macd_h[3]*0.55
                ax.plot([p1[0], p2[0]], [p1[1]+30, p2[1]+30],
                        color=div_color, lw=1.8, linestyle="--")
                ax.plot([p1[0], p2[0]], [m1y, m2y],
                        color=div_color, lw=1.8, linestyle="--")
                ax.text(50, 10,
                        "DIVERGENCE CONFIRMED — Wait for trigger candle",
                        color=div_color, fontsize=10, ha="center", fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.4", facecolor=PANEL,
                                  edgecolor=div_color))
            add_footer(ax)
            fp = os.path.join(FRAMES_DIR, f"{scene_id}_{i:05d}.png"); save_frame(fig, fp)
            frames.append(fp)

        clip = ImageSequenceClip(frames, fps=FPS).set_duration(dur)
        ap = os.path.join(AUDIO_DIR, audio_file)
        if os.path.exists(ap):
            a = AudioFileClip(ap); clip = clip.set_audio(a.subclip(0, min(dur, a.duration)))
        return clip

    n_bull = (
        "Regular bullish divergence forms when price makes a lower low "
        "while the MACD histogram makes a higher low. "
        "This tells us that even though price fell further, the selling momentum is weakening. "
        "Draw trendlines on both the price lows and the MACD lows — "
        "they will slope in opposite directions. "
        "Wait for a bullish trigger: an engulfing candle, a hammer, or the MACD crossing above signal."
    )
    clips.append(divergence_scene(True,  n_bull, "m4_bull.wav", "m4b"))

    n_bear = (
        "Regular bearish divergence forms when price makes a higher high "
        "while the MACD histogram makes a lower high. "
        "Price is breaking new highs, but momentum is secretly fading. "
        "This is the warning sign that the trend is about to reverse. "
        "Confirm with a bearish trigger: a shooting star, a bearish engulfing, "
        "or the MACD line crossing below the signal line."
    )
    clips.append(divergence_scene(False, n_bear, "m4_bear.wav", "m4r"))

    # Hidden divergence scene
    narration3 = (
        "Hidden divergence is the opposite of regular divergence — it signals trend continuation. "
        "Hidden bullish divergence occurs when price makes a higher low during a pullback, "
        "but the MACD makes a lower low. This confirms the uptrend is intact and "
        "the correction is complete. It is especially powerful at wave two and wave four pullbacks. "
        "Hidden bearish divergence is the mirror image — use it to sell bounces in downtrends."
    )
    dur3 = speak(narration3, "m4_hidden.wav")
    fig3, ax3 = new_fig()
    add_header_bar(ax3, "Module 4 — Divergence Trading", "Hidden Divergence — Continuation Signal")
    data = [
        ("REGULAR BULLISH",  "Price: Lower Low",  "MACD: Higher Low",  "→ REVERSAL BUY",   GREEN,  30),
        ("REGULAR BEARISH",  "Price: Higher High", "MACD: Lower High",  "→ REVERSAL SELL",  RED,    52),
        ("HIDDEN BULLISH",   "Price: Higher Low",  "MACD: Lower Low",   "→ CONTINUATION BUY", GREEN, 74),
        ("HIDDEN BEARISH",   "Price: Lower High",  "MACD: Higher High", "→ CONTINUATION SELL", RED, 20),
    ]
    for j, (name, pd, md, sig, col, y) in enumerate(data):
        ax3.add_patch(mpatches.FancyBboxPatch((5, y-6), 90, 12,
                      boxstyle="round,pad=0.3", lw=1.2, edgecolor=col, facecolor=PANEL))
        ax3.text(10, y+1, name, color=col, fontsize=10, fontweight="bold", va="center")
        ax3.text(35, y+1, pd,   color=LGRAY, fontsize=9, va="center")
        ax3.text(57, y+1, md,   color=LGRAY, fontsize=9, va="center")
        ax3.text(78, y+1, sig,  color=col,   fontsize=9, fontweight="bold", va="center")
    add_footer(ax3)
    p3 = os.path.join(FRAMES_DIR, "m4_hidden.png"); save_frame(fig3, p3)
    frm3 = still_frames(p3, dur3)
    c3 = ImageSequenceClip(frm3, fps=FPS).set_duration(dur3)
    ap3 = os.path.join(AUDIO_DIR, "m4_hidden.wav")
    if os.path.exists(ap3):
        a3 = AudioFileClip(ap3); c3 = c3.set_audio(a3.subclip(0, min(dur3, a3.duration)))
    clips.append(c3)

    return concatenate_videoclips(clips)

# ── MODULE 5 — Integration ────────────────────────────────────────────────────
def render_module5():
    print("  Rendering Module 5...")
    clips = []

    narration1 = (
        "Module five is where everything comes together. "
        "Elliott Waves tell you WHERE in the cycle price is. "
        "MACD divergence tells you WHEN momentum is shifting. "
        "The most powerful setup in this entire course is the wave five bearish reversal. "
        "Wave three produces the strongest MACD histogram peak. "
        "When wave five then makes a new price high but the MACD histogram fails to "
        "match the wave three peak, bearish divergence is confirmed. "
        "This is your signal that the impulse is complete and a major correction is coming."
    )
    dur1 = speak(narration1, "m5_w5.wav")
    n1 = int(dur1 * FPS)
    wx = [8, 20, 30, 48, 60, 78]
    wy = [18, 42, 28, 65, 45, 70]
    wl = ["0","1","2","3","4","5"]
    wc = [GREEN,RED,GREEN,RED,GREEN]
    macd_h = [0, 14, 4, 28, 9, 20]

    frames1 = []
    for i in range(n1):
        t = i / FPS
        fig, ax = new_fig()
        add_header_bar(ax, "Module 5 — Wave + MACD Integration", "Wave 5 Bearish Divergence Setup")
        progress = min(5, int(t / (dur1 * 0.6) * 5))

        for seg in range(min(progress, 5)):
            ax.annotate("", xy=(wx[seg+1], wy[seg+1]+22), xytext=(wx[seg], wy[seg]+22),
                        arrowprops=dict(arrowstyle="-|>", color=wc[seg], lw=2.5, mutation_scale=14))
        for pt in range(min(progress+1, 6)):
            ax.plot(wx[pt], wy[pt]+22, "o", color=GOLD, ms=7, zorder=5)
            off = 4 if pt%2==0 else -5
            ax.text(wx[pt], wy[pt]+22+off, wl[pt], color=GOLD, fontsize=9,
                    ha="center", fontweight="bold")

        # MACD bars
        zero_b = 16
        ax.axhline(zero_b, color=MGRAY, lw=0.7, xmin=0.03, xmax=0.88)
        ax.text(5, 16+1.5, "MACD", color=ACCENT, fontsize=7, fontweight="bold")
        for j in range(min(progress+1, 6)):
            bh = macd_h[j] * 0.38
            col = GREEN if macd_h[j] >= 0 else RED
            ax.add_patch(mpatches.Rectangle((wx[j]-3, zero_b), 6, bh,
                                            color=col, alpha=0.85))

        # divergence trendlines appear at progress 5
        if progress >= 5 and t > dur1 * 0.65:
            # price: w3 to w5 (higher high)
            ax.plot([wx[3], wx[5]], [wy[3]+22, wy[5]+22],
                    color=ORANGE, lw=1.5, linestyle="--")
            # macd: w3 to w5 (lower high)
            ax.plot([wx[3], wx[5]], [zero_b+macd_h[3]*0.38, zero_b+macd_h[5]*0.38],
                    color=ORANGE, lw=1.5, linestyle="--")
            ax.text(63, 55, "⚠ BEARISH\nDIVERGENCE", color=RED, fontsize=9,
                    ha="center", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor=PANEL, edgecolor=RED))

        # checklist fades in late
        checks = [
            "✔ 5-wave impulse complete",
            "✔ Wave 3 had highest MACD peak",
            "✔ Wave 5 shows bearish divergence",
            "✔ Reversal trigger confirmed",
            "✔ Enter SHORT — target Wave 4 low",
        ]
        for ci, chk in enumerate(checks):
            calpha = min(1.0, max(0, (t - dur1*0.7 - ci*0.8)/0.6))
            ax.text(85, 72 - ci*7, chk, color=GREEN, fontsize=7.5,
                    ha="center", alpha=calpha, fontweight="bold")

        add_footer(ax)
        fp = os.path.join(FRAMES_DIR, f"m5_w5_{i:05d}.png"); save_frame(fig, fp)
        frames1.append(fp)

    c1 = ImageSequenceClip(frames1, fps=FPS).set_duration(dur1)
    ap1 = os.path.join(AUDIO_DIR, "m5_w5.wav")
    if os.path.exists(ap1):
        a1 = AudioFileClip(ap1); c1 = c1.set_audio(a1.subclip(0, min(dur1, a1.duration)))
    clips.append(c1)

    # Wave C bottom setup
    narration2 = (
        "The wave C bottom with bullish divergence is the premier buy setup. "
        "After a five-wave impulse completes, price corrects in A-B-C. "
        "Wave C makes a new low below wave A's end. "
        "But the MACD histogram at the wave C low is HIGHER than at the wave A low. "
        "Bullish divergence confirmed. "
        "Enter long on the first bullish candle. Stop below wave C low. "
        "Target the wave B high and beyond for a one-to-three risk reward or better."
    )
    dur2 = speak(narration2, "m5_wc.wav")
    fig2, ax2 = new_fig()
    add_header_bar(ax2, "Module 5 — Wave + MACD Integration", "Wave C Bottom — Bullish Divergence")
    # ABC on chart
    abc_x = [12, 35, 52, 75]
    abc_y = [68, 35, 55, 22]
    abc_l = ["End\nWave 5", "A", "B", "C"]
    abc_c = [RED, GREEN, RED]
    for i in range(3):
        ax2.annotate("", xy=(abc_x[i+1], abc_y[i+1]+15), xytext=(abc_x[i], abc_y[i]+15),
                     arrowprops=dict(arrowstyle="-|>", color=abc_c[i], lw=2.5, mutation_scale=14))
    for i in range(4):
        ax2.plot(abc_x[i], abc_y[i]+15, "o", color=GOLD, ms=7, zorder=5)
        ax2.text(abc_x[i], abc_y[i]+15 + (5 if i in [0,2] else -6),
                 abc_l[i], color=GOLD, fontsize=8, ha="center", fontweight="bold")
    # MACD bars
    zero_b = 14
    ax2.axhline(zero_b, color=MGRAY, lw=0.7, xmin=0.05, xmax=0.88)
    ax2.text(5, 16, "MACD", color=ACCENT, fontsize=7, fontweight="bold")
    macd_abc = [0, -22, -8, -16]
    for j, (bx, bh) in enumerate(zip(abc_x, macd_abc)):
        col = GREEN if bh >= 0 else RED
        bhr = abs(bh) * 0.35
        if bh < 0:
            ax2.add_patch(mpatches.Rectangle((bx-4, zero_b-bhr), 8, bhr, color=col, alpha=0.85))
        else:
            ax2.add_patch(mpatches.Rectangle((bx-4, zero_b), 8, bhr, color=col, alpha=0.85))
    # Divergence lines
    ax2.plot([abc_x[1], abc_x[3]], [abc_y[1]+15, abc_y[3]+15], color=GREEN, lw=1.8, linestyle="--")
    ax2.plot([abc_x[1], abc_x[3]], [zero_b-22*0.35, zero_b-16*0.35], color=GREEN, lw=1.8, linestyle="--")
    ax2.text(45, 10, "✔ BULLISH DIVERGENCE — Wave C Bottom", color=GREEN,
             fontsize=10, ha="center", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.4", facecolor=PANEL, edgecolor=GREEN))
    # Entry/SL/TP
    ax2.axhline(abc_y[3]+15+2, xmin=0.68, xmax=0.90, color=GOLD, lw=1.2, linestyle="--")
    ax2.axhline(abc_y[3]+15-3, xmin=0.68, xmax=0.90, color=RED, lw=1.2, linestyle="--")
    ax2.axhline(abc_y[2]+15,   xmin=0.68, xmax=0.90, color=GREEN, lw=1.2, linestyle="--")
    ax2.text(93, abc_y[3]+15+2, "ENTRY", color=GOLD, fontsize=7, va="center", fontweight="bold")
    ax2.text(93, abc_y[3]+15-3, "SL",   color=RED,  fontsize=7, va="center", fontweight="bold")
    ax2.text(93, abc_y[2]+15,   "TP",   color=GREEN,fontsize=7, va="center", fontweight="bold")
    add_footer(ax2)
    p2 = os.path.join(FRAMES_DIR, "m5_wc.png"); save_frame(fig2, p2)
    frm2 = still_frames(p2, dur2)
    c2 = ImageSequenceClip(frm2, fps=FPS).set_duration(dur2)
    ap2 = os.path.join(AUDIO_DIR, "m5_wc.wav")
    if os.path.exists(ap2):
        a2 = AudioFileClip(ap2); c2 = c2.set_audio(a2.subclip(0, min(dur2, a2.duration)))
    clips.append(c2)

    return concatenate_videoclips(clips)

# ── MODULE 6 — Risk Management ────────────────────────────────────────────────
def render_module6():
    print("  Rendering Module 6...")
    narration = (
        "Risk management separates profitable traders from the rest. "
        "Never enter on divergence alone — always wait for a trigger. "
        "The best triggers are a price candle closing beyond the pivot, "
        "a candlestick reversal pattern, or the MACD line crossing the signal line. "
        "Place your stop loss where the trade idea is definitively wrong — "
        "behind the divergence pivot with one ATR of buffer. "
        "For take profit, scale out: close thirty percent at one-to-one, "
        "forty percent at one-to-two, and trail the remainder to the wave projection target. "
        "Never risk more than one to two percent of your account on any single trade. "
        "Use the formula: position size equals account times risk percent "
        "divided by the stop loss distance."
    )
    dur = speak(narration, "m6_risk.wav")
    fig, ax = new_fig()
    add_header_bar(ax, "Module 6 — Risk Management", "Entry, Stop Loss & Position Sizing")

    # Trade setup diagram
    entry_y = 55; sl_y = 44; tp1_y = 63; tp2_y = 73; tp3_y = 80
    ax.add_patch(mpatches.Rectangle((12, sl_y), 60, entry_y-sl_y, color="#FF17441A",  alpha=0.3))
    ax.add_patch(mpatches.Rectangle((12, entry_y), 60, tp3_y-entry_y, color="#00E6761A", alpha=0.3))
    for y, lbl, col in [(entry_y,"ENTRY",GOLD),(sl_y,"STOP LOSS",RED),(tp1_y,"TP1  1:1",GREEN),
                        (tp2_y,"TP2  1:2",GREEN),(tp3_y,"TP3  1:3",GREEN)]:
        ax.axhline(y, xmin=0.10, xmax=0.75, color=col, lw=1.5,
                   linestyle="-" if lbl in ["ENTRY","STOP LOSS"] else "--")
        ax.text(9, y, lbl, color=col, fontsize=8, va="center", fontweight="bold", ha="right")
    # Price candles (simulated approach)
    cx = [18, 24, 30, 36, 42, 50, 58, 66]
    cy = [44, 46, 48, 50, 52, 55, 60, 68]
    ax.plot(cx, cy, color=LGRAY, lw=2)
    ax.plot(cx[-1], cy[-1], "^", color=GREEN, ms=10, zorder=5)

    # Scaling box
    ax.add_patch(mpatches.FancyBboxPatch((75, 40), 22, 42,
                 boxstyle="round,pad=0.4", lw=1.2, edgecolor=ACCENT, facecolor=PANEL))
    ax.text(86, 80, "SCALE OUT", color=GOLD, fontsize=9, ha="center", fontweight="bold")
    scale = [("TP1 (1:1)", "Close 30% → Move SL to BE", GREEN),
             ("TP2 (1:2)", "Close 40% → Trail SL", GREEN),
             ("TP3 (1:3)", "Trail remainder", GREEN)]
    for j, (t, d, c) in enumerate(scale):
        ax.text(77, 73-j*9, t, color=c, fontsize=7.5, fontweight="bold")
        ax.text(77, 69-j*9, d, color=LGRAY, fontsize=7)

    # Position sizing formula
    ax.add_patch(mpatches.FancyBboxPatch((5, 4), 90, 16,
                 boxstyle="round,pad=0.4", lw=1.5, edgecolor=GOLD, facecolor=PANEL))
    ax.text(50, 18, "POSITION SIZE = (Account × Risk%) ÷ (Entry − Stop in $)",
            color=GOLD, fontsize=10, ha="center", fontweight="bold")
    ax.text(50, 12, "Example: $10,000 account × 1% risk = $100 risk    |    SL = 50 pips    |    Size = 2 mini lots",
            color=LGRAY, fontsize=8, ha="center")
    ax.text(50, 7, "NEVER risk more than 1–2% per trade    |    Min R/R = 1:2    |    Ideal R/R = 1:3+",
            color=ORANGE, fontsize=8, ha="center", fontweight="bold")
    add_footer(ax)
    p = os.path.join(FRAMES_DIR, "m6_risk.png"); save_frame(fig, p)
    frm = still_frames(p, dur)
    c = ImageSequenceClip(frm, fps=FPS).set_duration(dur)
    ap = os.path.join(AUDIO_DIR, "m6_risk.wav")
    if os.path.exists(ap):
        a = AudioFileClip(ap); c = c.set_audio(a.subclip(0, min(dur, a.duration)))
    return c


# ── MODULE 7 — Multi-Timeframe ────────────────────────────────────────────────
def render_module7():
    print("  Rendering Module 7...")
    narration = (
        "Multi-timeframe analysis is what separates amateur traders from professionals. "
        "Always work top-down: start on the weekly chart to identify the dominant trend, "
        "move to the daily for wave structure and divergence zones, "
        "then use the four-hour and one-hour charts for entry timing. "
        "Only trade in the direction of the higher-timeframe wave. "
        "Never fight a wave three on the daily chart by taking a counter-trend trade on the hourly. "
        "When MACD divergence appears on two or three timeframes simultaneously, "
        "that is a major turning point signal with the highest probability."
    )
    dur = speak(narration, "m7_mtf.wav")
    fig, ax = new_fig()
    add_header_bar(ax, "Module 7 — Multi-Timeframe Analysis", "Top-Down Wave Counting")

    tfs = [
        ("WEEKLY",  "Grand Supercycle — identify dominant trend",  GOLD,   82),
        ("DAILY",   "Primary wave position + divergence zones",    ACCENT, 68),
        ("4H",      "Intermediate structure + entry preparation",  GREEN,  54),
        ("1H",      "Minor wave + trigger confirmation",           ORANGE, 40),
        ("15M",     "Fine-tune entry, stop, position size",        LGRAY,  26),
    ]
    for tf, desc, col, y in tfs:
        ax.add_patch(mpatches.FancyBboxPatch((8, y-5), 84, 10,
                     boxstyle="round,pad=0.3", lw=1.2, edgecolor=col, facecolor=PANEL))
        ax.text(20, y, tf, color=col, fontsize=10, va="center", fontweight="bold")
        ax.text(38, y, desc, color=LGRAY, fontsize=9, va="center")
        # arrow down to next
        if y > 26:
            ax.annotate("", xy=(50, y-6), xytext=(50, y-5),
                        arrowprops=dict(arrowstyle="-|>", color=MGRAY, lw=1.2, mutation_scale=10))

    ax.text(50, 14, "Multi-TF MACD Divergence Alignment = MAJOR TURNING POINT",
            color=GOLD, fontsize=10, ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=PANEL, edgecolor=GOLD))
    ax.text(50, 8.5, "Rule: ONLY trade in the direction of the higher-timeframe wave",
            color=ORANGE, fontsize=9, ha="center", style="italic")
    add_footer(ax)
    p = os.path.join(FRAMES_DIR, "m7_mtf.png"); save_frame(fig, p)
    frm = still_frames(p, dur)
    c = ImageSequenceClip(frm, fps=FPS).set_duration(dur)
    ap = os.path.join(AUDIO_DIR, "m7_mtf.wav")
    if os.path.exists(ap):
        a = AudioFileClip(ap); c = c.set_audio(a.subclip(0, min(dur, a.duration)))
    return c


# ── MODULE 8 — Checklist ──────────────────────────────────────────────────────
def render_module8():
    print("  Rendering Module 8...")
    narration = (
        "Before every trade, run through the master checklist. "
        "First: is the higher-timeframe wave direction clear? "
        "Second: which specific wave am I in, and does the count satisfy all three rules? "
        "Third: is MACD divergence confirmed on at least two timeframes? "
        "Fourth: do I have a clear entry trigger — a candlestick pattern or breakout? "
        "Fifth: is my stop loss at the logical invalidation level? "
        "Sixth: is my risk-reward at least one-to-two? "
        "Only take trades where ALL conditions are met. "
        "The best traders are not those who find every setup — "
        "they are those who wait for perfect alignment. "
        "Patience is your most valuable trading tool."
    )
    dur = speak(narration, "m8_check.wav")
    fig, ax = new_fig()
    add_header_bar(ax, "Module 8 — Master Trading Checklist", "Complete Pre-Trade Verification")

    sections = [
        ("WAVE STRUCTURE",  GREEN,  [
            "Higher-TF wave direction identified",
            "Wave count satisfies all 3 Elliott rules",
            "Wave at Fibonacci completion zone",
        ]),
        ("MACD DIVERGENCE", ACCENT, [
            "Divergence visible on 2+ timeframes",
            "Trendlines drawn on price AND MACD pivots",
            "Histogram divergence (not just MACD line)",
        ]),
        ("ENTRY TRIGGER",   GOLD,   [
            "Candlestick reversal or breakout present",
            "MACD signal line crossover confirms",
            "Entry candle has closed",
        ]),
        ("RISK MANAGEMENT", ORANGE, [
            "Stop at logical invalidation level",
            "Risk ≤ 2% of account",
            "R/R ≥ 1:2   |   TP1, TP2, TP3 set",
        ]),
    ]
    y_start = 82
    for sec, col, items in sections:
        ax.text(10, y_start, sec, color=col, fontsize=10, fontweight="bold")
        ax.axhline(y_start-2, xmin=0.07, xmax=0.93, color=col, lw=0.8, alpha=0.5)
        for j, item in enumerate(items):
            ax.text(13, y_start-6-j*5, f"☐  {item}", color=LGRAY, fontsize=8.5)
        y_start -= 6 + len(items)*5 + 4

    ax.text(50, 7, "ALL boxes checked = HIGH-PROBABILITY TRADE    |    Missing boxes = WAIT",
            color=GOLD, fontsize=9, ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=PANEL, edgecolor=GOLD))
    add_footer(ax)
    p = os.path.join(FRAMES_DIR, "m8_check.png"); save_frame(fig, p)
    frm = still_frames(p, dur)
    c = ImageSequenceClip(frm, fps=FPS).set_duration(dur)
    ap = os.path.join(AUDIO_DIR, "m8_check.wav")
    if os.path.exists(ap):
        a = AudioFileClip(ap); c = c.set_audio(a.subclip(0, min(dur, a.duration)))
    return c


# ── OUTRO ─────────────────────────────────────────────────────────────────────
def render_outro():
    print("  Rendering OUTRO...")
    narration = (
        "You now have all the tools to identify high-probability reversal setups "
        "using Elliott Wave structure and MACD divergence. "
        "Practice wave counting on historical charts. "
        "Apply the master checklist on every trade. "
        "Let the waves guide your direction and the divergence confirm your timing. "
        "Remember: patience, discipline, and consistent risk management "
        "are what separate successful traders. Good luck, and trade well."
    )
    dur = speak(narration, "outro.wav")
    n = int(dur * FPS)
    frames = []
    for i in range(n):
        t = i / FPS
        fig, ax = new_fig()
        # wave in background
        xs = np.linspace(0, 100, 300)
        ys_pts = [20,38,28,55,42,70,55,82,65,88]
        ys = np.interp(xs, np.linspace(0,100,len(ys_pts)), ys_pts)
        ax.plot(xs, ys, color=ACCENT, lw=1.2, alpha=0.15)
        # fade in text
        a1 = min(1.0, t / 2.0)
        ax.text(50, 62, "Master the Waves.", color=ACCENT, fontsize=32,
                ha="center", fontweight="bold", alpha=a1)
        ax.text(50, 52, "Trade the Divergences.", color=GOLD, fontsize=26,
                ha="center", fontweight="bold", alpha=a1)
        if t > 2.5:
            ax.plot([15, 85], [46, 46], color=ORANGE, lw=2)
        a2 = min(1.0, max(0, (t-3.0)/1.5))
        ax.text(50, 41, "Elliott Wave & MACD Divergences — Complete Course",
                color=LGRAY, fontsize=12, ha="center", alpha=a2)
        a3 = min(1.0, max(0, (t-4.5)/1.5))
        ax.text(50, 20, "For educational purposes only. Not financial advice.",
                color=MGRAY, fontsize=8, ha="center", alpha=a3, style="italic")
        add_footer(ax)
        fp = os.path.join(FRAMES_DIR, f"outro_{i:05d}.png"); save_frame(fig, fp)
        frames.append(fp)

    clip = ImageSequenceClip(frames, fps=FPS).set_duration(dur)
    ap = os.path.join(AUDIO_DIR, "outro.wav")
    if os.path.exists(ap):
        a = AudioFileClip(ap); clip = clip.set_audio(a.subclip(0, min(dur, a.duration)))
    return clip

# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║  Elliott Wave & MACD Divergences — Video Generator  ║")
    print("╚══════════════════════════════════════════════════════╝\n")
    print("Step 1/3 — Generating TTS audio + rendering frames...")

    scenes = [
        ("Intro",    render_intro),
        ("Module 1", render_module1),
        ("Module 2", render_module2),
        ("Module 3", render_module3),
        ("Module 4", render_module4),
        ("Module 5", render_module5),
        ("Module 6", render_module6),
        ("Module 7", render_module7),
        ("Module 8", render_module8),
        ("Outro",    render_outro),
    ]

    clips = []
    for name, fn in scenes:
        print(f"\n[{name}]")
        try:
            clip = fn()
            clips.append(clip)
            print(f"  ✔ {name} done — {clip.duration:.1f}s")
        except Exception as ex:
            print(f"  ✗ {name} FAILED: {ex}")

    print("\nStep 2/3 — Concatenating all scenes...")
    final = concatenate_videoclips(clips, method="compose")

    print(f"Step 3/3 — Writing final video: {FINAL_VIDEO}")
    print(f"  Total duration: {final.duration:.1f}s  ({final.duration/60:.1f} min)")
    final.write_videofile(
        FINAL_VIDEO,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=os.path.join(OUT_DIR, "temp_audio.m4a"),
        remove_temp=True,
        logger="bar",
        threads=4,
        preset="fast",
    )
    print(f"\n✅  Video saved to: {FINAL_VIDEO}")

if __name__ == "__main__":
    main()
