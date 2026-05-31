#!/usr/bin/env python3
"""Generate outline.md from seed + world + characters + mystery + craft."""
import os
import sys
import tomllib
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")

with open(BASE_DIR / "config" / "gen_outline.toml", "rb") as f:
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

seed = (BASE_DIR / "lore" / "seed.txt").read_text()
world = (BASE_DIR / "lore" / "world.md").read_text()
characters = (BASE_DIR / "lore" / "characters.md").read_text()
mystery = (BASE_DIR / "lore" / "MYSTERY.md").read_text()
craft = (BASE_DIR / "framework" / "CRAFT.md").read_text()

# Voice Part 2 only
voice = (BASE_DIR / "lore" / "voice.md").read_text()
voice_lines = voice.split('\n')
part2_start = next(i for i, l in enumerate(voice_lines) if 'Part 2' in l)
voice_part2 = '\n'.join(voice_lines[part2_start:])

prompt = CONFIG["prompts"]["user"].format(
    seed=seed, mystery=mystery, world=world, characters=characters, voice_part2=voice_part2, craft=craft
)

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
print(result)
