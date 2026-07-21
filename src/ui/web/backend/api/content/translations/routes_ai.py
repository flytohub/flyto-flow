"""
Translation API — AI Translation.

Endpoint: AI-powered translation of selected keys.
"""

import json
import logging
import re

import httpx
from fastapi import APIRouter, Depends, HTTPException

from api.content.translations.deps import require_admin
from api.content.translations.github_service import OPENAI_API_KEY
from api.content.translations.models import AITranslateRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ai/translate")
async def ai_translate(
    data: AITranslateRequest,
    _: dict = Depends(require_admin),
):
    """
    Use AI to translate selected keys.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        # Build prompt
        style_instruction = {
            "formal": "Use formal, professional language suitable for software documentation.",
            "casual": "Use friendly, conversational language."
        }.get(data.style, "Use formal language.")

        # Get source texts
        source_texts = {key: "" for key in data.keys}
        # In a real implementation, we'd look up the English values here

        prompt = f"""Translate the following English UI text to {data.target_locale}.

{style_instruction}

Important guidelines:
- Keep placeholders like {{variable}} and ${{variable}} unchanged
- Keep technical terms in English if commonly used
- Match the tone and length of the original
- Return ONLY the JSON object, no explanation

Input (JSON):
{json.dumps(source_texts, indent=2)}

Output (JSON with same keys, translated values):"""

        # Call OpenAI API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a professional translator for software UI."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                }
            )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="OpenAI API error")

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON from response
            try:
                translations = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
                if match:
                    translations = json.loads(match.group(1))
                else:
                    raise HTTPException(status_code=500, detail="Failed to parse AI response")

            return {
                "ok": True,
                "translations": translations,
                "keys_translated": len(translations)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI translation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
