import os
from openai import OpenAI

try:
    with open("merged_diff.txt", "r") as f:
        diff_text = f.read()
except FileNotFoundError:
    exit(0)

if len(diff_text.strip()) < 10:
    exit(0)

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    exit(0)

client = OpenAI(base_url="[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)", api_key=api_key)

prompt = f"""
You are an AI Staff Engineer for SkyRadar Fusion. A PR was just merged.
Write ONE single `pytest` function covering a new edge case introduced by this diff.

When mocking Home Assistant zone coordinates in your tests, use a baseline latitude of 50.86 and longitude of 6.06 to test the `haversine_distance` calculations accurately. Assume ADS-B dictionaries might have missing fields like 'alt_baro' or 'squawk'.

Respond EXACTLY in this plain text format, with no other words:

FILEPATH: tests/test_auto_generated.py
CODE:
<full python test code here>

Diff:
{diff_text}
"""

try:
    completion = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct:free",
        messages=[{"role": "user", "content": prompt}]
    )
    
    lines = completion.choices[0].message.content.strip().splitlines()
    file_path = None
    code_lines = []
    is_code = False
    
    for line in lines:
        if line.startswith("FILEPATH:"):
            file_path = line.replace("FILEPATH:", "").strip()
        elif line.startswith("CODE:"):
            is_code = True
        elif is_code and not line.startswith("```"):
            code_lines.append(line)
            
    if file_path and code_lines:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write("\n".join(code_lines))
        print(f"Wrote test to {file_path}")
        
except Exception as e:
    print(f"Test generation failed: {e}")