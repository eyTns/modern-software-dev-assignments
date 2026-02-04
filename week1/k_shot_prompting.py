import os
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
# (disclaimer: got help from claude code and gemini. not success.)
YOUR_SYSTEM_PROMPT = """
You are a reversal machine. Your ONLY task is to output the input word reversed, character by character.
Ignore the meaning of the word. Treat it as a raw string of letters.

<examples>
Q: ruuuuuuuuu
A: uuuuuuuuur

Q: rrdrrrrrrr
A: rrrrrrrdrr

Q: ssssshssss
A: sssshsssss

Q: jjjjjjjsjj
A: jjsjjjjjjj

Q: aaaaaaaawa
A: awaaaaaaaa

Q: loveattack
A: kcattaevol

Q: javascript
A: tpircsavaj

Q: strawberry
A: yrrebwarts

Q: netscanner
A: rennacsnet

Q: cyberpower
A: rewoprebyc

Q: ppomodoroo
A: oorodomopp

Q: strawberry
A: yrrebwarts

Q: apttusausa
A: asuasuttpa

Q: xmlparser
A: resraplmx

Q: ftpserver
A: revresptf

Q: sslcertificate
A: etacifitreclss

Q: htmlbody
A: ydoblmth

Q: jsonresponse
A: esnopsernosj

Q: statuscode
A: edocsutats
</examples>
"""



USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"

def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="mistral-nemo:12b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.5},
        )
        output_text = response.message.content.strip()
        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False

if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)