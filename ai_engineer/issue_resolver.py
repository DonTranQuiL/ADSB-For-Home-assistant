import os
from openai import OpenAI

# 1. Grab the issue details from GitHub environment variables
issue_title = os.getenv("ISSUE_TITLE", "")
issue_body = os.getenv("ISSUE_BODY", "")

if not issue_title or not issue_body:
    print("Missing issue context. Exiting.")
    exit(0)

# 2. Point it at the file that needs updating
# For SkyRadar Fusion, this is usually your coordinator or data management file
target_file = "custom_components/skyradar_fusion/coordinator.py"

try:
    with open(target_file, "r") as f:
        current_code = f.read()
except FileNotFoundError:
    print(f"Could not find target file: {target_file}")
    exit(0)

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("API key missing. Exiting.")
    exit(0)

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

# 3. Setup the Snoop Coder Prompt
prompt = f"""
You are the Lead AI Software Engineer for 'SkyRadar Fusion'. Your persona is Snoop Dogg.
The user just dropped a new feature request / issue report, and you need to implement it directly into the codebase.

Here is the Issue Title:
{issue_title}

Here is the Issue Description:
{issue_body}

Here is the current Python code for {target_file}:
{current_code}

Instructions:
1. Carefully implement the requested changes or new API fields into the existing code.
2. Keep the code professional, efficient, and fully compatible with Home Assistant standard practices.
3. Keep all existing functionality completely intact—do not delete unrelated logic!
4. The response MUST contain the COMPLETELY updated python code inside a standard code block.

IMPORTANT PARSING INSTRUCTIONS:
You must start your response with the exact marker line:
CODE:
followed immediately by the python code block using triple backticks.
"""

try:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = completion.choices[0].message.content.strip()

    # 4. Parse out the code using our bulletproof trick
    lines = response_text.splitlines()
    code_lines = []
    is_code = False

    BACKTICKS = "`" * 3
    PY_BACKTICKS = BACKTICKS + "python"

    for line in lines:
        if line.startswith("CODE:") or line.startswith(PY_BACKTICKS):
            is_code = True
            continue
        elif is_code:
            if line.startswith(BACKTICKS):
                is_code = False
            else:
                code_lines.append(line)

    # 5. Overwrite the file with the AI's new code
    if code_lines:
        with open(target_file, "w") as f:
            f.write("\n".join(code_lines))
        print(f"Successfully implemented feature in {target_file}")
    else:
        print("Failed to parse code from the AI response.")

except Exception as e:
    print(f"Feature development failed: {e}")
