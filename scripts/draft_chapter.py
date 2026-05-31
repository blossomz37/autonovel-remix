#!/usr/bin/env python3
"""
Draft a single chapter using the writer model.
Usage: python draft_chapter.py 1
"""
import os
import re
import sys
import tomllib
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")
PROJECT_DIR = BASE_DIR / "workspace"

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://openrouter.ai/api/v1")
CHAPTERS_DIR = PROJECT_DIR / "chapters"

with open(BASE_DIR / "config" / "draft_chapter.toml", "rb") as f:
    CONFIG = tomllib.load(f)

def call_writer(prompt, max_tokens=None, temperature=None):
    if max_tokens is None: max_tokens = CONFIG.get("model", {}).get("max_tokens", 4000)
    if temperature is None: temperature = CONFIG.get("model", {}).get("temperature", 0.7)
    from api_client import call_llm
    from pathlib import Path
    return call_llm(
        messages=[
            {"role": "system", "content": CONFIG["prompts"]["system"].strip()},
            {"role": "user", "content": prompt}
        ],
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        script_name=Path(__file__).name
    )

def load_file(path):
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return ""

def extract_chapter_outline(outline_text, chapter_num):
    """Extract a specific chapter's outline entry."""
    pattern = rf'### Ch {chapter_num}:.*?(?=### Ch {chapter_num + 1}:|## Foreshadowing|$)'
    match = re.search(pattern, outline_text, re.DOTALL)
    return match.group(0).strip() if match else "(not found)"

def extract_next_chapter_outline(outline_text, chapter_num):
    """Extract the next chapter's outline (just first few lines for continuity)."""
    next_entry = extract_chapter_outline(outline_text, chapter_num + 1)
    if next_entry == "(not found)":
        return "(final chapter)"
    lines = next_entry.split('\n')[:10]
    return '\n'.join(lines)

def main():
    chapter_num = int(sys.argv[1])
    
    # Load all context
    voice = load_file(PROJECT_DIR / "lore" / "voice.md")
    world = load_file(PROJECT_DIR / "lore" / "world.md")
    characters = load_file(PROJECT_DIR / "lore" / "characters.md")
    outline = load_file(PROJECT_DIR / "lore" / "outline.md")
    canon = load_file(PROJECT_DIR / "lore" / "canon.md")
    
    # Chapter-specific context
    chapter_outline = extract_chapter_outline(outline, chapter_num)
    next_chapter = extract_next_chapter_outline(outline, chapter_num)
    
    # Previous chapter (if exists)
    prev_path = CHAPTERS_DIR / f"ch_{chapter_num - 1:02d}.md"
    if prev_path.exists():
        prev_text = prev_path.read_text()
        prev_tail = prev_text[-2000:] if len(prev_text) > 2000 else prev_text
    else:
        prev_tail = "(first chapter -- no previous)"
    
    prompt = CONFIG["prompts"]["user"].format(
        chapter_num=chapter_num,
        voice=voice,
        chapter_outline=chapter_outline,
        next_chapter=next_chapter,
        prev_tail=prev_tail,
        world=world,
        characters=characters
    )

    print(f"Drafting Chapter {chapter_num}...", file=sys.stderr)
    result = call_writer(prompt)
    
    # Save
    out_path = CHAPTERS_DIR / f"ch_{chapter_num:02d}.md"
    out_path.write_text(result)
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)

if __name__ == "__main__":
    main()
