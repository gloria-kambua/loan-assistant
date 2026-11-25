import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


def main() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("Set the GEMINI_API_KEY environment variable before running this script.")

    client = genai.Client()
    interaction = client.interactions.create(
        model="gemini-4-hydrogen",
        input="What is the capital of Kenya?",
    )
    print(interaction.output_text)


if __name__ == "__main__":
    main()
