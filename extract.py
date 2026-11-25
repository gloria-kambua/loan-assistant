"""Extract structured loan applications from plain-text field notes."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError

from models import LoanApplication


# Fictional input used only to exercise the extraction prototype.
FAKE_APPLICATION = """
Field officer notes: Mary Wanjiku is applying for an individual loan of KES 120,000
for purchase of shop inventory. Her stated monthly income is 45,000. She has named
Peter Otieno as her guarantor.
"""


def extract(text: str) -> LoanApplication | None:
    """Ask Gemini to extract an application and validate its response with Pydantic."""

    # load_dotenv makes a local .env file available through os.environ.
    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GEMINI_API_KEY in the environment or in a local .env file."
        )

    # The client reads API credentials; the model can be overridden without code edits.
    client = genai.Client(api_key=api_key)
    # Use the replacement named by Gemini when the older model is unavailable.
    model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

    prompt = f"""
Extract the loan application as JSON. Do not approve or reject it and do not infer
values that are not stated. Use "individual" or "group" for loan_type. Omit optional
fields rather than inventing values. Return only JSON matching the provided schema.

Application text:
{text}
""".strip()

    # JSON mode plus the Pydantic-generated schema constrains the model's output shape.
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=LoanApplication.model_json_schema(),
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    # Printing the raw result makes model output differences easy to inspect.
    print("Raw response:")
    print(response.text)

    if not response.text:
        print("No JSON content was returned by the model.")
        return None

    # Pydantic is the final validation boundary before application data is used.
    try:
        return LoanApplication.model_validate_json(response.text)
    except ValidationError as error:
        print("The model response failed validation:")
        print(error)
        return None


if __name__ == "__main__":
    # Run the complete extraction flow on the fictional field-note example.
    extracted_application = extract(FAKE_APPLICATION)

    print("Validated result:")
    if extracted_application is not None:
        print(extracted_application.model_dump())
    else:
        print("No valid loan application was extracted.")