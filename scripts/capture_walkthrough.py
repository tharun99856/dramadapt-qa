"""Capture a guided tour of the hosted app as PNG frames plus a caption manifest.

Optional deliverable tooling, not part of the gate: it needs `selenium`, a local Chrome, and the
paths below. Nothing here clicks a button, so no model call is spent and no editor decision is
written. Frames land in the git-ignored scratch tree; `scripts/make_walkthrough.py` turns them into
the committed MP4.

    python scripts/capture_walkthrough.py
"""
import json
import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "scratch" / "walkthrough" / "raw"
MANIFEST = ROOT / "scratch" / "walkthrough" / "manifest.json"
URL = "https://dramadapt-app.streamlit.app/"
STEP = 300

# scene, finder, argument, extra scroll steps, caption
SCENES = [
    ("01_title", "top", None, 2,
     "DramAdapt QA. A quality gate for an English to Telugu microdrama draft, before the dubbing booth."),
    ("02_five_checks", "strong", "What this page does", 3,
     "Five checks read every line pair. Three ask a model. Timing and script form are counted from the text."),
    ("03_why_telugu", "strong", "Because Telugu is my native language", 2,
     "Why Telugu: the ground truth is 100 lines the author graded by hand and 83 rewrote."),
    ("04_not_hindi", "strong", "Why Telugu and not Hindi", 1,
     "Why not Hindi: the evaluator constraint picks the language, not the linguistics."),
    ("05_summary", "heading", "Summary", 1,
     "The run: 100 lines, 91 with at least one flag, 73 model requests for a whole season."),
    ("06_howto", "open", "How to read the numbers above", 2,
     "How to read the numbers: which are counted, which are asked, which are still assumptions."),
    ("07_card", "card", "meaning", 3,
     "One flag: the English line, the Telugu line, its time slot, the evidence, the fix offered."),
    ("08_action", "radio_first", None, 2,
     "The editor answers each flag: pending, approved, edited or dismissed. Nothing is auto-approved."),
    ("09_relationship", "card", "relationship", 2,
     "A register flag: the form of address is wrong between these two characters."),
    ("10_script", "verdict", "not_in_telugu_script", 2,
     "A script flag: Telugu typed in Latin letters. A voice artist cannot read that aloud."),
    ("11_timing", "card", "timing", 2,
     "A timing flag: this line needs more seconds than its slot. Reported as risk, not failure."),
    ("12_sheet", "open", "Relationship and address sheet", 2,
     "The relationship sheet: who calls whom what, confirmed by the editor once, then applied per line."),
    ("13_sidebar", "sidebar", None, 2,
     "The sidebar: pick a stored run, or point the same checks at a different Telugu draft."),
    ("14_run", "open", "Run checks now", 2,
     "Or run the five checks here on any new draft, against your own key and your own budget."),
    ("15_export", "open", "Export", 2,
     "Export: the editor's decisions leave as JSON or CSV, with timestamps, so the review is auditable."),
]

FIND_JS = {
    "top": "(n)=>{const h=document.querySelector('h1'); if(!h)return null; return h;}",
    "heading": "(n)=>{const h=Array.from(document.querySelectorAll('h1,h2,h3,h4')).find(e=>e.textContent.includes(n));"
               "if(!h)return null; return h;}",
    "text": "(n)=>{const el=Array.from(document.querySelectorAll('[data-testid=stMarkdownContainer]'))"
            ".find(e=>e.textContent.includes(n)); if(!el)return null; return el;}",
    "strong": "(n)=>{const el=Array.from(document.querySelectorAll('strong'))"
              ".find(e=>e.textContent.includes(n)); if(!el)return null; return el;}",
    "card": "(n)=>{const el=Array.from(document.querySelectorAll('[data-testid=stMarkdownContainer]'))"
            ".find(e=>{const t=e.textContent.trim(); return t==='check: '+n;});"
            "if(!el)return null; return el;}",
    "verdict": "(n)=>{const el=Array.from(document.querySelectorAll('[data-testid=stMarkdownContainer]'))"
              ".find(e=>e.textContent.trim()==='verdict: '+n); if(!el)return null; return el;}",
    "radio_first": "(n)=>{const r=document.querySelector('[data-testid=stRadio]'); if(!r)return null; return r;}",
    "sidebar": "(n)=>{const s=document.querySelector('[data-testid=stSidebar]'); if(!s)return null; return s;}",
}


def main() -> None:
    os.makedirs(RAW, exist_ok=True)
    opts = Options()
    opts.binary_location = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    for flag in ("--headless=new", "--window-size=1500,950", "--hide-scrollbars",
                 "--force-device-scale-factor=1", "--disable-gpu", "--no-first-run"):
        opts.add_argument(flag)
    driver = webdriver.Chrome(options=opts)
    manifest = []
    try:
        driver.get(URL)
        time.sleep(28)
        frame = [f for f in driver.find_elements("tag name", "iframe")
                 if "statuspage" not in str(f.get_attribute("src"))][0]
        driver.switch_to.frame(frame)
        for _ in range(40):
            if driver.execute_script("return document.body.innerText.includes('pre-dubbing')"):
                break
            time.sleep(1.5)
        for name, kind, arg, steps, caption in SCENES:
            if kind in ("open", "open_in_sidebar"):
                opened = open_expander(driver, kind, arg)
                anchor = open_expander_anchor(driver, kind, arg)
            else:
                opened = None
                anchor = driver.execute_script(
                    f"const f = {FIND_JS[kind]}; return f(arguments[0]);", arg or "")
            if anchor is None:
                print(f"{name:16s} MISS {kind} {arg}")
                continue
            for k in range(steps):
                where = driver.execute_script(
                    "const a=arguments[0], off=arguments[1];"
                    "const m=document.querySelector('[data-testid=stMain]')||document.scrollingElement;"
                    "if(!(a instanceof Node)) return 'no-anchor';"
                    "const r=a.getBoundingClientRect(), mr=m.getBoundingClientRect();"
                    "m.scrollTop=Math.max(0, m.scrollTop + r.top - mr.top - 110 + off);"
                    "const side=document.querySelector('[data-testid=stSidebar]');"
                    "if(side && side.scrollHeight>side.clientHeight){"
                    "  const s=a.getBoundingClientRect(), sr=side.getBoundingClientRect();"
                    "  side.scrollTop=Math.max(0, side.scrollTop + s.top - sr.top - 90 + off);}"
                    "const after=a.getBoundingClientRect();"
                    "return 'in:'+(after.top>=-4 && after.bottom<=window.innerHeight"
                    "? 'yes':'no')+' scrollTop='+Math.round(m.scrollTop)+' text='+"
                    "(a.textContent||'').trim().slice(0,40);", anchor, k * STEP)
                time.sleep(0.9)
                driver.switch_to.default_content()
                path = f"{RAW}/{name}_{k}.png"
                driver.save_screenshot(path)
                driver.switch_to.frame(frame)
                manifest.append({"scene": name, "frame": k, "frames": steps,
                                 "caption": caption, "png": path, "opened": opened, "where": where})
                print(f"  {name}_{k}: {str(where)[:96]}")
            print(f"{name:16s} ok   {steps} frames  {str(opened or '')[:52]}")
        print("frames:", len(manifest))
    finally:
        with open(MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=1)
        driver.quit()


def open_expander(driver, kind, needle):
    scope = "document.querySelector('[data-testid=stSidebar]')||document" if kind == "open_in_sidebar" else "document"
    return driver.execute_script(
        "const n=arguments[0];"
        f"const s=Array.from({scope}.querySelectorAll('summary')).find(e=>e.textContent.includes(n));"
        "if(!s) return null; if(s.getAttribute('aria-expanded')!=='true') s.click();"
        "return s.textContent.replace('keyboard_arrow_down','').replace('keyboard_arrow_right','').slice(0,50);",
        needle)


def open_expander_anchor(driver, kind, needle):
    scope = "document.querySelector('[data-testid=stSidebar]')||document" if kind == "open_in_sidebar" else "document"
    return driver.execute_script(
        "const n=arguments[0];"
        f"const s=Array.from({scope}.querySelectorAll('summary')).find(e=>e.textContent.includes(n));"
        "if(!s) return null; return s.parentElement;", needle)


main()
