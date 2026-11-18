# ascii-chichi

Chichi, the symbol character of [agent-chichi.ai](https://agent-chichi.ai/), drawn as live ASCII art in the browser. The head follows the pointer, and a click makes Chichi swat at the click point.

https://github.com/user-attachments/assets/524553e9-d501-4062-a99e-273241003157

One HTML file, no dependencies, no build step.

Live page: <https://ascii-chichi.vercel.app/>

## Run

The page loads its clip data with `fetch`, so it needs a web server. Opening `index.html` from the file system does not work.

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000/>.

It needs a browser with `DecompressionStream`: Chrome 80, Safari 16.4, Firefox 113, or newer.

## Controls

| Input | Result |
|---|---|
| Move the pointer | The head turns toward the pointer. The body stays still. |
| Click or tap | A burst appears at the point, Chichi swats at it, and the "hey chichi" clip plays. |
| Type | The laptop clip plays while keys are pressed. |
| `1` to `6` | Plays a clip directly: standby, look-around, heychichi, yeeees, listening, typing. |
| No input for 10 s | Chichi looks around or listens. |

Visitors who ask for reduced motion get no burst and no swat.

## How it works

Every frame goes through the same steps:

1. **Clip frame.** The active clip gives one frame of 240 × 144 cells. The frame is scaled to the character grid: one pixel per character.
2. **Paw swat.** After a click, one front leg is drawn into that small image: a curved, tapered leg from the shoulder to the paw. The body leans with it.
3. **Head turn.** The face region slides over a dome: most in the middle, nothing at the rim. The face turns and the silhouette holds.
4. **Glyphs.** Each pixel becomes one character from the ramp `' .,:;-=+*#%@'`, in the color of the pixel.

The leg is drawn before the glyph step. It gets the same shading as the clip, so it reads as the same fur.

On load, the figure fills in from its bottom row to its top row behind a band of random glyphs.

## Clip data

The clips are not video files. `tools/bake.py` converts the rendered source videos into compact frame data:

- One byte per cell: 64 gray levels, then 64 brightness levels of the headset blue.
- Each frame is stored as the difference from the frame before it.
- Each clip is one gzip file: `assets/<clip>.bin`.
- `assets/clips.json` holds the grid size, the frame rate, the frame counts, and the two base colors.

The six clips take about 530 KB in total. The source videos are not part of this repository.

To bake again, put the source videos (`dark-<clip>.mp4`) in a directory and run:

```sh
python3 tools/bake.py <directory with the videos>
```

This needs `ffmpeg` and `numpy`.

## Tuning

All settings are constants near the top of the script in `index.html`.

| Constant | Meaning |
|---|---|
| `CELL` | Character height in CSS pixels. |
| `SIDE` | Extra grid width on each side of the clip, so a paw is not cut off. |
| `HEAD` | Face region and turn strength. Keep `yaw` and `pitch` below 0.5. |
| `STIFFNESS`, `DAMPING` | Spring that moves the head toward the pointer. |
| `PAWS` | Shoulder and resting paw position of each front leg. |
| `SWAT_MS`, `SWAT_REACH` | Length of the swat and how far the paw reaches. |
| `ARM_R`, `PAW_R` | Leg and paw thickness. |
| `LEAN_X`, `LEAN_Y` | How far the body moves with the swat. |
| `BURST_MS`, `BURST_R`, `SPARKS` | Click burst. |
| `REVEAL_MS`, `BAND` | Load reveal. |

## Files

```
index.html       the page: markup, styles, and script
assets/          baked clip data
tools/bake.py    converts source videos to clip data
```
