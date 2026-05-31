#!/usr/bin/env python3
"""
seed.py -- Generate fantasy novel seed concepts.

Usage:
  uv run python seed.py              # Generate 10 concepts, pick one
  uv run python seed.py --count=5    # Generate 5 concepts
  uv run python seed.py --riff "magic costs memories"  # Riff on an idea
"""

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6-20250217")
ANTHROPIC_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_BASE_URL = os.environ.get("AUTONOVEL_API_BASE_URL", "https://openrouter.ai/api/v1")
ANTHROPIC_BETA = "context-1m-2025-08-07"


with open(BASE_DIR / "config" / "seed.toml", "rb") as f:
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
    parser = argparse.ArgumentParser(description="Generate novel seed concepts")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of concepts to generate (default: 10)")
    parser.add_argument("--riff", type=str, default=None,
                        help="Riff on an existing idea")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("ERROR: Set ANTHROPIC_API_KEY in .env first")
        sys.exit(1)

    if args.riff:
        print(f"Riffing on: {args.riff}\n")
        prompt = CONFIG["prompts"]["riff_prompt"].format(idea=args.riff)
    else:
        print(f"Generating {args.count} seed concepts...\n")
        prompt = CONFIG["prompts"]["generate_prompt"].format(count=args.count)

    result = call_writer(prompt)
    print(result)
    print("\n" + "=" * 60)
    print("To pick a seed, copy the concept you like into seed.txt:")
    print("  nano seed.txt")
    print("Or remix several concepts into your own seed.")
    print("Then proceed to Step 2 in WORKFLOW.md.")


if __name__ == "__main__":
    main()
