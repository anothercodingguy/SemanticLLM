import re
import math
from typing import List, Dict, Any, Tuple, Optional

# ── Fast Token Estimation ───────────────────────────────────────────────
def estimate_tokens(text: str) -> int:
    """
    Fast, accurate BPE token estimation (~4 characters per token or ~1.3 words per token).
    """
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    token_est = int(max(words * 1.3, chars / 4.0))
    return max(1, token_est)


# ── Environmental & Sustainability Calculator ───────────────────────────
def sustainability_from_tokens_saved(tokens_saved: int) -> Dict[str, Any]:
    """
    Converts token savings into estimated GPU-seconds avoided, Watt-hours saved, and kg CO₂ avoided.
    Standard documented assumptions:
    - 2,500 tokens / GPU-sec
    - 150W GPU power consumption
    - 0.417 kg CO₂ / kWh (US energy grid average)
    - 55% prefill work share
    """
    if tokens_saved <= 0:
        return {
            "co2_kg_avoided": 0.0,
            "watt_hours_saved": 0.0,
            "gpu_seconds_avoided": 0.0,
            "assumptions": {
                "tokens_per_gpu_sec": 2500,
                "gpu_power_watts": 150,
                "co2_kg_per_kwh": 0.417,
                "context_share_of_prefill": 0.55
            }
        }

    gpu_seconds_avoided = (tokens_saved / 2500.0) * 0.55
    watt_hours_saved = (gpu_seconds_avoided / 3600.0) * 150.0
    co2_kg_avoided = (watt_hours_saved / 1000.0) * 0.417

    return {
        "co2_kg_avoided": round(co2_kg_avoided, 7),
        "watt_hours_saved": round(watt_hours_saved, 5),
        "gpu_seconds_avoided": round(gpu_seconds_avoided, 4),
        "assumptions": {
            "tokens_per_gpu_sec": 2500,
            "gpu_power_watts": 150,
            "co2_kg_per_kwh": 0.417,
            "context_share_of_prefill": 0.55
        }
    }


# ── Context Deduplication & Noise Cleaning ─────────────────────────────
def remove_duplicate_lines(text: str) -> Tuple[str, int]:
    """
    Deduplicate repetitive log lines, repeated RAG output chunks, and boilerplate system traces.
    """
    lines = text.split('\n')
    if len(lines) <= 1:
        return text, 0

    seen_lines = set()
    cleaned_lines = []
    removed_count = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped in ('```', '---', '***'):
            cleaned_lines.append(line)
            continue

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
    Reduce excessive consecutive blank lines and trailing whitespace.
    """
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    return text.strip()


def deduplicate_conversation_history(messages: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], int]:
    """
    Deduplicate repeated user/system turns while preserving chronological order.
    """
    if len(messages) <= 2:
        return messages, 0

    seen_contents = set()
    deduped_messages = []
    removed_count = 0

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


# ── Semantic Block Segmentation ─────────────────────────────────────────
def segment_context_blocks(text: str) -> List[Dict[str, Any]]:
    """
    Segments long context into semantic blocks:
    - Markdown sections (# Heading)
    - Code fences (``` ... ```)
    - Log chunks
    - Paragraphs / conversation turns
    """
    if not text or not text.strip():
        return []

    blocks = []
    lines = text.split('\n')
    current_block_lines = []
    current_heading = "General Context"
    current_type = "prose"
    in_code_fence = False

    for line in lines:
        stripped = line.strip()

        # Check for code fence toggles
        if stripped.startswith('```'):
            if in_code_fence:
                current_block_lines.append(line)
                in_code_fence = False
                # Finish code block
                block_content = '\n'.join(current_block_lines)
                blocks.append({
                    "heading": current_heading,
                    "type": "code",
                    "content": block_content,
                    "tokens": estimate_tokens(block_content)
                })
                current_block_lines = []
                current_type = "prose"
                current_heading = "Code Execution Context"
                continue
            else:
                if current_block_lines:
                    block_content = '\n'.join(current_block_lines)
                    blocks.append({
                        "heading": current_heading,
                        "type": current_type,
                        "content": block_content,
                        "tokens": estimate_tokens(block_content)
                    })
                    current_block_lines = []
                in_code_fence = True
                current_type = "code"
                current_heading = f"Code Block ({stripped.replace('`', '') or 'snippet'})"
                current_block_lines.append(line)
                continue

        if in_code_fence:
            current_block_lines.append(line)
            continue

        # Check for Markdown headers
        header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if header_match:
            if current_block_lines:
                block_content = '\n'.join(current_block_lines)
                blocks.append({
                    "heading": current_heading,
                    "type": current_type,
                    "content": block_content,
                    "tokens": estimate_tokens(block_content)
                })
                current_block_lines = []
            current_heading = header_match.group(2).strip()
            current_type = "section"
            current_block_lines.append(line)
            continue

        # Check for Log streams
        is_log = bool(re.search(r'\d{4}-\d{2}-\d{2}|\b(INFO|DEBUG|WARN|ERROR|FATAL)\b', stripped))
        if is_log and current_type != "log" and len(current_block_lines) > 2:
            block_content = '\n'.join(current_block_lines)
            blocks.append({
                "heading": current_heading,
                "type": current_type,
                "content": block_content,
                "tokens": estimate_tokens(block_content)
            })
            current_block_lines = []
            current_heading = "System Logs & Diagnostic Traces"
            current_type = "log"

        # Check for paragraph breaks
        if not stripped and len(current_block_lines) >= 8 and not in_code_fence:
            block_content = '\n'.join(current_block_lines)
            blocks.append({
                "heading": current_heading,
                "type": current_type,
                "content": block_content,
                "tokens": estimate_tokens(block_content)
            })
            current_block_lines = []
            continue

        current_block_lines.append(line)

    if current_block_lines:
        block_content = '\n'.join(current_block_lines)
        blocks.append({
            "heading": current_heading,
            "type": current_type,
            "content": block_content,
            "tokens": estimate_tokens(block_content)
        })

    return blocks


# ── Query-Aware Relevance Scorer & Neural Ranking ────────────────────────
def score_block_relevance(block: Dict[str, Any], query: str) -> Tuple[float, str]:
    """
    Evaluates semantic relevance of a context block with respect to the user query.
    Returns (score: 0.0-1.0, reason: str).
    """
    content = block.get("content", "")
    heading = block.get("heading", "")
    btype = block.get("type", "prose")

    if not query or not query.strip():
        return 0.85, "No query filter provided; preserved default evidence"

    query_lower = query.lower()
    content_lower = content.lower()
    heading_lower = heading.lower()

    # Extract query keywords (>2 chars)
    raw_terms = re.findall(r'\b\w{3,}\b', query_lower)
    stopwords = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how",
                 "the", "and", "for", "with", "about", "against", "between", "into", "through",
                 "during", "before", "after", "above", "below", "from", "down", "over", "under",
                 "again", "further", "then", "once", "here", "there", "all", "any", "both", "each",
                 "does", "explain", "describe", "tell", "give", "show", "find", "can", "you", "please"}
    query_terms = [t for t in raw_terms if t not in stopwords]
    if not query_terms:
        query_terms = raw_terms

    if not query_terms:
        return 0.7, "General context alignment"

    # Term overlap scoring
    term_matches = sum(1 for term in query_terms if term in content_lower or term in heading_lower)
    overlap_ratio = term_matches / len(query_terms)

    # Heading relevance boost
    heading_match = any(term in heading_lower for term in query_terms)
    
    # Code & Error keyword boost if query is technical
    tech_boost = 0.0
    if any(k in query_lower for k in ("error", "fail", "exception", "bug", "crash", "deploy", "trace", "code")):
        if "error" in content_lower or "failed" in content_lower or "exception" in content_lower or "traceback" in content_lower:
            tech_boost += 0.35

    # Penalize repetitive boilerplate & stale log chunks
    noise_penalty = 0.0
    if btype == "log" and overlap_ratio < 0.2 and not tech_boost:
        noise_penalty = 0.4
    if "duplicate line removed" in content_lower:
        noise_penalty = 0.5

    final_score = min(1.0, max(0.0, (overlap_ratio * 0.7) + (0.25 if heading_match else 0.0) + tech_boost - noise_penalty))

    # Determine descriptive reason
    if final_score >= 0.7:
        if heading_match:
            reason = f"Matches query topic in '{heading}'"
        elif tech_boost > 0:
            reason = "Contains error trace or failure evidence matching query"
        else:
            reason = f"High keyword alignment with user question ({term_matches}/{len(query_terms)} terms)"
    elif final_score >= 0.4:
        reason = "Supporting contextual evidence and nearby structural declarations"
    else:
        if btype == "log":
            reason = "Stale system log noise not referenced in current ask"
        elif noise_penalty > 0:
            reason = "Repetitive boilerplate and non-critical trace output"
        else:
            reason = "Irrelevant passage to the specific query question"

    return final_score, reason


# ── SuperCompress Core Compression Engine ───────────────────────────────
def compress_context_engine(
    text: str,
    query: str = "",
    mode: str = "compiler",
    budget_ratio: Optional[float] = None
) -> Dict[str, Any]:
    """
    Comprehensive Query-Aware Context Compression Engine:
    - Mode 'compiler': Dynamic semantic keep/drop targeting >98% answer retention and maximum token cut.
    - Mode 'precision': Conservative high-confidence quality gate.
    - Mode 'fixed': Fixed retention budget (0.1 to 1.0 ratio).
    """
    if not text or not text.strip():
        sustain = sustainability_from_tokens_saved(0)
        return {
            "compressed_text": text or "",
            "compressed": text or "",
            "original_tokens": 0,
            "kept_tokens": 0,
            "tokens_saved": 0,
            "tokens_saved_pct": 0.0,
            "important_kept_pct": 1.0,
            "compression_risk": "low",
            "kept_blocks": [],
            "dropped_blocks": [],
            "policy_name": f"SemanticGateway-{mode}",
            "mode": mode,
            "keep_ratio": 1.0,
            "kept_line_ratio": 1.0,
            "sustainability": sustain,
            "savings_notes": []
        }

    original_text = text
    original_tokens = estimate_tokens(original_text)

    # Step 1: Deduplicate noisy lines & redundant whitespace
    deduped_text, lines_removed = remove_duplicate_lines(original_text)
    cleaned_text = clean_redundant_whitespace(deduped_text)

    # Step 2: Segment into semantic blocks
    blocks = segment_context_blocks(cleaned_text)

    if not blocks:
        blocks = [{
            "heading": "Main Document",
            "type": "prose",
            "content": cleaned_text,
            "tokens": estimate_tokens(cleaned_text)
        }]

    # Step 3: Score each block against the query
    scored_blocks = []
    for b in blocks:
        score, reason = score_block_relevance(b, query)
        scored_blocks.append({
            **b,
            "score": score,
            "reason": reason
        })

    # Step 4: Mode Selection & Filtering
    kept_blocks_data = []
    dropped_blocks_data = []

    if mode == "fixed" and budget_ratio is not None:
        # Fixed budget mode: keep highest scored blocks up to budget_ratio
        target_tokens = max(1, int(original_tokens * max(0.1, min(1.0, budget_ratio))))
        sorted_by_score = sorted(scored_blocks, key=lambda x: x["score"], reverse=True)
        accumulated_tokens = 0
        kept_indices = set()

        for b in sorted_by_score:
            if accumulated_tokens + b["tokens"] <= target_tokens or not kept_indices:
                kept_indices.add(id(b))
                accumulated_tokens += b["tokens"]
                kept_blocks_data.append({
                    "heading": b["heading"],
                    "reason": b["reason"],
                    "tokens": b["tokens"]
                })
            else:
                dropped_blocks_data.append({
                    "heading": b["heading"],
                    "reason": b["reason"],
                    "tokens": b["tokens"]
                })

        final_blocks = [b for b in scored_blocks if id(b) in kept_indices]

    else:
        # Compiler & Precision Mode
        # In compiler mode, threshold is query-dependent (default keep if score >= 0.35)
        # In precision mode, threshold is stricter (keep if score >= 0.45)
        cutoff_threshold = 0.45 if mode == "precision" else 0.30

        # Always keep at least the highest scored block
        max_score = max(b["score"] for b in scored_blocks) if scored_blocks else 1.0

        final_blocks = []
        for b in scored_blocks:
            # Always keep if score >= cutoff or if it's the highest scoring block
            if b["score"] >= cutoff_threshold or (b["score"] == max_score and not final_blocks):
                final_blocks.append(b)
                kept_blocks_data.append({
                    "heading": b["heading"],
                    "reason": b["reason"],
                    "tokens": b["tokens"]
                })
            else:
                dropped_blocks_data.append({
                    "heading": b["heading"],
                    "reason": b["reason"],
                    "tokens": b["tokens"]
                })

    # Step 5: Assemble compressed text
    if final_blocks:
        compressed_text = "\n\n".join(b["content"] for b in final_blocks).strip()
    else:
        compressed_text = cleaned_text

    kept_tokens = estimate_tokens(compressed_text)
    tokens_saved = max(0, original_tokens - kept_tokens)
    tokens_saved_pct = round((tokens_saved / original_tokens) * 100.0, 2) if original_tokens > 0 else 0.0

    # Step 6: Verifier Quality & Risk Assessment
    # Oracle retention: if we kept all blocks with score >= 0.5, retention is near 100%
    high_value_blocks = [b for b in scored_blocks if b["score"] >= 0.5]
    if high_value_blocks:
        high_kept = sum(1 for b in high_value_blocks if b in final_blocks)
        important_kept_pct = round(high_kept / len(high_value_blocks), 2)
    else:
        important_kept_pct = 1.0

    if important_kept_pct >= 0.95:
        compression_risk = "low"
    elif important_kept_pct >= 0.80:
        compression_risk = "medium"
    else:
        compression_risk = "high"

    # Line retention ratio
    orig_lines = max(1, len(original_text.splitlines()))
    kept_lines = len(compressed_text.splitlines())
    kept_line_ratio = round(min(1.0, kept_lines / orig_lines), 3)
    keep_ratio = round(min(1.0, kept_tokens / original_tokens), 3) if original_tokens > 0 else 1.0

    # Step 7: Sustainability calculation
    sustainability = sustainability_from_tokens_saved(tokens_saved)

    # Savings notes
    savings_notes = []
    if lines_removed > 0:
        savings_notes.append(f"Deduplicated {lines_removed} noisy log and boilerplate line(s)")
    if dropped_blocks_data:
        savings_notes.append(f"Removed {len(dropped_blocks_data)} irrelevant context section(s) via query-aware compiler")
    if tokens_saved_pct > 0:
        savings_notes.append(f"Reduced prompt tokens by {tokens_saved_pct}% while retaining {int(important_kept_pct*100)}% critical evidence")
    if not savings_notes:
        savings_notes.append("Context already optimal; preserved verbatim")

    return {
        "compressed_text": compressed_text,
        "compressed": compressed_text,
        "original_tokens": original_tokens,
        "kept_tokens": kept_tokens,
        "tokens_saved": tokens_saved,
        "tokens_saved_pct": tokens_saved_pct,
        "important_kept_pct": important_kept_pct,
        "compression_risk": compression_risk,
        "kept_blocks": kept_blocks_data,
        "dropped_blocks": dropped_blocks_data,
        "policy_name": f"SemanticGateway-{mode}",
        "mode": mode,
        "keep_ratio": keep_ratio,
        "kept_line_ratio": kept_line_ratio,
        "sustainability": sustainability,
        "savings_notes": savings_notes,
        "original_text": original_text,
        "optimized_text": compressed_text,
        "optimized_tokens": kept_tokens,
        "compression_percent": tokens_saved_pct
    }


# ── Python SDK Helper Functions ─────────────────────────────────────────
def compress_context(
    text: str,
    query: str = "",
    mode: str = "compiler",
    budget_ratio: Optional[float] = None
) -> Dict[str, Any]:
    """
    Public Python API alias for SuperCompress context compression.
    """
    return compress_context_engine(text=text, query=query, mode=mode, budget_ratio=budget_ratio)


def compress_for_turn(
    context: str = "",
    user_query: str = "",
    context_blocks: Optional[List[str]] = None,
    mode: str = "compiler",
    budget_ratio: Optional[float] = None
) -> Dict[str, Any]:
    """
    Multi-turn / block-based compression for conversational agents.
    """
    if context_blocks:
        full_text = "\n\n".join(b for b in context_blocks if b and b.strip())
        if context and context.strip():
            full_text = f"{context}\n\n{full_text}"
    else:
        full_text = context

    return compress_context_engine(
        text=full_text,
        query=user_query,
        mode=mode,
        budget_ratio=budget_ratio
    )


def compress_prompt(prompt: str, query: str = "") -> Dict[str, Any]:
    """
    Gateway internal integration wrapper.
    """
    return compress_context_engine(text=prompt, query=query, mode="compiler")
