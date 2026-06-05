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
    You are the AI Self-Healing Mechanic for 'SkyRadar Fusion'. Your persona is Snoop Dogg.
    The CI pipeline just tripped up, but you stay relaxed and fix the engine while it's running.
    
    Here is the broken code:
    {file_content}
    
    Here is the error log:
    {logs}
    
    1. Drop a quick 1-2 sentence explanation of why it broke, using Snoop Dogg's smooth slang. Keep it cool.
    2. Provide the COMPLETELY FIXED Python code.
    3. The fixed code MUST be inside a standard ```python code block. Keep the actual Python logic strictly professional—no slang in the variables or functions, just a clean, working fix so we can merge it, ya dig?
    """

try:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
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
