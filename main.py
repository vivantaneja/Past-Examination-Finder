#!/usr/bin/env python3
import json
from typing import Dict, List


def load_data() -> Dict:
    with open("data.json") as f:
        return json.load(f)


def choose(prompt: str, options: List[str]) -> str:
    """Generic numbered-menu chooser."""
    if not options:
        raise ValueError(f"No options available for: {prompt}")

    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")

    while True:
        try:
            choice = int(input("Enter number: ")) - 1
            if 0 <= choice < len(options):
                return options[choice]
        except (ValueError, KeyboardInterrupt):
            pass
        print("Invalid choice")


def classify_material_type(entry: Dict) -> str:
    """
    Map a raw entry to one of:
    - 'Exam Paper'
    - 'Marking Scheme'
    - 'Deferred Exam Paper'
    - 'Deferred Marking Scheme'
    - 'Audio'
    or '' (unknown / not in the allowed set).
    """
    t = entry.get("type", "").strip()
    details = entry.get("details", "")
    url = entry.get("url", "")
    url_upper = url.upper()
    details_upper = details.upper()

    # Audio: mp3 files or explicitly marked as sound file
    if url_upper.endswith(".MP3") or "SOUND FILE" in details_upper:
        return "Audio"

    if t == "Exam Paper":
        return "Exam Paper"
    if t == "Marking Scheme":
        return "Marking Scheme"
    if t == "Deferred Exam Paper":
        return "Deferred Exam Paper"
    if t == "Deferred Marking Scheme":
        return "Deferred Marking Scheme"

    return ""


def main() -> None:
    data = load_data()

    # 1. Examination (exam): JC, LC, LCA
    exams = {
        "Junior Certificate": "jc",
        "Leaving Certificate": "lc",
        "Leaving Certificate Applied": "lb",
    }
    exam_name = choose("Choose examination:", list(exams.keys()))
    exam_key = exams[exam_name]

    if exam_key not in data:
        print("No data available for that examination.")
        return

    # 2. Course (subject) – only those that exist for this exam
    subjects = sorted(data[exam_key].keys())
    if not subjects:
        print("No subjects available for that examination.")
        return

    subject_name = choose("Choose course (subject):", subjects)

    # 3. Year – only years that exist for this exam + subject
    subject_years = data[exam_key].get(subject_name, {})
    if not subject_years:
        print("No years available for that subject in this examination.")
        return

    years = sorted(subject_years.keys(), reverse=True)
    year = choose("Choose year:", years)

    entries = subject_years.get(year, [])
    if not entries:
        print("No materials found for that combination.")
        return

    # 4. Level – infer from details (Higher, Ordinary, Foundation, Common)
    possible_levels = ["Higher", "Ordinary", "Foundation", "Common"]
    levels = set()
    for e in entries:
        for lvl in possible_levels:
            if lvl in e.get("details", ""):
                levels.add(lvl)
                break

    if not levels:
        levels = {"All"}

    level = choose("Choose level:", sorted(levels))
    if level != "All":
        entries = [e for e in entries if level in e.get("details", "")]

    if not entries:
        print("No materials found for that level.")
        return

    # 5. Language – infer from URL suffix (EV/IV) across PDFs/MP3s
    langs = {"English": "EV", "Irish": "IV"}
    available_langs = []
    for lang_name, code in langs.items():
        code_upper = code.upper()
        if any(
            e.get("url", "").upper().endswith(f"{code_upper}.PDF")
            or e.get("url", "").upper().endswith(f"{code_upper}.MP3")
            for e in entries
        ):
            available_langs.append(lang_name)

    lang_code = None
    if available_langs:
        lang_name = choose("Choose language:", available_langs)
        lang_code = langs[lang_name].upper()
        entries = [
            e
            for e in entries
            if e.get("url", "").upper().endswith(f"{lang_code}.PDF")
            or e.get("url", "").upper().endswith(f"{lang_code}.MP3")
        ]

        if not entries:
            print("No materials found for that language.")
            return

    # 6. Material type – only show the types that actually exist
    material_labels_in_order = [
        "Exam Paper",
        "Marking Scheme",
        "Deferred Exam Paper",
        "Deferred Marking Scheme",
        "Audio",
    ]

    available_materials = set()
    for e in entries:
        mt = classify_material_type(e)
        if mt:
            available_materials.add(mt)

    material_choices = [m for m in material_labels_in_order if m in available_materials]

    if not material_choices:
        print("No supported material types found for that combination.")
        return

    material_choice = choose("Choose material type:", material_choices)

    # Filter entries down to the chosen material type
    filtered = [
        e for e in entries if classify_material_type(e) == material_choice
    ]

    if not filtered:
        print("No materials found for that material type.")
        return

    # 7. If more than one file remains (e.g. Paper One / Two), ask which one
    if len(filtered) == 1:
        chosen = filtered[0]
    else:
        details_options = [e.get("details", "(no details)") for e in filtered]
        chosen_details = choose("Choose specific file:", details_options)
        idx = details_options.index(chosen_details)
        chosen = filtered[idx]

    url = chosen.get("url")
    if not url:
        print("Selected material has no URL.")
        return

    print(f"\n→ https://www.examinations.ie/archive/exampapers/{year}/{url}")


if __name__ == "__main__":
    main()