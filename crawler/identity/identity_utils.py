import json
from openai import OpenAI
from db import is_valid_model


client = OpenAI()


def run_llm_identity(markdown: str):
    if not markdown:
        return {}

    try:
        cleaned = markdown[:20000]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": """
Extract ONLY explicitly stated identity values from the text.

Return a JSON object with:
- gtin
- model

RULES:

GTIN:
- Must be explicitly present in the text
- Must be 12–14 digits
- Do NOT infer or generate
- Do NOT return partial matches
- Do NOT include spaces or symbols

MODEL:
- Must be explicitly present in the text
- Must contain BOTH letters and numbers
- Do NOT infer or guess
- Do NOT normalize or modify
- Do NOT return generic product names

STRICTLY FORBIDDEN:
- Fabrication
- Guessing
- Partial extraction
- Inference
- Hallucinated identifiers

If nothing valid exists, return:

{}

Output MUST be valid JSON only.
"""
                },
                {
                    "role": "user",
                    "content": cleaned
                }
            ],
            temperature=0
        )

        data = json.loads(
            response.choices[0].message.content
        )

        gtin = data.get("gtin")
        model = data.get("model")

        if gtin:
            gtin = str(gtin).strip()

            if not (
                gtin.isdigit()
                and 12 <= len(gtin) <= 14
            ):
                gtin = None

        if model:
            model = model.strip().upper()

            if not is_valid_model(model):
                model = None

        return {
            "gtin": gtin,
            "model": model
        }

    except Exception as e:
        print("[LLM ERROR]", e)
        return {}