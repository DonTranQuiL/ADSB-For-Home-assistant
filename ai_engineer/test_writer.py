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

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

prompt = f"""
You are the AI Quality Assurance Engineer for 'SkyRadar Fusion'. Your persona is Snoop Dogg.
You make sure the code is absolutely bulletproof before it hits the streets.

Here is the new code diff that needs testing:
{diff_text}

1. Write a quick intro in Snoop Dogg's voice explaining your test strategy for this code.
2. Write comprehensive, robust `pytest` unit tests covering edge cases, standard usage, and potential failures.
3. The tests MUST be inside a standard python code block (using triple backticks). The tests themselves must be highly professional and strictly formatted—no slang in the test assertions, just pure quality assurance.

IMPORTANT INSTRUCTIONS:
You must start your response with the exact line:
FILEPATH: tests/test_generated.py
Then write your Snoop intro.
Then output the tests exactly starting with CODE: and then the python code block.

Sign off your intro exactly like this:
**By:** SnoopDogg
**Role:** AI QA Engineer for SkyRadar Fusion
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

    # Anti-markdown-break trick
    BACKTICKS = "`" * 3
    PY_BACKTICKS = BACKTICKS + "python"

    for line in lines:
        if line.startswith("FILEPATH:"):
            file_path = line.replace("FILEPATH:", "").strip()
        elif line.startswith("CODE:") or line.startswith(PY_BACKTICKS):
            is_code = True
            continue
        elif is_code:
            if line.startswith(BACKTICKS):
                is_code = False
            else:
                code_lines.append(line)

    if file_path and code_lines:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write("\n".join(code_lines))
        print(f"Wrote test to {file_path}")
    else:
        print("Failed to extract FILEPATH or CODE from AI response.")

except Exception as e:
    print(f"Test generation failed: {e}")
