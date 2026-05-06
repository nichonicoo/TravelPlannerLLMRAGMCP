from datetime import date, timedelta
import re


def extract_hotel_params(query: str, session: dict = None) -> dict:
    """Extract hotel parameters using simple regex and fallback logic (no LLM)."""
    query_lower = query.lower()

    today = date.today()
    check_in = (today + timedelta(days=1)).isoformat()
    check_out = (today + timedelta(days=2)).isoformat()

    # Extract location using simple regex
    location = None
    words = query_lower.split()
    for i, w in enumerate(words):
        if w == "di" and i + 1 < len(words):
            location = words[i + 1].capitalize()
            break

    # Handle reference to previous location
    if not location and session:
        # Check for reference keywords
        if any(ref in query_lower for ref in ["di situ", "di sana", "tempat itu"]):
            location = (
                session.get("context", {}).get(
                    "city", {}).get("destination_name")
                or session.get("context", {}).get("city", {}).get("name")
            )
        # Fallback to session context
        if not location:
            location = (
                session.get("context", {}).get(
                    "city", {}).get("destination_name")
                or session.get("context", {}).get("city", {}).get("name")
            )

    # Extract currency based on language
    currency = "IDR"  # Default to IDR
    if any(word in query_lower for word in ["dollar", "usd", "$", "english"]):
        currency = "USD"

    # Extract adults count
    adults = 1
    match_adult = re.search(r"(\d+)\s*(orang|dewasa)", query_lower)
    if match_adult:
        adults = int(match_adult.group(1))

    # Extract children count
    children = 0
    match_child = re.search(r"(\d+)\s*anak", query_lower)
    if match_child:
        children = int(match_child.group(1))

    # Extract price constraints
    min_price = None
    max_price = None
    if "murah" in query_lower:
        max_price = 500000

    sort_by = 3 if "murah" in query_lower else None

    return {
        "location": location,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": adults,
        "children": children,
        "currency": currency,
        "sort_by": sort_by,
        "min_price": min_price,
        "max_price": max_price
    }
