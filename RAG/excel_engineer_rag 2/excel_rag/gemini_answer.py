from __future__ import annotations

import os

SYSTEM_RULES = """
You are an engineering Excel analysis assistant.
Rules:
1. Use only the retrieved workbook context.
2. Always mention sheet name and cell address for formulas.
3. Do not invent engineering formulas outside the context.
4. If the requested formula is not in context, say it is not found in retrieved cells.
5. When converting Excel formula to JavaScript, preserve Excel logic as much as possible.
6. Explain dependencies and units only when present in context.
7. Flag risky formulas such as INDIRECT, OFFSET, external references, and #REF!.
""".strip()


def answer_with_gemini(question: str, context: str, model: str = "gemini-3-flash-preview") -> str:
    """Generate grounded answer with Gemini API.

    Requires environment variable GEMINI_API_KEY.
    Uses official Google GenAI SDK: google-genai.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "GEMINI_API_KEY belum diset. Berikut retrieved context mentah:\n\n"
            + context
        )

    from google import genai

    client = genai.Client(api_key=api_key)
    prompt = f"""
{SYSTEM_RULES}

Retrieved workbook context:
{context}

User question:
{question}

Answer in Indonesian. Include Excel formula and JavaScript code if relevant.
""".strip()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    return response.text or "Tidak ada jawaban dari model."
