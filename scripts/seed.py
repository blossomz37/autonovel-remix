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
PROJECT_DIR = BASE_DIR / "workspace"

WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6-20250217")
ANTHROPIC_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_BASE_URL = os.environ.get("AUTONOVEL_API_BASE_URL", "https://openrouter.ai/api/v1")
ANTHROPIC_BETA = "context-1m-2025-08-07"


with open(BASE_DIR / "config" / "seed.toml", "rb") as f:
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
    parser = argparse.ArgumentParser(description="Generate novel seed concepts")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of concepts to generate (default: 10)")
    parser.add_argument("--riff", type=str, default=None,
                        help="Riff on an existing idea")
    parser.add_argument("--auto-select", nargs="?", const="the most original, narratively sound, and compelling option", default=None,
                        help="Automatically select the best seed and write it to seed.txt. Optionally provide selection criteria.")
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
    
    ideas_dir = PROJECT_DIR / "ideas"
    ideas_dir.mkdir(exist_ok=True)
    
    out_file = ideas_dir / ("riff.md" if args.riff else "seeds.md")
    out_file.write_text(result)
    
    if args.auto_select:
        print("\n" + "=" * 60)
        print(f"Auto-selecting the best seed using criteria: '{args.auto_select}'...")
        select_prompt = CONFIG["prompts"]["select_prompt"].format(criteria=args.auto_select)
        full_select_prompt = f"{select_prompt}\n\nGENERATED SEEDS:\n{result}"
        
        from api_client import call_llm
        from pathlib import Path
        
        selected_seed = call_llm(
            messages=[
                {"role": "user", "content": full_select_prompt}
            ],
            model=WRITER_MODEL,
            max_tokens=2000,
            temperature=0.4,
            stream=True,
            script_name=Path(__file__).name
        )
        
        seed_txt = PROJECT_DIR / "lore" / "seed.txt"
        seed_txt.parent.mkdir(parents=True, exist_ok=True)
        seed_txt.write_text(selected_seed.strip())
        
        print("\n" + "=" * 60)
        print(f"Auto-selected seed written to: {seed_txt.relative_to(BASE_DIR)}")
        print("Then proceed to Step 2 in WORKFLOW.md.")
    else:
        print("\n" + "=" * 60)
        print(f"Saved concepts to: {out_file.relative_to(BASE_DIR)}")
        print("To pick a seed, copy the concept you like into workspace/lore/seed.txt:")
        print("  nano workspace/lore/seed.txt")
        print("Or remix several concepts into your own seed.")
        print("Then proceed to Step 2 in WORKFLOW.md.")


if __name__ == "__main__":
    main()
