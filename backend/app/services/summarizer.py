from __future__ import annotations

import json
import re
from typing import Any

import httpx

from ..config import get_settings

settings = get_settings()

DEFAULT_SECTIONS = ["Agenda-Ueberblick", "Entscheidungen", "Aufgaben", "Offene Punkte"]
HIGHLIGHT_SECTION = "Highlights"
SECTION_HINTS = {
    "Agenda-Ueberblick": "Was wurde besprochen?",
    "Entscheidungen": "Welche konkreten Entscheidungen wurden getroffen?",
    "Aufgaben": "Welche Aufgaben wurden verteilt? Wer ist verantwortlich? Welche Fristen?",
    "Offene Punkte": "Was ist noch zu klaeren oder nachzuholen?",
    "Highlights": "Bemerkenswerte Aussagen, Zitate oder Stimmungen (optional).",
}
PLACEHOLDER_TEXT = "(nicht eindeutig aus Transkript ersichtlich)"


async def summarize(transcript: str, session_settings: dict[str, Any]) -> dict[str, Any]:
    clean_text = transcript.strip()
    sections = _effective_sections(session_settings.get("sections"))
    prompt_sections = sections + ([HIGHLIGHT_SECTION] if HIGHLIGHT_SECTION not in sections else [])

    if not clean_text:
        return _fallback_summary(sections)

    prompt = _build_prompt(clean_text, prompt_sections, session_settings)
    url = f"{settings.ollama_host}/api/generate"
    payload = {
        "model": settings.summary_model,
        "prompt": prompt,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("response") or data.get("message", {}).get("content", "") or ""
    except Exception:
        return _fallback_summary(sections)

    summary_text = content.strip()
    if not summary_text:
        return _fallback_summary(sections)

    _validate_summary(summary_text, prompt_sections)
    structured = _structure_summary(summary_text, sections, prompt_sections)
    structured["raw"] = summary_text
    return structured


def _effective_sections(configured: Any) -> list[str]:
    if not configured:
        return list(DEFAULT_SECTIONS)
    sections = [str(section).strip() for section in configured if str(section).strip()]
    return sections or list(DEFAULT_SECTIONS)


def _build_prompt(transcript: str, sections: list[str], session_settings: dict[str, Any]) -> str:
    section_lines = []
    for index, section in enumerate(sections, start=1):
        label = _display_label(section)
        hint = SECTION_HINTS.get(section, "Fasse klar strukturiert zusammen und nenne Verantwortliche sowie Fristen.")
        section_lines.append(f"{index}. **{label}** – {hint}")

    meeting_type = session_settings.get("meeting_type") or PLACEHOLDER_TEXT
    audience = session_settings.get("audience") or PLACEHOLDER_TEXT
    objectives = session_settings.get("objectives") or PLACEHOLDER_TEXT
    notes = session_settings.get("notes") or PLACEHOLDER_TEXT

    return (
        "Du erhaelst ein potenziell fehlerhaftes Transkript eines deutschsprachigen Meetings.\n"
        "Bereinige offensichtliche Erkennungsfehler, ignoriere unverständliche Sätze und generiere ein kompaktes Ergebnisprotokoll.\n"
        "Arbeite die folgenden Abschnitte muendlich sauber heraus:\n"
        f"{chr(10).join(section_lines)}\n\n"
        "Wichtige Regeln:\n"
        "- Lasse Grussformeln, Smalltalk und irrelevante Inhalte weg.\n"
        "- Verwende klare, korrekte deutsche Sprache.\n"
        "- Wenn Informationen fehlen, schreibe genau: \"(nicht eindeutig aus Transkript ersichtlich)\".\n"
        "- Erfinde keine Fakten.\n"
        "- Gib die Antwort strukturiert mit den oben genannten Zwischenueberschriften aus.\n\n"
        f"Kontext:\n"
        f"- Besprechungstyp: {meeting_type}\n"
        f"- Zielgruppe: {audience}\n"
        f"- Ziele: {objectives}\n"
        f"- Notizen: {notes}\n\n"
        "Transkript (bereinigt):\n\n"
        f"{transcript}\n"
    )


def _structure_summary(summary_text: str, sections: list[str], prompt_sections: list[str]) -> dict[str, Any]:
    section_map = {section: [] for section in sections}
    highlights: list[str] = []
    current_section: str | None = None
    for raw_line in summary_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        header_match = _match_section_heading(line, prompt_sections)
        if header_match:
            current_section = header_match
            continue

        if current_section is None:
            continue

        if current_section == HIGHLIGHT_SECTION:
            bullet = line.lstrip("-• ").strip()
            if bullet:
                highlights.append(bullet)
        elif current_section in section_map:
            section_map[current_section].append(line)

    sections_result = {
        section: (" ".join(lines).strip() or PLACEHOLDER_TEXT)
        for section, lines in section_map.items()
    }

    return {
        "sections": sections_result,
        "highlights": highlights,
    }


def _match_section_heading(line: str, sections: list[str]) -> str | None:
    normalized_line = re.sub(r"^\d+[\).\-\s]*", "", line)
    normalized_line = normalized_line.strip("*:- ").lower()
    for section in sections:
        label = _display_label(section).lower()
        if normalized_line.startswith(label):
            return section
    return None


def _display_label(section: str) -> str:
    return (
        section.replace("Ae", "Ä")
        .replace("ae", "ä")
        .replace("Oe", "Ö")
        .replace("oe", "ö")
        .replace("Ue", "Ü")
        .replace("ue", "ü")
    )


def _validate_summary(summary_text: str, sections: list[str]) -> None:
    lowered = summary_text.lower()
    missing = []
    for section in sections:
        label = _display_label(section).lower()
        if label not in lowered:
            missing.append(label)
    if missing:
        print(f"Warnung: Zusammenfassung enthaelt folgende Sektionen nicht eindeutig: {', '.join(missing)}")


def _fallback_summary(sections: list[str]) -> dict[str, Any]:
    return {
        "sections": {section: PLACEHOLDER_TEXT for section in sections},
        "highlights": [],
        "raw": "",
    }
