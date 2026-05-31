import os
import re

scripts_dir = "/Users/carlo/Github/autonovel-master/scripts"

WRITER_PATTERN = re.compile(
    r'def call_writer\(.*?\):.*?return full_text',
    re.DOTALL
)

WRITER_REPLACEMENT = """def call_writer(prompt, max_tokens=None, temperature=None):
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
    )"""

EVALUATOR_PATTERN = re.compile(
    r'def call_evaluator\(.*?\):.*?return content',
    re.DOTALL
)

EVALUATOR_REPLACEMENT = """def call_evaluator(prompt, max_tokens=None, temperature=None):
    if max_tokens is None: max_tokens = CONFIG.get("model", {}).get("max_tokens", 4000)
    if temperature is None: temperature = CONFIG.get("model", {}).get("temperature", 0.2)
    from api_client import call_llm
    from pathlib import Path
    return call_llm(
        messages=[
            {"role": "system", "content": CONFIG["prompts"]["system"].strip()},
            {"role": "user", "content": prompt}
        ],
        model=EVALUATOR_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=False,
        require_json=True,
        script_name=Path(__file__).name
    )"""

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    new_content = content
    if "def call_writer" in new_content:
        # Some scripts might not return full_text but something else? We standardized it to return full_text
        new_content = WRITER_PATTERN.sub(WRITER_REPLACEMENT, new_content)
    
    if "def call_evaluator" in new_content:
        new_content = EVALUATOR_PATTERN.sub(EVALUATOR_REPLACEMENT, new_content)

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Refactored: {os.path.basename(filepath)}")

for filename in os.listdir(scripts_dir):
    if filename.endswith(".py") and filename != "api_client.py":
        process_file(os.path.join(scripts_dir, filename))

print("Done.")
