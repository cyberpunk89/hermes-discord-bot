# Social Awareness Layer - Implementation Plan

## Feature: Should I Respond?

A filter that makes Hermes respond naturally to conversations instead of every message.

---

## Problem

Currently Hermes replies to every message in the channel, which feels:
- Bot-like and intrusive
- Overwhelming for conversations
- Misses natural conversation flow

## Solution

Two-stage pipeline:
1. **Cheap LLM Check** - "Should I respond?" (max 200 tokens)
2. **Generate Reply** - Only if decision says yes

---

## Architecture

```
Message → Hard Filters → LLM Decision → Probability Gate → Generate Reply
```

---

## Component: `skills/_social_aware.py`

### Exported Functions

```python
def should_respond(message: str, context: dict) -> dict:
    """
    Returns: { respond: bool, reason: str, tone: str, confidence: float }
    """
    
def get_trigger_category(message: str) -> str:
    """Returns trigger type or 'none'"""
    
def get_natural_delay(response: str) -> float:
    """Typing simulation delay"""
```

### Trigger Categories

| Category | Examples | Response Rate |
|----------|----------|-------------|
| `funny` | jokes, memes, absurd takes | 90% |
| `question` | questions to group | 80% |
| `hot_take` | debate starters | 70% |
| `relatable` | venting, complaints | 60% |
| `compliment` | praise, thanks | 85% |
| `logistics` | meeting times, plans | 0% |
| `one_word` | lol, nice, same | 0% |
| `dm` | @ mentions | 0% |
| `none` | everything else | varies |

---

## Hard Filters (Skip Before LLM)

```python
def hard_filter(message: str) -> bool:
    """Returns True if should skip (don't respond)"""
    # Logistics
    if re.match(r'^(ok|meeting|at \d|see you|bye)', message.lower()):
        return True
    # One word
    if len(message.split()) <= 1:
        return True
    # @ mentions to others
    if re.search(r'<@\d+>', message):
        if '<@BOT_ID>' not in message:
            return True
    return False
```

---

## LLM Decision Prompt

```python
DECISION_PROMPT = """You are a social awareness filter for a witty NPC character.

Message: "{message}"

Does this deserve a natural, witty response? Consider:
- Is it funny or absurdist?
- Is it a question to the group?
- Is it a hot take or debate?
- Is it relatable venting?

Respond with JSON only (no other text):
{{
  "respond": true/false,
  "reason": "funny/question/hot_take/relatable/compliment/none",
  "tone": "playful/sarcastic/witty/serious/none",
  "confidence": 0.0-1.0
}}
"""
```

---

## Probability Gates

```python
RESPONSE_RATES = {
    "funny": 0.90,
    "question": 0.80,
    "hot_take": 0.70,
    "relatable": 0.60,
    "compliment": 0.85,
    "none": 0.30,
}

def should_respond_after_gate(decision: dict) -> bool:
    rate = RESPONSE_RATES.get(decision["reason"], 0.30)
    return random.random() < rate
```

---

## Natural Delay

```python
def get_natural_delay(response: str) -> float:
    base = len(response) / 50  # 50 chars per second
    jitter = random.uniform(0.5, 2.0)
    return min(max(base + jitter, 1.0), 5.0)
```

---

## Integration with Discord Handler

```python
# In message_handler.py:
from skills._social_aware import should_respond, get_natural_delay

async def on_message(message):
    # Skip bot messages
    if message.author.bot:
        return
    
    # Check hard filters
    if hard_filter(message.content):
        return
    
    # LLM decision
    decision = should_respond(message.content, get_context())
    if not decision["respond"]:
        return
    
    # Probability gate
    if not should_respond_after_gate(decision):
        return
    
    # Generate response
    response = await generate_hermes_response(message.content, decision["tone"])
    
    # Natural delay
    delay = get_natural_delay(response)
    await asyncio.sleep(delay)
    
    await message.channel.send(response)
```

---

## Testing

```bash
# Test trigger detection
python3 -c "
from skills._social_aware import should_respond, get_trigger_category

tests = [
    'This game is literally unplayable lol',
    'who wants to play?',
    'ok meeting at 8',
    'lol',
    'this take is wild',
]

for msg in tests:
    result = should_respond(msg, {})
    print(f'{msg[:30]:30} -> {result}')
"
```

---

## Status: IMPLEMENTED (Module Created)

### Completed ✓
- [x] Create `skills/_social_aware.py` - Core decision module
- [x] Hard filter logic (logistics, one-word, DMs)
- [x] Pattern-based trigger detection
- [x] Probability gates
- [x] Natural delay simulation

### Remaining (Integration)
- [ ] Integrate with Discord gateway message handler
- [ ] Add LLM-based decision for ambiguous messages
- [ ] Configure confidence thresholds

---

## Integration (For Future)

The module is ready. To integrate with Discord gateway:

```python
# In Hermes Discord handler (outside this project)
from skills._social_aware import should_respond, get_natural_delay

async def on_message(message):
    decision = await should_respond(message.content)
    
    if not decision["respond"]:
        return  # Skip
    
    # Generate Hermes response...
    response = await generate_hermes_response(
        message.content, 
        tone=decision["tone"]
    )
    
    # Natural delay
    await asyncio.sleep(get_natural_delay(response))
    
    await message.reply(response)
```

### Gateway Location
- File: `~/.hermes/hermes-agent/gateway/platforms/discord.py`
- Function: Look for `on_message` or message handler

---

## Files to Create/Modify

- **Create:** `skills/_social_aware.py`
- **Modify:** Discord message handler
- **Add:** Tests in `tests/test_social_aware.py`

---

## Configuration

```yaml
# config.yaml
social_awareness:
  enabled: true
  hard_filters: true
  probability_gates: true
  min_confidence: 0.5
  max_response_rate: 0.9
```