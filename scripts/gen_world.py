#!/usr/bin/env python3
"""
One-shot world.md generator for foundation phase.
Reads seed.txt + voice.md, calls the writer model, outputs world.md content.
"""
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

with open(BASE_DIR / "config" / "gen_world.toml", "rb") as f:
    CONFIG = tomllib.load(f)

def call_writer(prompt, max_tokens=None, temperature=None):
    if max_tokens is None: max_tokens = CONFIG["model"]["max_tokens"]
    if temperature is None: temperature = CONFIG["model"]["temperature"]
    import httpx
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": CONFIG["prompts"]["system"].strip(),
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = httpx.post(f"{API_BASE}/v1/messages", headers=headers, json=payload, timeout=300)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"API Error: {resp.text}", file=sys.stderr)
        raise e
    return resp.json()["content"][0]["text"]

seed = (BASE_DIR / "lore" / "seed.txt").read_text()
voice = (BASE_DIR / "lore" / "voice.md").read_text()
craft = (BASE_DIR / "framework" / "CRAFT.md").read_text()

# Extract voice Part 2 only (the novel-specific voice)
voice_lines = voice.split('\n')
part2_start = next(i for i, l in enumerate(voice_lines) if 'Part 2' in l)
voice_part2 = '\n'.join(voice_lines[part2_start:])

prompt = CONFIG["prompts"]["user"].format(seed=seed, voice_part2=voice_part2)

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
print(result)
