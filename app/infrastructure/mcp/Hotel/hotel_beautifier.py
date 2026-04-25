def beautify_hotels(result: dict) -> str:
    props = result.get("properties", [])

    if not props:
        return "Tidak ditemukan hotel."

    lines = ["🏨 Rekomendasi Hotel:\n"]

    for i, h in enumerate(props[:5], 1):
        name = h.get("name", "-")
        price = h.get("rate_per_night", {}).get("lowest", "Tidak tersedia")
        rating = h.get("overall_rating", "-")
        reviews = h.get("reviews", "-")
        hotel_class = h.get("hotel_class", "-")
        link = h.get("link", "-")

        amenities = h.get("amenities", [])
        amenities_str = ", ".join(amenities[:3]) if amenities else "Tidak tersedia"

        lines.append(f"{i}. {name}")
        lines.append(f"   ⭐ {rating} ({reviews} reviews)")
        lines.append(f"   🏨 {hotel_class}⭐")
        lines.append(f"   💰 {price}")
        lines.append(f"   🧳 {amenities_str}")
        lines.append(f"   🔗 {link}")
        lines.append("")

    return "\n".join(lines)


def beautify_hotel_detail(result: dict) -> str:
    h = result.get("property", {})

    if not h:
        return "Detail hotel tidak tersedia."

    name = h.get("name", "-")
    address = h.get("address", "-")
    rating = h.get("overall_rating", "-")
    reviews = h.get("reviews", "-")
    price = h.get("rate_per_night", {}).get("lowest", "Tidak tersedia")
    hotel_class = h.get("hotel_class", "-")

    check_in = h.get("check_in_time", "-")
    check_out = h.get("check_out_time", "-")

    link = h.get("link", "-")

    amenities = ", ".join(h.get("amenities", [])[:8]) or "Tidak tersedia"

    nearby = "\n".join(
        f"- {p.get('name')} ({p.get('distance')})"
        for p in h.get("nearby_places", [])[:5]
    ) or "Tidak tersedia"

    breakdown = "\n".join(
        f"- {k}: {v}"
        for k, v in h.get("reviews_breakdown", {}).items()
    ) or "Tidak tersedia"

    return f"""
            🏨 {name}

            📍 {address}

            ⭐ {rating} ({reviews} reviews)
            🏨 {hotel_class}⭐

            💰 {price}

            🕒 Check-in: {check_in}
            🕛 Check-out: {check_out}

            🧳 Fasilitas:
            {amenities}

            📍 Sekitar:
            {nearby}

            🗣 Review:
            {breakdown}

            🔗 {link}
            """