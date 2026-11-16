#!/usr/bin/env python3
"""Bake the Chichi clips into compact frame data, so the page does not need the videos.

Usage:  python3 tools/bake.py <directory with dark-*.mp4>

Each cell of each frame becomes one byte:
  0..GRAY-1      gray level (fur, eyes, background, laptop)
  GRAY..2*GRAY-1 brightness level of the headset blue
A frame is stored as the difference from the frame before it, then the clip is gzipped.
Output: assets/<clip>.bin (gzip data) for each clip and assets/clips.json with the shared metadata.
Needs ffmpeg and numpy.
"""
import gzip
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

W, H = 240, 144          # cells; 240 / 144 matches a 0.6-wide monospace glyph on a square clip
FPS = 24
GRAY = 64                # levels per class
HOLD = 1                 # a cell keeps its old level unless it changes by more than this
CLIPS = ['standby', 'look-around', 'heychichi', 'yeeees', 'listening', 'typing']

src = Path(sys.argv[1])
out = Path(__file__).resolve().parent.parent / 'assets'
out.mkdir(exist_ok=True)

meta = {'width': W, 'height': H, 'fps': FPS, 'levels': GRAY, 'clips': {}}
blue_sum, blue_n = np.zeros(3), 0
white_sum, white_n = np.zeros(3), 0
total = 0
for name in CLIPS:
    raw = subprocess.run(
        ['ffmpeg', '-loglevel', 'error', '-i', str(src / f'dark-{name}.mp4'),
         '-vf', f'scale={W}:{H}:flags=area', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'],
        check=True, capture_output=True).stdout
    rgb = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.float32)
    hi, lo = rgb.max(-1), rgb.min(-1)
    blue = ((hi - lo) / np.maximum(hi, 1) > 0.35) & (rgb[..., 2] > rgb[..., 0]) & (hi > 40)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    level = np.where(blue, hi, lum) / 255 * (GRAY - 1)
    code = np.rint(level).astype(np.int16) + np.where(blue, GRAY, 0)

    # average headset color at full brightness, for the page to rebuild the blue
    px = rgb[blue]
    blue_sum += (px / px.max(-1, keepdims=True)).sum(0)
    blue_n += len(px)
    px = rgb[~blue & (lum > 150)]                 # the same for the fur tint
    white_sum += (px / px.max(-1, keepdims=True)).sum(0)
    white_n += len(px)

    # Hold a cell when it changes by one level only: video noise would cost space and flicker.
    held = code.copy()
    for f in range(1, len(held)):
        keep = (np.abs(held[f] - held[f - 1]) <= HOLD) & ((held[f] >= GRAY) == (held[f - 1] >= GRAY))
        held[f][keep] = held[f - 1][keep]
    frames = held.astype(np.uint8)
    delta = frames.copy()
    delta[1:] = frames[1:] - frames[:-1]          # wraps modulo 256; the page adds it back
    data = gzip.compress(delta.tobytes(), 9, mtime=0)
    (out / f'{name}.bin').write_bytes(data)
    meta['clips'][name] = len(frames)
    total += len(data)
    print(f'{name:12} {len(frames):4} frames  {len(data) / 1024:7.1f} KB')

meta['blue'] = [round(float(c), 3) for c in blue_sum / blue_n]
meta['white'] = [round(float(c), 3) for c in white_sum / white_n]
(out / 'clips.json').write_text(json.dumps(meta) + '\n')
print(f'total {total / 1024:.1f} KB, blue {meta["blue"]}, white {meta["white"]}')
