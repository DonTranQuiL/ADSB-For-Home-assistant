import os
from openai import OpenAI

try:
    with open("failed_logs.txt", "r") as f:
        logs = f.read()[-3000:] 
except FileNotFoundError:
    exit(0)

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    exit(0)

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

prompt = f"""
You are an AI Staff Engineer. The pytest suite just failed for SkyRadar Fusion.
Logs:
{logs}

Identify the broken Python file and write the FULL, corrected code.
Respond EXACTLY in this plain text format, with no other words:

FILEPATH: path/to/file.py
CODE:
<full python code here>
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
        with open(file_path, "w") as f:
            f.write("\n".join(code_lines))
        print(f"Patched {file_path}")
        
except Exception as e:
    print(f"Repair failed: {e}")