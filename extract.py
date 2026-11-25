"""Extract structured loan applications from plain-text field notes."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from google.genai import types
from pydantic import ValidationError

from models import LoanApplication


# Fictional field notes for manually checking extraction edge cases.
TEST_CASES = [
    (
        "No guarantor mentioned",
        "Jane Wambui applies for an individual loan of KES 80,000 to buy market "
        "stock. Her monthly income is KES 32,000.",
        "guarantor should be None",
    ),
    (
        "Amount written as shorthand",
        "Brian Otieno wants an individual loan of 120k for a motorcycle repair "
        "shop. His monthly income is KES 55,000. Guarantor is Lucy Achieng.",
        "requested_amount should be 120000",
    ),
    (
        "Amount written in words",
        "Grace Njeri requests an individual loan of one hundred and twenty "
        "thousand shillings to expand her tailoring shop. Her monthly income is "
        "KES 48,000.",
        "requested_amount should be 120000",
    ),
    (
        "Applicant amount and officer suggestion",
        "Asha Njeri applied for an individual loan of KES 150,000 to restock her "
        "salon. The officer suggests reducing it to KES 100,000. Her monthly "
        "income is KES 60,000.",
        "check whether requested_amount reflects the applicant's request: 150000",
    ),
    (
        "Swahili and Sheng notes",
        "Naitwa Amina Njeri. Nahitaji mkopo wa shilingi elfu mia moja nifungue "
        "kibanda ya smokie. Income yangu ni elfu arobaini na tano kwa mwezi. "
        "Sina guarantor.",
        "requested_amount should be 100000, monthly_income 45000, and guarantor None",
    ),
]


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
    # Run every case separately so a temporary API failure does not skip later cases.
    for case_name, application_text, expected_check in TEST_CASES:
        print(f"\n=== {case_name} ===")
        print(f"Expected check: {expected_check}")

        try:
            extracted_application = extract(application_text)
        except APIError as error:
            # Report service/API errors and continue; these are not extraction results.
            print(f"Gemini API request failed: {error}")
            continue

        print("Validated result:")
        if extracted_application is not None:
            print(extracted_application.model_dump())
        else:
            print("No valid loan application was extracted.")