"""
Elliott Wave & MACD Divergences — Course Video Generator
Strategy: render KEYFRAME PNGs with matplotlib, use moviepy to build
slide-style clips with crossfades. Fast and professional.
"""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pyttsx3
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, ColorClip
)

# ── Paths ──────────────────────────────────────────────────────────────────────
OUT_DIR    = "video_output"
FRAMES_DIR = os.path.join(OUT_DIR, "frames")
AUDIO_DIR  = os.path.join(OUT_DIR, "audio")
FINAL      = os.path.join(OUT_DIR, "Elliott_Wave_MACD_Course.mp4")
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR,  exist_ok=True)

FPS   = 24
W, H  = 1920, 1080
DPI   = 100

# ── Colors ─────────────────────────────────────────────────────────────────────
BG    = "#0D1B2A";  PANEL = "#111F2E";  MGRAY = "#607080"
ACCENT= "#00D4FF";  GOLD  = "#FFD700";  ORANGE= "#FF6B35"
GREEN = "#00E676";  RED   = "#FF1744";  LGRAY = "#E0E0E0"; WHITE= "#FFFFFF"

# ── TTS ────────────────────────────────────────────────────────────────────────
_tts = None
def get_tts():
    global _tts
    if _tts is None:
        _tts = pyttsx3.init()
        for v in _tts.getProperty("voices"):
            if any(k in v.name.lower() for k in ["zira","david","english"]):
                _tts.setProperty("voice", v.id); break
        _tts.setProperty("rate", 150)
        _tts.setProperty("volume", 1.0)
    return _tts

def make_audio(text, fname):
    path = os.path.join(AUDIO_DIR, fname)
    if not os.path.exists(path):
        e = get_tts()
        e.save_to_file(text, path)
        e.runAndWait()
    try:
        return AudioFileClip(path), AudioFileClip(path).duration
    except:
        wpm = 150; dur = max(4.0, len(text.split()) / wpm * 60)
        return None, dur

# ── Figure helpers ─────────────────────────────────────────────────────────────
def new_fig():
    fig = plt.figure(figsize=(W/DPI, H/DPI), facecolor=BG)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BG); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis("off")
    for x in range(0,101,5): ax.axvline(x, color="#172330", lw=0.25, zorder=0)
    for y in range(0,101,5): ax.axhline(y, color="#172330", lw=0.25, zorder=0)
    return fig, ax

def hdr(ax, title, sub=""):
    ax.add_patch(mpatches.Rectangle((0,91),100,9,color=PANEL,zorder=4))
    ax.plot([0,100],[90.8,90.8],color=ACCENT,lw=2,zorder=5)
    ax.text(50,95.5,title,color=ACCENT,fontsize=17,ha="center",va="center",fontweight="bold",zorder=6)
    if sub: ax.text(50,92,sub,color=GOLD,fontsize=10,ha="center",va="center",zorder=6)

def footer(ax):
    ax.add_patch(mpatches.Rectangle((0,0),100,3,color=PANEL,zorder=4))
    ax.text(50,1.3,"Elliott Wave & MACD Divergences — Complete Trading Course",
            color=MGRAY,fontsize=7,ha="center",va="center",zorder=5)

def savefig(fig, name):
    path = os.path.join(FRAMES_DIR, name)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0,
                facecolor=BG, edgecolor="none")
    plt.close(fig)
    return path

def slide(img_path, audio_obj, duration, crossfade=0.5):
    """Return an ImageClip of given duration with audio."""
    c = ImageClip(img_path).set_duration(duration)
    if audio_obj is not None:
        adur = min(duration, audio_obj.duration)
        c = c.set_audio(audio_obj.subclip(0, adur))
    return c
