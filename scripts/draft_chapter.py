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

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")
CHAPTERS_DIR = BASE_DIR / "chapters"

with open(BASE_DIR / "config" / "draft_chapter.toml", "rb") as f:
    CONFIG = tomllib.load(f)

def call_writer(prompt, max_tokens=None, temperature=None):
    if max_tokens is None: max_tokens = CONFIG["model"]["max_tokens"]
    if temperature is None: temperature = CONFIG["model"]["temperature"]
    import httpx
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "context-1m-2025-08-07",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": CONFIG["prompts"]["system"].strip(),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=600)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]

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
    voice = load_file(BASE_DIR / "lore" / "voice.md")
    world = load_file(BASE_DIR / "lore" / "world.md")
    characters = load_file(BASE_DIR / "lore" / "characters.md")
    outline = load_file(BASE_DIR / "lore" / "outline.md")
    canon = load_file(BASE_DIR / "lore" / "canon.md")
    
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
    print(result)

if __name__ == "__main__":
    main()
