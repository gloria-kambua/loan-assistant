"""Validated data model for individual and group loan applications."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class LoanApplication(BaseModel):
    """Defines the fields that a loan application must contain.

    Pydantic performs validation while the model is being created, so callers receive
    structured, consistent data or a clear validation error instead of silently using
    malformed application details.
    """

    # Reject unknown fields and trim accidental whitespace from text values.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Limit loan type values so downstream rule-checking code is predictable.
    loan_type: Literal["individual", "group"] = Field(
        description="Whether this is an individual or group loan application"
    )
    # A borrower name is required and cannot be blank after whitespace trimming.
    applicant: str = Field(min_length=1, description="The borrower's full name")

    # Reject zero, negative, or missing loan requests; they cannot represent a valid request.
    requested_amount: float = Field(
        gt=0,
        description="The positive amount of money requested by the applicant",
    )
    # Keep currency codes machine-readable and consistent for later calculations.
    currency: str = Field(
        default="KES",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="Three-letter ISO 4217 currency code",
    )
    # Purpose is required so every application has a basic reason for the loan.
    purpose: str = Field(min_length=1, description="What the loan will be used for")

    # Income may be absent, but when supplied it cannot be negative.
    monthly_income: float | None = Field(
        default=None,
        ge=0,
        description="The applicant's monthly income, if provided",
    )
    # Guarantor data is optional, so blank text is not accepted when it is present.
    guarantor: str | None = Field(
        default=None,
        min_length=1,
        description="The guarantor's full name, if provided",
    )


if __name__ == "__main__":
    # Example: demonstrate creating and inspecting a valid application.
    application = LoanApplication(
        loan_type="individual",
        applicant="Jane Doe",
        requested_amount=250_000,
        purpose="Purchase inventory",
        monthly_income=80_000,
    )
    print(application.model_dump())
    print(LoanApplication.model_json_schema())

    # Demonstrate that Pydantic rejects a negative requested amount.
    try:
        LoanApplication(
            loan_type="individual",
            applicant="Jane Doe",
            requested_amount=-500,
            purpose="Purchase inventory",
        )
    except ValidationError as error:
        print(error)