import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.6-flash"


def analyze_issue(title, description):

    prompt = f"""
You are an AI maintenance management assistant.

Analyze the following maintenance issue.

Issue Title:
{title}

Description:
{description}

Return ONLY valid JSON using exactly these four fields:

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

Do not add markdown.
Do not add explanations outside the JSON.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    result = response.text.strip()

    # Remove markdown code fences if Gemini adds them
    if result.startswith("```"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    return json.loads(result)