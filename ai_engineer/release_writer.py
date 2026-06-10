import os
import re
import requests
from openai import OpenAI

try:
    with open("changelog.txt", "r") as f:
        changelog = f.read()
except FileNotFoundError:
    print("Could not find changelog.txt. Exiting.")
    exit(0)

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("No API key found. Exiting.")
    exit(0)

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

prompt = f"""
You are the AI Release Manager for 'SkyRadar Fusion'. Your persona is Snoop Dogg.
We are dropping a brand new release, and your job is to write the official GitHub Release Notes based on the commit history.

Here are the commit titles and extended descriptions since the last release:
{changelog}

1. Analyze these commit messages and organize them into clean, professional markdown categories:
   - 🚀 What's New (New features)
   - 🛠️ Changed & Fixed (Bug fixes, deprecated lines, updates)
   - ⚙️ Under the Hood (Backend stuff, dependency updates)
2. Explain the updates in a smooth, engaging way (Snoop Dogg style, but keep it highly professional so users understand the updates).
3. ONLY output the raw Markdown text. DO NOT wrap your response in triple backticks (```) or a code block. Just output the raw text directly.
"""

try:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    release_notes = completion.choices[0].message.content.strip()

    # Clean up any accidental code block wrappers
    release_notes = re.sub(r"^
