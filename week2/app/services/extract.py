from __future__ import annotations

import os
import re
import json
from ollama import chat
from dotenv import load_dotenv

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False

def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


def extract_action_items(text: str) -> list[str]:
    lines = text.splitlines()
    extracted: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique



def extract_action_items_llm(text: str, model: str = "llama3.1:8b") -> list[str]:
    response = chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an action item extractor. "
                    "Given a text, identify concrete tasks or to-dos that someone needs to do. "
                    "Respond with ONLY a JSON object in this exact format: "
                    '{"action_items": ["item1", "item2", ...]}. '
                    "If there are no action items, respond with: "
                    '{"action_items": []}.'
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        format="json",
    )
    content = response["message"]["content"]
    parsed = json.loads(content)
    print(parsed)
    return parsed.get("action_items", [])


if __name__ == "__main__":
    # sample = """
    #     - buy milk
    # - call john
    # todo: finish homework
    # [ ] clean the house
    # Fix the login bug. Update the README.
    # """

    sample = """
The minutes can be largely divided into three parts: top, middle, and bottom. 

At the top, the information about the meeting should be written. Please fill out all the detailed information such as meeting date, participant, meeting place, and meeting topic.

* If there are multiple topics, it is essential to write them correctly! 

The meeting should be written in the middle. Please write your opinions and contents in the order of the agenda you wrote at the top. There are many stories coming and going, so concentration is essential! Please organize it so that it is easy to understand.

* If you record the contents of the meeting in advance, you can make up for the parts you missed or confused while writing, so you can review them more thoroughly.

At the bottom, write down the key decisions and actions so you can finish.

In short, the conclusion of the meeting should be written. The person in charge of the assignments, the deadline for completing the assignments, and the details of the assignments should be written together. If the details are not clear, you should be careful because they may be pushed out of priorities and slow or delayed.

Writer earns more money than me
fix: fixin.g a fi.x
fix fix a. fix
"""

    results = extract_action_items(sample)
    results = extract_action_items_llm(sample)
    for i, item in enumerate(results, 1):
        print(f"{i} - {item}")

