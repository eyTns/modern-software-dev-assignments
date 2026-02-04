import os
import re
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
# (disclaimer: got help from claude code)
YOUR_SYSTEM_PROMPT = """
You are a mathematician solving modular exponentiation problems step by step using Euler's theorem.

Here are some examples:

Example 1:
Problem: what is 7^35 (mod 12)?
Solution:
I'll use Euler's theorem. First find φ(12):
12 = 4 × 3 = 2^2 × 3
φ(12) = φ(2^2) × φ(3) = 2 × 2 = 4

Since gcd(7, 12) = 1:
7^4 ≡ 1 (mod 12)

Now divide the exponent:
35 = 4 × 8 + 3

So: 7^35 = (7^4)^8 × 7^3 ≡ 1 × 7^3 (mod 12)

Calculate 7^3:
7^1 = 7
7^2 = 49 ≡ 1 (mod 12)
7^3 = 7 × 1 = 7 (mod 12)

Answer: 7

Example 2:
Problem: what is 11^123 (mod 20)?
Solution:
I'll use Euler's theorem. First find φ(20):
20 = 4 × 5 = 2^2 × 5
φ(20) = φ(2^2) × φ(5) = 2 × 4 = 8

Since gcd(11, 20) = 1:
11^8 ≡ 1 (mod 20)

Now divide the exponent:
123 = 8 × 15 + 3

So: 11^123 = (11^8)^15 × 11^3 ≡ 1 × 11^3 (mod 20)

Calculate 11^3:
11^1 = 11
11^2 = 121 ≡ 1 (mod 20)
11^3 = 11 × 1 = 11 (mod 20)

Answer: 11

Example 3:
Problem: what is 13^456 (mod 30)?
Solution:
I'll use Euler's theorem. First find φ(30):
30 = 2 × 3 × 5
φ(30) = φ(2) × φ(3) × φ(5) = 1 × 2 × 4 = 8

Since gcd(13, 30) = 1:
13^8 ≡ 1 (mod 30)

Now divide the exponent:
456 = 8 × 57 + 0

So: 13^456 = (13^8)^57 × 13^0 ≡ 1 × 1 = 1 (mod 30)

Answer: 1

Now solve the given problem using the same step-by-step approach.
"""


USER_PROMPT = """
Solve this problem, then give the final answer on the last line as "Answer: <number>".

what is 3^{12345} (mod 100)?
"""


# For this simple example, we expect the final numeric answer only
EXPECTED_OUTPUT = "Answer: 43"


def extract_final_answer(text: str) -> str:
    """Extract the final 'Answer: ...' line from a verbose reasoning trace.

    - Finds the LAST line that starts with 'Answer:' (case-insensitive)
    - Normalizes to 'Answer: <number>' when a number is present
    - Falls back to returning the matched content if no number is detected
    """
    matches = re.findall(r"(?mi)^\s*answer\s*:\s*(.+)\s*$", text)
    if matches:
        value = matches[-1].strip()
        # Prefer a numeric normalization when possible (supports integers/decimals)
        num_match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if num_match:
            return f"Answer: {num_match.group(0)}"
        return f"Answer: {value}"
    return text.strip()


def test_your_prompt(system_prompt: str) -> bool:
    """Run up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.3},
        )
        output_text = response.message.content
        final_answer = extract_final_answer(output_text)
        if final_answer.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {final_answer}")
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)


