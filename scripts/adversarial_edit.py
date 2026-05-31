#!/usr/bin/env python3
"""
Adversarial editing pass: ask the judge to CUT 500 words from each chapter.
What gets cut reveals what's weakest. The cut list IS the revision plan.

Usage: python adversarial_edit.py 1        # single chapter
       python adversarial_edit.py all      # all chapters
"""
import os
import sys
import json
import re
import tomllib
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

JUDGE_MODEL = os.environ.get("AUTONOVEL_JUDGE_MODEL", "claude-opus-4-6")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://openrouter.ai/api/v1")
CHAPTERS_DIR = BASE_DIR / "chapters"
EDIT_LOG_DIR = BASE_DIR / "edit_logs"
EDIT_LOG_DIR.mkdir(exist_ok=True)

with open(BASE_DIR / "config" / "adversarial_edit.toml", "rb") as f:
    CONFIG = tomllib.load(f)

def call_judge(prompt, max_tokens=None, temperature=None):
    if max_tokens is None: max_tokens = CONFIG["model"]["max_tokens"]
    if temperature is None: temperature = CONFIG["model"]["temperature"]
    import openai
    client = openai.OpenAI(api_key=API_KEY, base_url=API_BASE)
    msg = client.chat.completions.create(
        model=JUDGE_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": CONFIG["prompts"]["system"].strip()},
            {"role": "user", "content": prompt}
        ],
        timeout=300,
    )
    return msg.choices[0].message.content

def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    start = text.find('{')
    if start == -1:
        start = text.find('[')
    if start == -1:
        raise ValueError("No JSON found")
    # Try direct parse first
    try:
        return json.loads(text[start:], strict=False)
    except json.JSONDecodeError:
        # Find matching brace
        depth = 0
        in_string = False
        escape = False
        open_char = text[start]
        close_char = '}' if open_char == '{' else ']'
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == '\\' and in_string:
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == open_char:
                depth += 1
            elif c == close_char:
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1], strict=False)
        return json.loads(text[start:], strict=False)

EDIT_PROMPT = CONFIG["prompts"]["user"]

def edit_chapter(ch_num):
    ch_path = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
    text = ch_path.read_text()
    word_count = len(text.split())
    
    prompt = EDIT_PROMPT.format(chapter_text=text, word_count=word_count)
    raw = call_judge(prompt)
    result = parse_json(raw)
    
    # Save log
    log_path = EDIT_LOG_DIR / f"ch{ch_num:02d}_cuts.json"
    with open(log_path, "w") as f:
        json.dump(result, f, indent=2)
    
    return result, word_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python adversarial_edit.py <chapter_num|all>")
        sys.exit(1)
    
    if sys.argv[1] == "all":
        chapters = list(range(1, 25))
    else:
        chapters = [int(sys.argv[1])]
    
    for ch in chapters:
        print(f"\n{'='*50}")
        print(f"EDITING CH {ch}")
        print(f"{'='*50}")
        
        try:
            result, wc = edit_chapter(ch)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        
        cuts = result.get("cuts", [])
        cuttable = result.get("total_cuttable_words", 0)
        fat_pct = result.get("overall_fat_percentage", 0)
        verdict = result.get("one_sentence_verdict", "")
        
        # Count by type
        type_counts = {}
        for c in cuts:
            t = c.get("type", "?")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        print(f"  Words: {wc}")
        print(f"  Cuts found: {len(cuts)}")
        print(f"  Cuttable words: ~{cuttable} ({fat_pct}% fat)")
        print(f"  By type: {type_counts}")
        print(f"  Verdict: {verdict}")
        print(f"  Tightest: {result.get('tightest_passage', '')[:100]}...")
        print(f"  Loosest:  {result.get('loosest_passage', '')[:100]}...")

if __name__ == "__main__":
    main()
