"""Gemini-powered assistant for the CampusVerse AI simulated campus prototype.

The LLM receives bounded, non-secret, synthetic dashboard data only.
All updates to campus records continue to require existing administrator workflows.
"""
from __future__ import annotations

import json
from collections import Counter
from campusverse import data as db

DEFAULT_MODEL = "gemini-3.8-flash"


def build_campus_context(building: str) -> dict:
    """Collect bounded, structured data; do not send free-text ticket descriptions or staff names."""
    rooms = []
    for r in db.spaces(building)[:90]:
        row = {
            "facility": r["label"], "type": r["category"],
            "floor": r["floor"] if r["floor"] is not None and r["floor"] >= 0 else "unverified",
            "capacity_demo": r["capacity"], "occupied_demo": r["occupied"],
        }
        if r["category"] in ("classroom", "lecture"):
            e = db.energy_for(r["id"])
            if e:
                row["equipment_power_kw_demo"] = {
                    name: round(float(e[name]), 2) for name in ("ac", "lights", "fans", "other")
                }
        rooms.append(row)
    reports = db.tickets(building)
    crowd = db.crowd_events(building)
    return {
        "scope": building,
        "data_provenance": "Synthetic, illustrative hackathon database. NOT live DSU data or verified safety information.",
        "facilities": rooms,
        "waste_bins": [
            {"area": b["location"], "fill_percent_demo": b["fill"]}
            for b in db.bins(building)[:25]
        ],
        "parking_campus_wide": [
            {"zone": p["label"], "capacity_demo": p["capacity"], "occupied_demo": p["occupied"]}
            for p in db.parking()[:15]
        ],
        "maintenance": {
            "total_reports": len(reports),
            "status_counts": dict(Counter(r["status"] for r in reports)),
            "priority_counts": dict(Counter(r["priority"] for r in reports)),
            "category_counts": dict(Counter(r["category"] for r in reports)),
            "note": "Individual descriptions, submitter details, and staff names are not shared with the AI.",
        },
        "crowd": {
            "total_simulated_incidents": len(crowd),
            "status_counts": dict(Counter(c["status"] for c in crowd)),
            "note": "Illustrative counts only; no surveyed exits, safe routing, or verified crowd capacity.",
        },
    }


def ask_gemini(building: str, question: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    """Send one bounded, informational request; never mutate the database."""
    if not api_key.strip():
        raise ValueError("Missing GEMINI_API_KEY")
    clean_question = question.strip()[:600]
    if not clean_question:
        raise ValueError("Please enter a question")

    # Lazy import keeps existing rule-based Campus Brain usable without an API key.
    from google import genai

    context = build_campus_context(building)
    instructions = (
        "You are the CampusVerse AI Campus Brain, assisting an authorized administrator. "
        "Answer the user's question using ONLY the supplied structured synthetic demo data. "
        "Do not invent live DSU readings, verified locations, capacities, savings, or sensor integrations. "
        "If information is unavailable, say so. Clearly label conclusions as simulated. "
        "Give actionable campus-maintenance or energy-efficiency ideas as suggestions, "
        "not as actions performed. Never claim an issue was resolved or assigned. "
        "Do not provide evacuation routes, emergency exit instructions, or crowd movement plans. "
        "For congestion, suggest contacting campus safety staff and following approved procedures. "
        "Keep the answer concise and readable with a short prioritized list where useful."
    )
    prompt = (
        instructions + "\n\nSIMULATED DASHBOARD SNAPSHOT (JSON):\n"
        + json.dumps(context, ensure_ascii=False, separators=(",", ":"))
        + "\n\nADMINISTRATOR QUESTION:\n" + clean_question
    )
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model.strip() or DEFAULT_MODEL,
            contents=prompt,
            config={"temperature": 0.2, "max_output_tokens": 1000},
        )
        result = getattr(response, "text", None)
        return result.strip() if result and result.strip() else "Gemini returned no text. Try a different question."
    finally:
        client.close()
