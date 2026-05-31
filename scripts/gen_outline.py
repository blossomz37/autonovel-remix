#!/usr/bin/env python3
"""Generate outline.md from seed + world + characters + mystery + craft."""
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

with open(BASE_DIR / "config" / "gen_outline.toml", "rb") as f:
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

seed = (PROJECT_DIR / "lore" / "seed.txt").read_text()
world = (PROJECT_DIR / "lore" / "world.md").read_text()
characters = (PROJECT_DIR / "lore" / "characters.md").read_text()
mystery = (PROJECT_DIR / "lore" / "MYSTERY.md").read_text()
craft = (BASE_DIR / "framework" / "CRAFT.md").read_text()

# Voice Part 2 only
voice = (PROJECT_DIR / "lore" / "voice.md").read_text()
voice_lines = voice.split('\n')
part2_start = next(i for i, l in enumerate(voice_lines) if 'Part 2' in l)
voice_part2 = '\n'.join(voice_lines[part2_start:])

prompt = CONFIG["prompts"]["user"].format(
    seed=seed, mystery=mystery, world=world, characters=characters, voice_part2=voice_part2, craft=craft
)

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
