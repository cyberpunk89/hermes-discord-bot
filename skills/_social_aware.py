"""
Social Awareness Layer - "Should I Respond?" Decision Filter

Makes Hermes respond naturally to conversations instead of every message.

Two-stage pipeline:
1. Hard filters (cheap) - skip obvious non-responses
2. LLM decision (moderate) - determine if response warrants engagement
3. Probability gate - not every trigger fires
"""

import os
import re
import random
from typing import Optional

# For LLM calls - will use existing Hermes infrastructure
HERMES_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Response rate thresholds by trigger type
RESPONSE_RATES = {
    "funny": 0.90,       # 90% - jokes, memes
    "question": 0.80,   # 80% - questions to group
    "hot_take": 0.70,    # 70% - debate starters
    "relatable": 0.60,   # 60% - venting, complaints
    "compliment": 0.85,  # 85% - praise, thanks
    "observation": 0.50, # 50% - interesting observations
    "none": 0.30,       # 30% - default for uncategorized
}

# Trigger patterns
TRIGGER_PATTERNS = {
    "funny": [
        r"\blol\b",
        r"\blmao\b",
        r"\brofl\b",
        r"\bfunny\b",
        r"\bdied\b",
        r"\bdead\b",
        r"\bshits?\b",
        r"\bcopium\b",
    ],
    "question": [
        r"\bwho wants\b",
        r"\banyone\b",
        r"\bshould we\b",
        r"\blets? (play|do|go)\b",
        r"\bwhat (game|mode|map)\b",
        r"\bjoin\b",
        r"\bserver\b",
    ],
    "hot_take": [
        r"\btake is\b",
        r"\b(un|over)rated\b",
        r"\b(is|are) (better|worse)\b",
        r"\bnot (good|bad)\b",
        r"\bcontroversial\b",
        r"\bdebate\b",
        r"\bchange my mind\b",
    ],
    "relatable": [
        r"\b(so|really|totally) (annoying|frustrating|mad)\b",
        r"\b(why|how) does (this|it) (always|never)\b",
        r"\bhate\b",
        r"\bventing\b",
        r"\b(dead|exhausted) after\b",
    ],
    "compliment": [
        r"\b(thanks|thank you|appreciate)\b",
        r"\b(very|really|super) (good|great|cool|nice)\b",
        r"\bloved\b",
        r"\bamazing\b",
    ],
    "observation": [
        r"\b(interesting|weird|odd|random)\b",
        r"\bjust (realized|noticed|thought)\b",
        r"\bfun fact\b",
    ],
}


def hard_filter(message: str) -> tuple[bool, str]:
    """
    Quick hard filters before any LLM call.
    Returns (should_skip, reason)
    """
    msg = message.strip()
    msg_lower = msg.lower()
    
    # Skip one-word responses
    if len(msg.split()) == 1:
        return True, "one_word"
    
    # Skip logistics patterns
    logistics_patterns = [
        r"^(ok|okay|alright|got it|gotcha|sure|ye[as]?)\b",
        r"^meeting\s+at\s+\d",
        r"^see\s+(you|ya)\s+(later|tomorrow|at)\b",
        r"^(bye|brb|gtg|nf)\b",
        r"^on\s+(my|one|your)\s+way\b",
        r"^\d+:\d+\s*(am|pm)\b",
    ]
    
    for pattern in logistics_patterns:
        if re.search(pattern, msg_lower):
            return True, "logistics"
    
    # Skip @ mentions to specific users (not Hermes)
    mention_match = re.search(r"<@(\d+)>", msg)
    if mention_match:
        # Allow if mentioning bot, otherwise skip
        bot_id = os.environ.get("DISCORD_BOT_ID", "")
        if mention_match.group(1) != bot_id:
            return True, "dm"
    
    # Skip spoiler tags
    if msg.startswith("||") and msg.endswith("||"):
        return True, "spoiler"
    
    return False, ""


def get_trigger_category(message: str) -> str:
    """Determine trigger category without LLM (pattern-based)"""
    msg_lower = message.lower()
    
    for category, patterns in TRIGGER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return category
    
    return "none"


def build_decision_prompt(message: str) -> str:
    """Build the LLM prompt for decision"""
    return f"""You are a social awareness filter for a witty NPC character in a Discord gaming group chat.

Message from user: "{message}"

Does this deserve a natural, witty response from this character? Consider:
- Is it genuinely funny or absurdist?
- Is it a question directed at the group?
- Is it a hot take or debate-starter?
- Is it relatable venting/complaining?
- Is it a compliment worth acknowledging?
- Is it an interesting observation?

Respond with ONLY valid JSON (no other text):
{{
  "respond": true or false,
  "reason": "funny/question/hot_take/relatable/compliment/observation/none/skip",
  "tone": "playful/sarcastic/witty/serious/dry/none",
  "confidence": 0.0 to 1.0
}}

JSON only:"""


async def call_llm_decision(message: str) -> dict:
    """Call LLM to get decision (placeholder - integrate with existing Hermes)"""
    # This would integrate with your existing Hermes LLM calls
    # For now, use pattern-based fallback
    
    category = get_trigger_category(message)
    
    return {
        "respond": category != "none",
        "reason": category,
        "tone": "playful" if category in ["funny", "question"] else "witty",
        "confidence": 0.7 if category != "none" else 0.5,
    }


def should_respond_after_gate(decision: dict) -> bool:
    """Apply probability gate"""
    if not decision.get("respond", False):
        return False
    
    reason = decision.get("reason", "none")
    rate = RESPONSE_RATES.get(reason, 0.30)
    
    return random.random() < rate


# Main function
async def should_respond(message: str, context: Optional[dict] = None) -> dict:
    """
    Main entry point - returns decision on whether to respond.
    
    Returns:
    {
        "respond": bool,
        "reason": str,
        "tone": str,
        "confidence": float,
        "skip_type": str (if respond=False)
    }
    """
    # Hard filters first
    should_skip, skip_reason = hard_filter(message)
    if should_skip:
        return {
            "respond": False,
            "reason": skip_reason,
            "tone": "none",
            "confidence": 0.95,
            "skip_type": skip_reason,
        }
    
    # Quick pattern check first (cheap)
    category = get_trigger_category(message)
    if category != "none":
        # Has trigger, apply probability gate
        decision = {
            "respond": True,
            "reason": category,
            "tone": "playful",
            "confidence": 0.7,
        }
        
        if should_respond_after_gate(decision):
            return decision
        else:
            return {
                "respond": False,
                "reason": category,
                "tone": "none",
                "confidence": 0.7,
                "skip_type": "probability_gate",
            }
    
    # No patterns found - could call LLM for better detection
    # For now, use default rate
    decision = {
        "respond": True,
        "reason": "observation",
        "tone": "witty",
        "confidence": 0.5,
    }
    
    if should_respond_after_gate(decision):
        return decision
    
    return {
        "respond": False,
        "reason": "none",
        "tone": "none",
        "confidence": 0.5,
        "skip_type": "probability_gate",
    }


def get_natural_delay(response: str) -> float:
    """
    Calculate typing delay for natural feel.
    Based on response length + random jitter.
    """
    if not response:
        return 0.5
    
    # Base: ~50 characters per second typing speed
    base = len(response) / 50
    
    # Random jitter between 0.5-2.0 seconds
    jitter = random.uniform(0.5, 2.0)
    
    # Cap between 1-5 seconds for realism
    delay = min(max(base + jitter, 1.0), 5.0)
    
    return delay


# Helper for testing
def get_decision_for_display(message: str) -> str:
    """Synchronous wrapper for testing"""
    import asyncio
    
    # Since we're using pattern-based for now, sync fallback
    should_skip, skip_reason = hard_filter(message)
    if should_skip:
        return f'skip ({skip_reason})'
    
    category = get_trigger_category(message)
    decision = {
        "respond": category != "none",
        "reason": category,
        "tone": "playful",
        "confidence": 0.7,
    }
    
    if should_respond_after_gate(decision):
        return f'respond ({category})'
    
    return f'skip (probability_gate)'


if __name__ == "__main__":
    # Test
    test_messages = [
        "This game is literally unplayable lol",
        "who wants to play some co-op?",
        "ok meeting at 8",
        "lol",
        "this take is wild - the combat is way better",
        "thanks for the recommendation!",
        "just found this funny clip",
        "anyone want to do a raid?",
    ]
    
    print("=== Social Awareness Test ===\n")
    for msg in test_messages:
        decision = get_decision_for_display(msg)
        print(f"{msg:40} -> {decision}")