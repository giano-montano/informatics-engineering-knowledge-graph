from io import BytesIO

import pytest

from iekg.ingestion.declared import SYLLABUS
from iekg.ingestion.orchestrator import document_path
from iekg.ingestion.submission import SubmissionError, submit_document, withdraw_submission
from iekg.operational_store import PENDING, OperationalStore

PDF = b"%PDF-1.7\n%fake body\n"


def submit(tmp_path, content=PDF, **overrides):
    declared = {
        "file_name": "silabo.pdf", "resource_type": SYLLABUS, "course_code": " 1inf33 ", "course_name": " Bases ",
    } | overrides
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        run_id = submit_document(store, tmp_path / "documents", BytesIO(content), **declared)
        return store.get_run(run_id)


def test_a_submission_keeps_the_whole_file_under_its_key_and_records_a_pending_run(tmp_path):
    run = submit(tmp_path)
    assert document_path(tmp_path / "documents", run.resource_key).read_bytes() == PDF
    assert run.status == PENDING
    assert (run.course_code, run.course_name, run.file_name) == ("1INF33", "Bases", "silabo.pdf")


@pytest.mark.parametrize("content, file_name", [
    (b"not a pdf at all", "silabo.pdf"),
    (b"", "silabo.pdf"),
    (PDF, "silabo.docx"),
])
def test_what_is_not_a_pdf_is_refused(tmp_path, content, file_name):
    with pytest.raises(SubmissionError, match="not a PDF"):
        submit(tmp_path, content, file_name=file_name)
    assert not any((tmp_path / "documents").glob("*"))


def test_an_unknown_resource_type_is_refused(tmp_path):
    with pytest.raises(SubmissionError, match="unknown resource type"):
        submit(tmp_path, resource_type="Libro")


@pytest.mark.parametrize("field", ["course_code", "course_name"])
def test_a_syllabus_without_its_course_is_refused(tmp_path, field):
    with pytest.raises(SubmissionError, match="code and the name"):
        submit(tmp_path, **{field: "  "})


@pytest.mark.parametrize("taken", [False, True])
def test_a_submission_is_withdrawn_with_its_document_only_while_no_worker_took_it(tmp_path, taken):
    run = submit(tmp_path)
    document = document_path(tmp_path / "documents", run.resource_key)
    with OperationalStore(tmp_path / "operational.sqlite") as store:
        if taken:
            store.take_pending_run()
        assert withdraw_submission(store, tmp_path / "documents", run.id) == (not taken)
        assert len(store.list_runs()) == (1 if taken else 0)
    assert document.is_file() == taken
