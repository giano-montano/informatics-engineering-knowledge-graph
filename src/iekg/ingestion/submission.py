"""Submission: what the API does when the operator uploads a document (RF-02).

Mints the resource key, keeps the file under it in the document store and
records a pending run (ADR-009). It does not touch the graph.
"""

import shutil
from pathlib import Path
from uuid import uuid4

from iekg.ingestion.declared import RESOURCE_TYPES, normalize_course_code
from iekg.ingestion.orchestrator import document_path
from iekg.operational_store import OperationalStore


class SubmissionError(ValueError):
    pass


def submit_document(
    store: OperationalStore,
    documents: Path,
    source: Path,
    *,
    resource_type: str,
    course_code: str,
    course_name: str,
) -> int:
    """Record a pending run for ``source``; return its id."""
    if resource_type not in RESOURCE_TYPES:
        raise SubmissionError(f"unknown resource type {resource_type!r}; known: {', '.join(RESOURCE_TYPES)}")
    if not normalize_course_code(course_code) or not course_name.strip():
        raise SubmissionError("a syllabus needs the code and the name of its course")
    if source.suffix.lower() != ".pdf" or not source.is_file():
        raise SubmissionError(f"{source} is not a PDF file")
    resource_key = str(uuid4())
    target = document_path(documents, resource_key)
    documents.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    try:
        return store.create_run(
            resource_key=resource_key,
            resource_type=resource_type,
            course_code=normalize_course_code(course_code),
            course_name=course_name.strip(),
            file_name=source.name,
        )
    except Exception:
        target.unlink(missing_ok=True)
        raise
