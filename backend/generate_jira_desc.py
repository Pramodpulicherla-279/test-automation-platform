from google import genai
from google.genai import types
import json
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_jira_description(issue_data):

    prompt = f"""
You are a QA automation assistant.

Convert the following issue details into a professional Jira bug description.

Format:

In the {{app_name}} (Version {{app_version}}), when a user performs the following scenario, the issue occurs.

Steps to Reproduce

1.
2.
3.


Issue Details:
{json.dumps(issue_data, indent=2)}

Only return the formatted description.
"""

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2
        )
    )

    return resp.text.strip()