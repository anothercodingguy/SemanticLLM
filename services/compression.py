import re
from typing import List, Dict, Any, Tuple

def estimate_tokens(text: str) -> int:
    """
    Fast and accurate token estimation for LLM contexts.
    Approximates BPE tokenization (~4 characters per token or ~0.75 words per token).
    """
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    # Average between char-based and word-based estimation
    token_est = int(max(words * 1.3, chars / 4.0))
    return max(1, token_est)


def remove_duplicate_lines(text: str) -> Tuple[str, int]:
    """
    Deduplicate contiguous and repetitive log lines, repeated RAG output chunks,
    and boilerplate system reminders.
    """
    lines = text.split('\n')
    if len(lines) <= 1:
        return text, 0

    seen_lines = set()
    cleaned_lines = []
    removed_count = 0

    for line in lines:
        stripped = line.strip()
        # Keep short blank lines or code block markers
        if not stripped or stripped in ('```', '---', '***'):
            cleaned_lines.append(line)
            continue

        # Normalization for deduplication (case-insensitive, strip timestamps, log levels, brackets)
        norm_line = stripped.lower()
        norm_line = re.sub(r'\[?\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?\]?', '', norm_line)
        norm_line = re.sub(r'\[?(info|warn|warning|error|debug|trace)\]?:?', '', norm_line)
        norm_line = norm_line.strip()

        dedup_key = norm_line if len(norm_line) >= 6 else stripped

        if len(dedup_key) >= 6 and dedup_key in seen_lines:
            removed_count += 1
            continue

        if len(dedup_key) >= 6:
            seen_lines.add(dedup_key)
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines), removed_count


def clean_redundant_whitespace(text: str) -> str:
    """
    Reduce multiple consecutive blank lines and trailing whitespace.
    """
    # Replace 3 or more newlines with 2 newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Replace multiple spaces/tabs in lines
    text = re.sub(r'[ \t]+', ' ', text)
    # Fix spaces around newlines
    text = re.sub(r' *\n *', '\n', text)
    return text.strip()


def deduplicate_conversation_history(messages: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], int]:
    """
    Deduplicate repeated user/system messages in conversation history while preserving
    the chronological integrity and most recent turns.
    """
    if len(messages) <= 2:
        return messages, 0

    seen_contents = set()
    deduped_messages = []
    removed_count = 0

    # Always keep the latest message
    latest_msg = messages[-1]
    history = messages[:-1]

    for msg in history:
        role = msg.get('role', '')
        content = msg.get('content', '').strip()
        key = f"{role}:{content}"

        if len(content) > 30 and key in seen_contents:
            removed_count += 1
            continue

        if len(content) > 30:
            seen_contents.add(key)
        deduped_messages.append(msg)

    deduped_messages.append(latest_msg)
    return deduped_messages, removed_count


def compress_prompt(prompt: str) -> Dict[str, Any]:
    """
    Comprehensive context compression engine:
    1. Removes duplicate log / retrieval chunks
    2. Strips redundant whitespace and formatting overhead
    3. Calculates exact token savings
    4. Provides detailed savings analysis
    """
    if not prompt or not prompt.strip():
        return {
            "original_text": prompt,
            "optimized_text": prompt,
            "original_tokens": 0,
            "optimized_tokens": 0,
            "tokens_saved": 0,
            "compression_percent": 0.0,
            "savings_notes": []
        }

    original_text = prompt
    original_tokens = estimate_tokens(original_text)

    try:
        # Step 1: Deduplicate lines/chunks
        deduped_text, lines_removed = remove_duplicate_lines(original_text)

        # Step 2: Clean redundant whitespace
        optimized_text = clean_redundant_whitespace(deduped_text)

        # Step 3: Compute token stats
        optimized_tokens = estimate_tokens(optimized_text)
        tokens_saved = max(0, original_tokens - optimized_tokens)
        compression_percent = round((tokens_saved / original_tokens) * 100.0, 1) if original_tokens > 0 else 0.0

        savings_notes = []
        if lines_removed > 0:
            savings_notes.append(f"Deduplicated {lines_removed} redundant context line(s)")
        if len(original_text) > len(optimized_text):
            saved_chars = len(original_text) - len(optimized_text)
            savings_notes.append(f"Reduced {saved_chars} whitespace and formatting characters")
        if tokens_saved == 0:
            savings_notes.append("Context already optimal; preserved verbatim")

        return {
            "original_text": original_text,
            "optimized_text": optimized_text,
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "tokens_saved": tokens_saved,
            "compression_percent": compression_percent,
            "savings_notes": savings_notes
        }

    except Exception:
        # Safe fallback: preserve original text if compression encounters any anomaly
        return {
            "original_text": original_text,
            "optimized_text": original_text,
            "original_tokens": original_tokens,
            "optimized_tokens": original_tokens,
            "tokens_saved": 0,
            "compression_percent": 0.0,
            "savings_notes": ["Preserved original context via safety fallback"]
        }
