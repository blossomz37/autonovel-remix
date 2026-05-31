#!/usr/bin/env python3
"""
Build a condensed arc summary for full-novel evaluation.
For each chapter: first 150 words, last 150 words, plus any dialogue.
Gives the reader panel enough to evaluate the ARC without 72k tokens.
"""
import os
import sys
import re
import tomllib
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")
CHAPTERS_DIR = BASE_DIR / "chapters"

with open(BASE_DIR / "config" / "build_arc_summary.toml", "rb") as f:
    CONFIG = tomllib.load(f)

def call_writer(prompt, max_tokens=None, temperature=None):
    if max_tokens is None: max_tokens = CONFIG["model"]["max_tokens"]
    if temperature is None: temperature = CONFIG["model"]["temperature"]
    import anthropic
    client = anthropic.Anthropic(api_key=API_KEY, base_url=API_BASE)
    msg = client.messages.create(
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=CONFIG["prompts"]["system"].strip(),
        messages=[{"role": "user", "content": prompt}],
        timeout=300,
    )
    return msg.content[0].text

def extract_key_passages(text):
    """Get opening, closing, and best dialogue from a chapter."""
    words = text.split()
    opening = ' '.join(words[:150])
    closing = ' '.join(words[-150:])
    
    # Extract dialogue lines
    dialogue = re.findall(r'["""]([^"""]{20,})["""]', text)
    # Pick up to 3 longest dialogue lines
    dialogue.sort(key=len, reverse=True)
    top_dialogue = dialogue[:3]
    
    return opening, closing, top_dialogue

def main():
    summaries = []
    
    for ch in range(1, 20):
        path = CHAPTERS_DIR / f"ch_{ch:02d}.md"
        text = path.read_text()
        wc = len(text.split())
        opening, closing, dialogue = extract_key_passages(text)
        
        # Get a 100-word summary from the model
        prompt = CONFIG["prompts"]["user"].format(ch=ch, text=text)
        summary = call_writer(prompt, max_tokens=200)
        
        entry = f"""### Chapter {ch} ({wc} words)
**Summary:** {summary}

**Opening:** {opening}...

**Closing:** ...{closing}

**Key dialogue:**
"""
        for d in dialogue:
            entry += f'> "{d}"\n\n'
        
        summaries.append(entry)
        print(f"Ch {ch}: summarized ({wc}w)")
    
    # Calculate total word count
    total_wc = sum(len((CHAPTERS_DIR / f"ch_{c:02d}.md").read_text().split()) for c in range(1, 20))
    
    # Assemble
    full = f"""# THE SECOND SON OF THE HOUSE OF BELLS
## Full-Arc Summary for Reader Panel

This document contains chapter summaries, opening/closing passages,
and key dialogue for all 23 chapters. Total novel: {total_wc:,} words.

PREMISE: In Cantamura, a city where law is sung into binding through
specific musical intervals, 14-year-old Cass Bellwright can hear when
someone is lying -- a quarter-tone between F and F-sharp that causes
him physical pain. His older brother Perin has been bound to service
in the House of Corda for 10 years through a contract their father
allowed. The bells their family maintains contain a secret: a question
("Do you consent to be bound?") embedded in the sub-harmonics by the
city's founder 200 years ago. No one has ever heard it. No one has
ever answered. Every binding in Cantamura is technically void.

---

"""
    full += '\n---\n\n'.join(summaries)
    
    out_path = BASE_DIR / "arc_summary.md"
    out_path.write_text(full)
    print(f"\nSaved to {out_path} ({len(full.split())} words)")

if __name__ == "__main__":
    main()
