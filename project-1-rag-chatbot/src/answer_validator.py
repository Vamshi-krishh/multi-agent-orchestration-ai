import re
from src.retriever import parse_service_scope


def validate_answer(question: str, answer: str, sources: list[str]) -> dict:
    """
    Lightweight post-generation check.
    Catches the most common failure modes before returning to the user.
    """

    # Honest "I don't know" is always valid — don't override it
    if "don't have enough information" in answer.lower():
        return {'valid': True, 'honest_failure': True}

    # If user named a specific service, at least one source must be from it
    service_scope = parse_service_scope(question)
    if service_scope:
        service_in_sources = any(f"({service_scope})" in src for src in sources)
        if not service_in_sources:
            return {
                'valid': False,
                'reason': f'No sources found from {service_scope.upper()} service — answer may be from wrong service'
            }

    # If a specific PascalCase class was mentioned, it should appear in sources or answer
    class_names = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-zA-Z0-9]*)+)\b', question)
    if class_names:
        found = any(
            cls in answer or any(cls in src for src in sources)
            for cls in class_names
        )
        if not found:
            return {
                'valid': False,
                'reason': f'{class_names[0]} not found in retrieved context — answer may be incomplete'
            }

    return {'valid': True}
