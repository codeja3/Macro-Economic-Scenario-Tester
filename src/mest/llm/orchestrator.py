"""Orchestrator for local Ollama LLM integration.

This module implements the cognitive architecture reasoning loop, including:
1. Decomposed query parsing (for queries > 50 tokens).
2. Chain of Thought (CoT) system prompt injection.
3. Self-Reflection (SR) verification.
4. Asynchronous streaming of structured chunks (thoughts, reflections, responses).
"""

import json
from typing import Any, Generator
import requests


def decompose_query(query: str, model: str = "llama3") -> list[str]:
    """Decomposes a complex query into a list of individual sub-questions.

    Args:
        query: The user query string.
        model: The local Ollama model to use.

    Returns:
        A list of sub-questions.
    """
    decomp_prompt = (
        "You are a financial analysis assistant. Decompose the following complex retirement query "
        "into a clean list of individual, specific, actionable sub-questions that need to be answered. "
        "Provide ONLY the numbered list of sub-questions, nothing else. "
        "Do not write any introductory or concluding text.\n\n"
        f"Query: {query}"
    )

    payload = {
        "model": model,
        "prompt": decomp_prompt,
        "stream": False,
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        response_text = data.get("response", "")
    except Exception:
        # Fallback to the original query if Ollama call fails
        return [query]

    # Parse numbered list of sub-questions
    sub_questions = []
    for line in response_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Check if line starts with a digit followed by a dot or is a list item
        if line[0].isdigit() or line.startswith("-") or line.startswith("*"):
            # Try splitting by dot for numbered list
            parts = line.split(".", 1)
            if len(parts) > 1 and parts[0].strip().isdigit():
                sub_questions.append(parts[1].strip())
            else:
                sub_questions.append(line.lstrip("-* ").strip())

    # Fallback to original query if parser fails to find sub-questions
    return sub_questions if sub_questions else [query]


def parse_tokens(response_stream: Generator[str, None, None]) -> Generator[dict[str, str], None, None]:
    """Parses a stream of text tokens and yields structured chunks based on XML tags.

    Args:
        response_stream: A generator yielding text tokens as they stream from Ollama.

    Yields:
        Dictionaries containing "type" (thought, reflection, or response) and
        "content" (token chunk).
    """
    state = "response"  # Default fallback state
    buffer = ""
    safe_buffer_len = 15  # Buffer size to prevent splitting a tag (e.g. "</reflection>")

    for token in response_stream:
        buffer += token

        # Check for state transitions (tags)
        if "<thought>" in buffer:
            parts = buffer.split("<thought>", 1)
            if parts[0]:
                yield {"type": state, "content": parts[0]}
            state = "thought"
            buffer = parts[1]
            
        elif "<reflection>" in buffer:
            parts = buffer.split("<reflection>", 1)
            if parts[0]:
                yield {"type": state, "content": parts[0]}
            state = "reflection"
            buffer = parts[1]
            
        elif "<response>" in buffer:
            parts = buffer.split("<response>", 1)
            if parts[0]:
                yield {"type": state, "content": parts[0]}
            state = "response"
            buffer = parts[1]
            
        elif "</thought>" in buffer:
            parts = buffer.split("</thought>", 1)
            if parts[0]:
                yield {"type": state, "content": parts[0]}
            state = "response"  # Fallback to response after thought
            buffer = parts[1]
            
        elif "</reflection>" in buffer:
            parts = buffer.split("</reflection>", 1)
            if parts[0]:
                yield {"type": state, "content": parts[0]}
            state = "response"  # Fallback to response after reflection
            buffer = parts[1]
            
        elif "</response>" in buffer:
            parts = buffer.split("</response>", 1)
            if parts[0]:
                yield {"type": state, "content": parts[0]}
            state = "response"
            buffer = parts[1]
            
        else:
            # Yield safe prefix of buffer to keep stream fluid
            if len(buffer) > safe_buffer_len:
                yield {"type": state, "content": buffer[:-safe_buffer_len]}
                buffer = buffer[-safe_buffer_len:]

    # Yield whatever is left in the buffer at the end
    if buffer:
        yield {"type": state, "content": buffer}


def stream_cot_sr(prompt: str, stats: dict[str, Any], model: str = "llama3") -> Generator[dict[str, str], None, None]:
    """Sends prompt and stats to Ollama and yields parsed thought/reflection/response tokens.

    Args:
        prompt: The specific sub-question or user query.
        stats: Dictionary of simulation result metrics.
        model: Local Ollama model name.

    Yields:
        Structured chunks with "type" and "content".
    """
    system_prompt = (
        "You are an expert economic and financial analysis assistant for MEST (Macro-Economic Scenario Tester). "
        "Analyze the user's decumulation strategy based on the simulation statistics.\n\n"
        "You MUST format your analysis exactly using XML tags in the following sequence:\n"
        "1. Open a `<thought>` block and output your step-by-step mathematical, economic, and logical deductions.\n"
        "2. Close the `</thought>` block.\n"
        "3. Open a `<reflection>` block and review your deductions for any arithmetic errors, economic fallacies, "
        "or contradictions, making corrections if needed.\n"
        "4. Close the `</reflection>` block.\n"
        "5. Open a `<response>` block and write your plain-English translation and final summary of findings.\n"
        "6. Close the `</response>` block.\n\n"
        "Example format:\n"
        "<thought>Step-by-step thinking...</thought>\n"
        "<reflection>Review and correction...</reflection>\n"
        "<response>Final plain-English findings...</response>"
    )

    user_prompt = (
        f"Simulation Stats:\n{json.dumps(stats, indent=2)}\n\n"
        f"User Question: {prompt}"
    )

    payload = {
        "model": model,
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "stream": True,
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, stream=True, timeout=30)
        response.raise_for_status()
    except Exception as e:
        # Graceful fallback: yield error message as response content
        yield {"type": "response", "content": f"Failed to connect to local Ollama instance: {e}"}
        return

    # Inner generator yielding raw strings
    def raw_token_generator() -> Generator[str, None, None]:
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode("utf-8"))
                    yield chunk.get("response", "")
                except Exception:
                    continue

    # Pipe raw strings through token tag parser
    yield from parse_tokens(raw_token_generator())


def generate_analysis_stream(prompt: str, stats: dict[str, Any], model: str = "llama3") -> Generator[dict[str, str], None, None]:
    """Main orchestrator entry point. Streams analysis for both short and long queries.

    Args:
        prompt: The user query string.
        stats: Dictionary of simulation result metrics.
        model: Local Ollama model name.

    Yields:
        Structured chunks containing type (sub_question, thought, reflection, response)
        and content.
    """
    # Token check: Decompose if query is > 50 tokens (words)
    tokens = prompt.split()
    if len(tokens) > 50:
        sub_questions = decompose_query(prompt, model=model)
        for sq in sub_questions:
            yield {"type": "sub_question", "content": sq}
            yield from stream_cot_sr(sq, stats, model=model)
    else:
        yield from stream_cot_sr(prompt, stats, model=model)
