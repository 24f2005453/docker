from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import re
from datetime import datetime

app = FastAPI()


class ExtractRequest(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


MONTHS = {
    "january": 1, "february": 2, "march": 3,
    "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}


def parse_date(text: str):
    # ISO format
    m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if m:
        return m.group(1)

    # 2026/07/21
    m = re.search(r"\b(20\d{2})[/-](\d{2})[/-](\d{2})\b", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # July 21, 2026
    m = re.search(
        r"([A-Za-z]+)\s+(\d{1,2}),?\s+(20\d{2})",
        text,
        re.I,
    )
    if m:
        month = MONTHS[m.group(1).lower()]
        day = int(m.group(2))
        year = int(m.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"

    return ""


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):

    text = req.text

    if not text.strip():
        return ExtractResponse(
            vendor="",
            amount=0,
            currency="",
            date=""
        )

    # Currency
    currency = ""
    m = re.search(r"\b(USD|EUR|GBP)\b", text, re.I)
    if m:
        currency = m.group(1).upper()

    # Amount
    amount = 0.0

    patterns = [
        r"Total\s+Due[:\s]*[$€£]?\s*([\d,]+(?:\.\d+)?)",
        r"Amount\s+Due[:\s]*[$€£]?\s*([\d,]+(?:\.\d+)?)",
        r"Balance\s+Due[:\s]*[$€£]?\s*([\d,]+(?:\.\d+)?)",
        r"Total[:\s]*[$€£]?\s*([\d,]+(?:\.\d+)?)",
    ]

    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            amount = float(m.group(1).replace(",", ""))
            break

    if amount == 0:
        nums = re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", text)
        if nums:
            amount = float(nums[-1].replace(",", ""))

    # Vendor
    vendor = ""

    vendor_patterns = [
        r"Vendor[:\s]*(.+)",
        r"From[:\s]*(.+)",
        r"Bill From[:\s]*(.+)",
        r"Issuer[:\s]*(.+)",
    ]

    for p in vendor_patterns:
        m = re.search(p, text, re.I)
        if m:
            vendor = m.group(1).split("\n")[0].strip()
            break

    if not vendor:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            vendor = lines[0]

    date = parse_date(text)

    return ExtractResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date,
    )
