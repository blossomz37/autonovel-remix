#!/usr/bin/env python3
"""
Rebuild outline.md from the actual chapters.
Reads each chapter, calls the LLM for a structured summary,
and assembles into an outline that reflects the novel as-written.
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
PROJECT_DIR = BASE_DIR / "workspace"

JUDGE_MODEL = os.environ.get("AUTONOVEL_JUDGE_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://openrouter.ai/api/v1")
CHAPTERS_DIR = PROJECT_DIR / "chapters"

with open(BASE_DIR / "config" / "build_outline.toml", "rb") as f:
    CONFIG = tomllib.load(f)

def call_model(prompt, max_tokens=None, temperature=None):
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
    text = msg.choices[0].message.content
    # Extract JSON from response
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text)

def main():
    # Load supporting docs for context
    characters = (PROJECT_DIR / "lore" / "characters.md").read_text()[:3000]
    
    entries = []
    
    for ch in range(1, 20):
        path = CHAPTERS_DIR / f"ch_{ch:02d}.md"
        text = path.read_text()
        wc = len(text.split())
        
        title_line = text.strip().split('\n')[0].lstrip('# ').strip()
        
        prompt = CONFIG["prompts"]["user"].format(ch=ch, title_line=title_line, wc=wc, text=text)

        data = call_model(prompt)
        data["num"] = ch
        data["words"] = wc
        entries.append(data)
        print(f"  {ch:2d}. {title_line} ({wc}w)")
    
    # Load existing outline header info
    old_outline = (PROJECT_DIR / "lore" / "outline.md").read_text()
    
    # Build new outline
    lines = []
    lines.append("# THE SECOND SON OF THE HOUSE OF BELLS")
    lines.append("## Chapter Outline (reflects actual novel as-written)")
    lines.append("")
    lines.append(f"**23 chapters, {sum(e['words'] for e in entries):,} words**")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for e in entries:
        lines.append(f"### Ch {e['num']}: {e['title']}")
        lines.append(f"**{e['words']} words** | **Location:** {e.get('location', 'N/A')}")
        lines.append(f"- **Characters:** {', '.join(e.get('characters', []))}")
        lines.append(f"- **Try-fail cycle:** {e.get('try_fail', 'N/A')}")
        lines.append(f"- **Emotional arc:** {e.get('emotional_arc', 'N/A')}")
        lines.append("")
        lines.append(f"**Summary:** {e.get('summary', 'N/A')}")
        lines.append("")
        lines.append("**Beats:**")
        for b in e.get("beats", []):
            lines.append(f"1. {b}")
        lines.append("")
        if e.get("plants"):
            lines.append("**Plants:**")
            for p in e["plants"]:
                lines.append(f"- {p}")
            lines.append("")
        if e.get("harvests"):
            lines.append("**Harvests:**")
            for h in e["harvests"]:
                lines.append(f"- {h}")
            lines.append("")
        lines.append(f"**Chapter question:** {e.get('chapter_question', 'N/A')}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Foreshadowing ledger
    lines.append("## FORESHADOWING LEDGER")
    lines.append("")
    lines.append("| Thread | Planted | Harvested |")
    lines.append("|--------|---------|-----------|")
    
    # Collect all plants and harvests
    all_plants = {}
    all_harvests = {}
    for e in entries:
        for p in e.get("plants", []):
            key = p[:60]
            if key not in all_plants:
                all_plants[key] = []
            all_plants[key].append(e["num"])
        for h in e.get("harvests", []):
            key = h[:60]
            if key not in all_harvests:
                all_harvests[key] = []
            all_harvests[key].append(e["num"])
    
    # Match plants to harvests by keyword overlap
    all_threads = set(list(all_plants.keys()) + list(all_harvests.keys()))
    for thread in sorted(all_threads):
        planted = ", ".join(f"Ch {n}" for n in all_plants.get(thread, []))
        harvested = ", ".join(f"Ch {n}" for n in all_harvests.get(thread, []))
        lines.append(f"| {thread} | {planted} | {harvested} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Outline rebuilt from actual chapters, Cycle 5.*")
    
    out = '\n'.join(lines)
    (PROJECT_DIR / "lore" / "outline.md").write_text(out)
    print(f"\nSaved outline.md ({len(out.split())} words)")

if __name__ == "__main__":
    main()
