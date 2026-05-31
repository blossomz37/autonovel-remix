import os
import sys
import csv
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path
import openai

BASE_DIR = Path(__file__).parent.parent
PROJECT_DIR = BASE_DIR / "workspace"
DATA_DIR = PROJECT_DIR / "data"
USAGE_CSV = DATA_DIR / "usage.csv"

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://openrouter.ai/api/v1")

def get_openrouter_cost(gen_id: str) -> float:
    """Fetch the cost of a generation from OpenRouter with retries."""
    if not gen_id or "openrouter" not in API_BASE:
        return 0.0
    
    max_retries = 3
    delays = [2, 5, 10]  # wait 2s, then 5s, then 10s if needed
    
    for attempt in range(max_retries):
        time.sleep(delays[attempt])
        
        req = urllib.request.Request(
            f"https://openrouter.ai/api/v1/generation?id={gen_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if "data" in data and "total_cost" in data["data"]:
                    return float(data["data"]["total_cost"])
        except urllib.error.HTTPError as e:
            if e.code == 404 and attempt < max_retries - 1:
                # Normal behavior: OpenRouter hasn't indexed it yet. Retry.
                continue
            print(f"[Warning] Failed to fetch cost from OpenRouter (Attempt {attempt+1}/{max_retries}): {e}", file=sys.stderr)
        except Exception as e:
            print(f"[Warning] Failed to fetch cost from OpenRouter (Attempt {attempt+1}/{max_retries}): {e}", file=sys.stderr)
            if attempt == max_retries - 1:
                break
            
    return 0.0

def log_usage(script_name: str, model: str, prompt_tokens: int, completion_tokens: int, cost: float = 0.0):
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    file_exists = USAGE_CSV.exists()
    
    try:
        with open(USAGE_CSV, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Script", "Model", "Prompt Tokens", "Completion Tokens", "Total Tokens", "Cost (USD)"])
            
            writer.writerow([
                datetime.now().isoformat(),
                script_name,
                model,
                prompt_tokens,
                completion_tokens,
                prompt_tokens + completion_tokens,
                f"${cost:.6f}" if cost > 0 else "$0.000000"
            ])
    except Exception as e:
        print(f"[Warning] Failed to log usage: {e}", file=sys.stderr)

def call_llm(messages: list, model: str, max_tokens: int = 4000, temperature: float = 0.7, 
             stream: bool = True, require_json: bool = False, script_name: str = "unknown"):
    
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
    
    stream_options = {"include_usage": True} if stream else None
    response_format = {"type": "json_object"} if require_json else None

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        "timeout": 600,
        "stream": stream,
    }
    if extra_body:
        kwargs["extra_body"] = extra_body
    if stream_options:
        kwargs["stream_options"] = stream_options
    if response_format:
        kwargs["response_format"] = response_format

    try:
        msg = client.chat.completions.create(**kwargs)
    except Exception as e:
        print(f"[Error] API Call failed: {e}", file=sys.stderr)
        raise e

    if stream:
        full_text = ""
        prompt_tokens = 0
        completion_tokens = 0
        gen_id = None
        
        for chunk in msg:
            if not gen_id and hasattr(chunk, 'id'):
                gen_id = chunk.id
                
            if hasattr(chunk, 'usage') and chunk.usage:
                prompt_tokens = getattr(chunk.usage, 'prompt_tokens', 0)
                completion_tokens = getattr(chunk.usage, 'completion_tokens', 0)

            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    text = delta.content
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    full_text += text
        
        sys.stdout.write("\n")
        
        cost = get_openrouter_cost(gen_id) if gen_id else 0.0
        
        if prompt_tokens > 0 or completion_tokens > 0 or cost > 0:
            log_usage(script_name, model, prompt_tokens, completion_tokens, cost)
            
        return full_text
    else:
        content = msg.choices[0].message.content
        prompt_tokens = 0
        completion_tokens = 0
        gen_id = getattr(msg, 'id', None)
        
        if hasattr(msg, 'usage') and msg.usage:
            prompt_tokens = getattr(msg.usage, 'prompt_tokens', 0)
            completion_tokens = getattr(msg.usage, 'completion_tokens', 0)
        
        cost = get_openrouter_cost(gen_id) if gen_id else 0.0
        
        if prompt_tokens > 0 or completion_tokens > 0 or cost > 0:
            log_usage(script_name, model, prompt_tokens, completion_tokens, cost)
            
        return content
