#!/usr/bin/env python3
"""Generate remaining chapters + foreshadowing ledger."""
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

with open(BASE_DIR / "config" / "gen_outline_part2.toml", "rb") as f:
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

part1 = open('/tmp/outline_output.md').read()
mystery = (BASE_DIR / "lore" / "MYSTERY.md").read_text()

prompt = CONFIG["prompts"]["user"].format(part1=part1, mystery=mystery)

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
