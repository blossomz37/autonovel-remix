#!/usr/bin/env python3
"""
Revision chapter generator. Rewrites a chapter from a specific revision brief.
Usage: python gen_revision.py <chapter_num> <brief_file>
"""
import os
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

with open(BASE_DIR / "config" / "gen_revision.toml", "rb") as f:
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

def main():
    ch_num = int(sys.argv[1])
    brief_file = sys.argv[2]
    
    voice = (PROJECT_DIR / "lore" / "voice.md").read_text()
    characters = (PROJECT_DIR / "lore" / "characters.md").read_text()
    world = (PROJECT_DIR / "lore" / "world.md").read_text()
    brief = Path(brief_file).read_text()
    
    # Load adjacent chapters for continuity
    prev_path = PROJECT_DIR / "chapters" / f"ch_{ch_num - 1:02d}.md"
    next_path = PROJECT_DIR / "chapters" / f"ch_{ch_num + 1:02d}.md"
    prev_tail = prev_path.read_text()[-2000:] if prev_path.exists() else "(first chapter)"
    next_head = next_path.read_text()[:1500] if next_path.exists() else "(last chapter)"
    
    # Load old version if exists
    old_path = PROJECT_DIR / "chapters" / f"ch_{ch_num:02d}.md"
    old_text = old_path.read_text() if old_path.exists() else "(no existing draft)"
    
    prompt = CONFIG["prompts"]["user"].format(
        ch_num=ch_num,
        brief=brief,
        voice=voice,
        characters=characters,
        world=world,
        prev_tail=prev_tail,
        next_head=next_head,
        old_text=old_text
    )

    print(f"Rewriting Chapter {ch_num}...", file=sys.stderr)
    result = call_writer(prompt)
    
    out_path = PROJECT_DIR / "chapters" / f"ch_{ch_num:02d}.md"
    out_path.write_text(result)
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)

if __name__ == "__main__":
    main()
