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

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://openrouter.ai/api/v1")

with open(BASE_DIR / "config" / "gen_revision.toml", "rb") as f:
    CONFIG = tomllib.load(f)

def call_writer(prompt, max_tokens=None, temperature=None):
    if max_tokens is None: max_tokens = CONFIG["model"]["max_tokens"]
    if temperature is None: temperature = CONFIG["model"]["temperature"]
    import openai
    
    extra_body = {}
    if os.environ.get("OPENROUTER_REASONING_EFFORT"):
        extra_body["reasoning"] = {
                "effort": os.environ.get("OPENROUTER_REASONING_EFFORT", "none"),
                "exclude": os.environ.get("OPENROUTER_REASONING_EXCLUDE", "true").lower() == "true",
                "enabled": os.environ.get("OPENROUTER_REASONING_ENABLED", "false").lower() == "true"
        }
    if os.environ.get("OPENROUTER_VERBOSITY"):
        extra_body["verbosity"] = os.environ.get("OPENROUTER_VERBOSITY", "low")

    client = openai.OpenAI(api_key=API_KEY, base_url=API_BASE)
    msg = client.chat.completions.create(
        model=WRITER_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": CONFIG["prompts"]["system"].strip()},
            {"role": "user", "content": prompt}
        ],
        timeout=300,
        extra_body=extra_body,
        stream=True
    )
    
    full_text = ""
    for chunk in msg:
        if chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            sys.stdout.write(text)
            sys.stdout.flush()
            full_text += text
    sys.stdout.write("\n")
    return full_text

def main():
    ch_num = int(sys.argv[1])
    brief_file = sys.argv[2]
    
    voice = (BASE_DIR / "lore" / "voice.md").read_text()
    characters = (BASE_DIR / "lore" / "characters.md").read_text()
    world = (BASE_DIR / "lore" / "world.md").read_text()
    brief = Path(brief_file).read_text()
    
    # Load adjacent chapters for continuity
    prev_path = BASE_DIR / "chapters" / f"ch_{ch_num - 1:02d}.md"
    next_path = BASE_DIR / "chapters" / f"ch_{ch_num + 1:02d}.md"
    prev_tail = prev_path.read_text()[-2000:] if prev_path.exists() else "(first chapter)"
    next_head = next_path.read_text()[:1500] if next_path.exists() else "(last chapter)"
    
    # Load old version if exists
    old_path = BASE_DIR / "chapters" / f"ch_{ch_num:02d}.md"
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
    
    out_path = BASE_DIR / "chapters" / f"ch_{ch_num:02d}.md"
    out_path.write_text(result)
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)

if __name__ == "__main__":
    main()
