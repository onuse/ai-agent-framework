# Reasoning Model Support

## Overview

The AI Agent Framework includes built-in support for **reasoning models** that output their complete chain of thought before providing the final answer.

## What are Reasoning Models?

Reasoning models (like GPT-OSS:120b, o1, etc.) work differently from standard language models:

1. **Standard Model**: Outputs the final answer directly
2. **Reasoning Model**: Outputs thinking process → marker → final answer

Example output from a reasoning model:
```
Let me analyze this step by step.
First, I need to consider the requirements...
After evaluating all options...
The best approach would be...
<|start|>assistant<|channel|>final<|message|>
Here is my final answer: The solution is to use X approach because...
```

## Automatic Extraction

The framework **automatically handles** this for you:

### Without Extraction (Raw Output)
```
[300 chars of reasoning]
<|start|>assistant<|channel|>final<|message|>
The final answer is 42.
```

### With Extraction (What Agents Receive)
```
The final answer is 42.
```

## How It Works

The `LLMClient` class post-processes all API responses:

1. **Check for marker**: Looks for `<|start|>assistant<|channel|>final<|message|>`
2. **Extract content**: Takes everything after the marker
3. **Clean up**: Removes any end markers like `<|end|>` or `<|endoftext|>`
4. **Return**: Agents receive only the final answer

This happens **transparently** - no changes needed in agent code.

## Configuration

### Enable/Disable Extraction

In `config.py`:
```python
# Enable automatic extraction (default: True)
EXTRACT_FINAL_ANSWER = True

# Disable to get raw output with reasoning
EXTRACT_FINAL_ANSWER = False
```

Or via environment variable:
```bash
export EXTRACT_FINAL_ANSWER="false"
```

### Custom Marker

If your reasoning model uses a different marker:

```python
# In config.py
FINAL_ANSWER_MARKER = "<your_custom_marker>"
```

Or via environment:
```bash
export FINAL_ANSWER_MARKER="<your_custom_marker>"
```

## Testing

Verify extraction works correctly:

```bash
python test_reasoning_extraction.py
```

This tests:
- Extraction with marker present
- No extraction when marker absent
- End marker cleanup
- Disabling extraction

## Benefits

1. **No Code Changes**: Agents don't need reasoning model awareness
2. **Clean Responses**: Only relevant content reaches agents
3. **Configurable**: Easy to enable/disable or change markers
4. **Transparent**: Framework handles complexity automatically
5. **Debuggable**: Flag in response indicates if extraction happened

## Response Format

The LLMClient includes a flag to indicate extraction:

```python
response = client.chat(messages=[...])

# Check if reasoning was extracted
if response.get('reasoning_extracted', False):
    print("Response was from reasoning model and extracted")
```

## Supported Markers

Default marker:
```
<|start|>assistant<|channel|>final<|message|>
```

Auto-cleaned end markers:
- `<|end|>`
- `<|endoftext|>`
- `<|eot_id|>`

## When to Disable Extraction

You might want to see the full reasoning for:
- **Debugging**: Understanding model's thought process
- **Research**: Analyzing how the model reaches conclusions
- **Transparency**: Showing users the reasoning
- **Development**: Testing prompt effectiveness

Simply set `EXTRACT_FINAL_ANSWER = False` in config.py.

## Example: GPT-OSS:120b

Your current setup uses GPT-OSS:120b at http://192.168.1.95:8000/v1:

```python
# config.py (current configuration)
LLM_PROVIDER = "openai"
LLM_MODEL = "llama3.1:8b"
OPENAI_BASE_URL = "http://192.168.1.95:8000/v1"
EXTRACT_FINAL_ANSWER = True
FINAL_ANSWER_MARKER = "<|start|>assistant<|channel|>final<|message|>"
```

With this configuration:
- All API calls go to your GPT-OSS:120b server
- Reasoning chain of thought is automatically removed
- Agents receive clean, concise final answers
- Framework works exactly as if using a non-reasoning model

## Implementation Details

The extraction logic in `llm_client.py`:

```python
def _extract_final_answer_from_reasoning(self, content: str) -> str:
    """Extract final answer from reasoning model output."""

    if not self.extract_final_answer or not self.final_answer_marker:
        return content

    if self.final_answer_marker in content:
        marker_pos = content.find(self.final_answer_marker)
        final_answer = content[marker_pos + len(self.final_answer_marker):].strip()

        # Clean up end markers
        for end_marker in ["<|end|>", "<|endoftext|>", "<|eot_id|>"]:
            if end_marker in final_answer:
                final_answer = final_answer.split(end_marker)[0].strip()

        return final_answer

    return content
```

This method is called automatically for every API response before returning to agents.

## Troubleshooting

**Agents receiving reasoning text**
- Check `EXTRACT_FINAL_ANSWER = True` in config.py
- Verify marker matches your model's output
- Run `python test_reasoning_extraction.py`

**Final answers seem incomplete**
- Check if your model uses a different end marker
- Try disabling extraction to see raw output
- Add your model's end marker to the cleanup list

**Want to see reasoning for debugging**
- Set `EXTRACT_FINAL_ANSWER = False` temporarily
- Re-run your test
- Re-enable when done debugging

---

**The framework is pre-configured for GPT-OSS:120b!** No changes needed - it works out of the box.
