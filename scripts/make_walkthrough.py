"""Assemble the captured frames into the captioned MP4 walkthrough at the repository root.

Optional deliverable tooling, not part of the gate: it needs `pillow` and `imageio-ffmpeg`, and the
Windows Arial paths below. Run `scripts/capture_walkthrough.py` first, then:

    python scripts/make_walkthrough.py

Every frame carries a step chip and a caption band that explains what is on screen. The file is
silent, so the captions are the narration and can be read aloud later without re-rendering.
"""
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from imageio_ffmpeg import get_ffmpeg_exe

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "scratch" / "walkthrough"
COMP = BASE / "composed"
OUT_MP4 = ROOT / "DramAdapt_QA_walkthrough.mp4"
W, SHOT_H, BAND = 1500, 950, 170
H = SHOT_H + BAND
ACCENT = (15, 76, 92)
ACCENT_LT = (126, 190, 205)
INK = (24, 32, 38)
WHITE = (252, 253, 253)
MUTED = (188, 202, 208)

STEPS = {
    "01_title": ("The claim on one line",
                 "The page opens with the whole claim: this is quality assurance, not translation. "
                 "Nothing here is auto-approved, and no number on it is a confidence score about Telugu."),
    "02_five_checks": ("What this page does",
                       "Five checks read every English and Telugu line pair. Meaning, relationship and "
                       "naturalness ask a model. Timing and script form are counted from the text, so they "
                       "cost no calls and never change their mind between runs."),
    "03_why_telugu": ("Why Telugu",
                      "Why this language: the ground truth is 100 lines I graded by hand, 81 of them marked "
                      "as needing work, and 83 rewritten in my own Telugu. One evaluator, one language, and "
                      "no inter-rater agreement claimed."),
    "04_not_hindi": ("Why not Hindi",
                     "Why not Hindi: the evaluator constraint picks the language, not the linguistics. A "
                     "Hindi version would need a Hindi evaluator, and then the verdicts on this sheet would "
                     "not be mine."),
    "05_summary": ("Summary numbers",
                   "The run in four numbers: 100 lines, all 100 carrying Telugu, 91 lines with at least one "
                   "flag, and 73 model requests for a whole season. The blue boxes are the free checks, the "
                   "yellow box is a coverage gap, not a clean pass."),
    "06_howto": ("How to read them",
                 "This panel is the honest part: which numbers are counted, which are asked of a model, and "
                 "which still rest on an assumed speaking rate that nobody has hand-timed yet."),
    "07_card": ("One flag",
                "One flag, top to bottom: the line id and speaker, which check raised it, its severity and "
                "verdict, the English line, the Telugu line with its time slot in seconds, the evidence, and "
                "the correction offered."),
    "08_action": ("The editor action",
                  "Every flag carries an editor action: pending, approved, edited or dismissed. The choice "
                  "is written to disk with a timestamp, so the review itself becomes evidence later."),
    "09_relationship": ("Register check",
                        "A register flag. Telugu marks who is speaking to whom in the pronoun and the verb "
                        "ending, so the wrong form of address is a real defect, not a style note."),
    "10_script": ("Script check",
                  "A script flag: this line came back as Telugu typed in Latin letters. A language model can "
                  "read it. A voice artist in the booth cannot, and the timing check cannot measure it."),
    "11_timing": ("Timing check",
                  "A timing flag: the line is estimated to need more seconds than its slot allows. Reported "
                  "as risk rather than failure, because dubbing can trim or retime a line."),
    "12_sheet": ("Relationship sheet",
                 "The relationship sheet: who calls whom what, in each episode. The model pre-fills it, the "
                 "editor confirms it, and the register check reads that instead of guessing line by line."),
    "13_sidebar": ("Sidebar inputs",
                   "The sidebar holds the two inputs: which stored run to show, and which Telugu draft file "
                   "to read. Point it at a new draft and the same checks run again."),
    "14_run": ("Run checks now",
               "Run checks now: the five checks against a new script, with your own key. This tour never "
               "pressed it, so no model calls were spent making this video."),
    "15_export": ("Export",
                  "Export: the decisions leave as JSON or CSV, with timestamps. A hosted demo has a "
                  "read-only filesystem, so the panel says that plainly instead of failing."),
}


def font(size, bold=False):
    path = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def frame(img, step_no, total, title, caption, sub=0):
    canvas = Image.new("RGB", (W, H), INK)
    canvas.paste(img.resize((W, SHOT_H)), (0, 0))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    label = f"Step {step_no:02d}/{total:02d}  -  {title}" + ("" if sub == 0 else f"  (cont.)")
    tw = d.textlength(label, font=font(26, True))
    d.rounded_rectangle([16, 16, 16 + tw + 34, 66], radius=10, fill=(15, 76, 92, 235))
    d.text((33, 26), label, font=font(26, True), fill=WHITE)

    d.rectangle([0, SHOT_H, W, H], fill=ACCENT)
    d.line([0, SHOT_H, W, SHOT_H], fill=(90, 150, 166, 255), width=3)
    y = SHOT_H + 14
    for line in wrap(d, caption, font(28), W - 70)[:4]:
        d.text((34, y), line, font=font(28), fill=WHITE)
        y += 34
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    return canvas


def card(lines, footer=""):
    canvas = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, 12, H], fill=ACCENT)
    y = 110
    for text, size, colour, bold in lines:
        for line in wrap(d, text, font(size, bold), W - 200):
            d.text((100, y), line, font=font(size, bold), fill=colour)
            y += int(size * 1.38)
        y += 20
    if footer:
        d.text((100, H - 130), footer, font=font(26), fill=MUTED)
    return canvas


def main() -> None:
    os.makedirs(COMP, exist_ok=True)
    manifest = json.load(open(f"{BASE}/manifest.json", encoding="utf-8"))
    order = []
    for m in manifest:
        if m["scene"] not in order:
            order.append(m["scene"])
    total = len(order)
    seq = []

    title = card([
        ("DramAdapt QA", 88, WHITE, True),
        ("A pre-dubbing quality gate for English to Telugu microdrama.", 42, MUTED, False),
        ("It reads the English line and the machine-made Telugu line and tells an editor which lines are "
         "not ready for the booth. It does not translate, dub or lip-sync.", 32, WHITE, False),
        ("Captured from the live prototype, step by step, with the captions on screen.", 30, MUTED, False),
    ], "https://dramadapt-app.streamlit.app/")
    title.save(f"{COMP}/000_title.png")
    seq.append(("000_title.png", 6.0))

    for i, scene in enumerate(order, start=1):
        ttl, cap = STEPS[scene]
        for j, m in enumerate([x for x in manifest if x["scene"] == scene]):
            out = f"{i:02d}_{scene}_{j}.png"
            frame(Image.open(m["png"]).convert("RGB"), i, total, ttl, cap, j).save(f"{COMP}/{out}")
            seq.append((out, 6.5 if j == 0 else 3.0))

    end = card([
        ("What is still open", 62, WHITE, True),
        ("Reviewer acceptance pass: 34 of 174 flags graded.", 34, MUTED, False),
        ("Speaking rate: assumed at 3.5 akshara/s, one derived alternative at 5.83, no hand timing yet.",
         34, MUTED, False),
        ("Step E, seeded errors: never run.", 34, MUTED, False),
        ("The gate scored itself against a rule written before the run and returned NO-GO. That verdict is "
         "on the page, not hidden in a folder.", 32, WHITE, False),
    ], "github.com/tharun99856/dramadapt-qa")
    end.save(f"{COMP}/900_end.png")
    seq.append(("900_end.png", 8.0))

    lst = f"{BASE}/concat.txt"
    with open(lst, "w", encoding="utf-8") as fh:
        for name, dur in seq:
            fh.write(f"file '{os.path.abspath(os.path.join(COMP, name))}'\nduration {dur}\n")
        fh.write(f"file '{os.path.abspath(os.path.join(COMP, seq[-1][0]))}'\n")

    out_mp4 = str(OUT_MP4)
    subprocess.run([get_ffmpeg_exe(), "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-vf", "fps=30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "23",
                    "-movflags", "+faststart", out_mp4], check=True, capture_output=True)
    print(f"wrote {out_mp4}: {len(seq)} stills, ~{sum(d for _, d in seq):.0f}s, "
          f"{os.path.getsize(out_mp4) / 1e6:.1f} MB")


main()
