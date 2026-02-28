"""AI Content Editor service — refines recipe outputs using Gemini.

Provides a conversational editing experience: the user sees the generated
content in an editable area, types an instruction (e.g. "make it punchier",
"add a CTA", "rewrite the intro"), and the AI revises the content while
honouring the brand and persona context.

Security: All user input is sanitised before being sent to the AI.
Conversation history is kept client-side (sent with each request) to
avoid storing PII/chat logs in the database.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Maximum conversation turns to accept per request (prevent abuse)
MAX_HISTORY_TURNS = 20
# Maximum content length (characters) we'll accept
MAX_CONTENT_LENGTH = 50_000
# Maximum instruction length (characters)
MAX_INSTRUCTION_LENGTH = 2_000


def refine_content(
    content: str,
    instruction: str,
    *,
    brand_context: str = "",
    persona_context: str = "",
    history: Optional[list] = None,
) -> dict:
    """Refine content based on user instruction with brand/persona awareness.

    Parameters
    ----------
    content : str
        The current text the user is editing (Markdown).
    instruction : str
        What the user wants changed (e.g. "make the tone more casual").
    brand_context : str
        Pre-built brand context string from ``BaseRecipe.build_brand_context()``.
    persona_context : str
        Pre-built persona context string from ``BaseRecipe.build_persona_context()``.
    history : list, optional
        Previous conversation turns: ``[{"role": "user", "text": "..."}, ...]``
        Kept client-side to avoid DB writes; truncated to MAX_HISTORY_TURNS.

    Returns
    -------
    dict
        ``{"refined_content": str, "explanation": str}``

    Raises
    ------
    ValueError
        If inputs exceed size limits.
    RuntimeError
        If the AI call fails.
    """
    # ── Input validation ──
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")
    if not instruction or not instruction.strip():
        raise ValueError("Instruction cannot be empty")
    if len(content) > MAX_CONTENT_LENGTH:
        raise ValueError(
            f"Content too long ({len(content):,} chars). "
            f"Maximum is {MAX_CONTENT_LENGTH:,} characters."
        )
    if len(instruction) > MAX_INSTRUCTION_LENGTH:
        raise ValueError(
            f"Instruction too long ({len(instruction):,} chars). "
            f"Maximum is {MAX_INSTRUCTION_LENGTH:,} characters."
        )

    # Sanitise & truncate history
    safe_history = _sanitise_history(history)

    # ── Build the prompt ──
    prompt = _build_editor_prompt(
        content=content.strip(),
        instruction=instruction.strip(),
        brand_context=brand_context,
        persona_context=persona_context,
        history=safe_history,
    )

    # ── Call Gemini ──
    from .agent_service import _call_gemini

    try:
        raw = _call_gemini(prompt)
    except Exception as exc:
        logger.error("Editor AI call failed: %s", exc)
        raise RuntimeError(
            "The AI editor couldn't process your request. Please try again."
        ) from exc

    # ── Parse response ──
    refined, explanation = _parse_editor_response(raw)

    return {
        "refined_content": refined,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sanitise_history(history: Optional[list]) -> list:
    """Validate and truncate conversation history."""
    if not history or not isinstance(history, list):
        return []

    safe = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role", "")
        text = turn.get("text", "")
        if role in ("user", "assistant") and text and len(text) < 10_000:
            safe.append({"role": role, "text": text[:5_000]})

    return safe


def _build_editor_prompt(
    content: str,
    instruction: str,
    brand_context: str,
    persona_context: str,
    history: list,
) -> str:
    """Assemble the full prompt for the editor AI."""
    # Brand/persona preamble
    context_block = ""
    if brand_context:
        context_block += (
            f"\n{brand_context}\n"
            "You MUST maintain this brand's voice, colors, and guidelines "
            "in all edits. Never contradict the brand.\n"
        )
    if persona_context:
        context_block += (
            f"\n{persona_context}\n"
            "Write in this persona's voice and style. Use their keywords "
            "naturally. Avoid their listed 'never use' words.\n"
        )

    # Conversation history block
    history_block = ""
    if history:
        turns = []
        for turn in history:
            prefix = "User" if turn["role"] == "user" else "Editor"
            turns.append(f"**{prefix}:** {turn['text']}")
        history_block = (
            "\n--- Previous Conversation ---\n"
            + "\n".join(turns)
            + "\n--- End Previous Conversation ---\n"
        )

    return f"""You are an expert AI content editor. The user has generated content
using a recipe and now wants to refine it. Your job is to apply their
editing instruction precisely while maintaining overall quality.

{context_block}
{history_block}

--- CURRENT CONTENT (user is editing this) ---
{content}
--- END CURRENT CONTENT ---

**User's editing instruction:** {instruction}

RULES:
1. Apply the user's instruction precisely — don't over-edit or change things they didn't ask about
2. Maintain the same formatting style (Markdown headers, lists, etc.)
3. If the instruction is unclear, make a reasonable interpretation and explain what you did
4. Keep the same approximate length unless the user asks to expand or shorten
5. Preserve any data, statistics, source attributions, and factual claims
6. If brand/persona context is provided, ensure edits stay on-brand

OUTPUT FORMAT (you MUST follow this exactly):
First, output the complete refined content (the full updated text, not just the changed parts).
Then output this exact separator on its own line:
---EDITOR_EXPLANATION---
Then output 1-3 sentences explaining what you changed and why.

Output the refined content now:"""


def _parse_editor_response(raw: str) -> tuple:
    """Split the AI response into (refined_content, explanation)."""
    SEP = "---EDITOR_EXPLANATION---"

    if SEP in raw:
        parts = raw.split(SEP, 1)
        refined = parts[0].strip()
        explanation = parts[1].strip()
    else:
        # No separator — treat the whole response as refined content
        refined = raw.strip()
        explanation = "Content has been updated based on your instruction."

    # Strip any markdown code fences the model may have wrapped
    if refined.startswith("```") and refined.endswith("```"):
        lines = refined.split("\n")
        # Remove first and last lines if they're fences
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        refined = "\n".join(lines).strip()

    return refined, explanation
