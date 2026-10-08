import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash-lite"


def analyze_issue(title, description):

    prompt = f"""
You are an AI maintenance management assistant.

Analyze the following maintenance issue.

Issue Title:
{title}

Description:
{description}

Return a JSON object with exactly these four fields:

{{
    "category": "string",
    "priority": "LOW, MEDIUM, or HIGH",
    "ai_summary": "short summary of the problem",
    "suggested_action": "recommended maintenance action"
}}

Choose a suitable category such as:
HVAC, Electrical, Plumbing, IT, Equipment, Furniture, Safety, or Other.

Priority rules:
- LOW: minor issue with little operational impact
- MEDIUM: issue affects normal operation but is not critical
- HIGH: safety risk, major equipment failure, or serious disruption
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    result = response.text.strip()

    return json.loads(result)