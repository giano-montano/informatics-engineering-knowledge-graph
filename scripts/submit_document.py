"""Development aid: submit a document and run the worker, without the API.

Not an entry point of the system (ADR-007): it calls the same submission
function the API calls, then runs the worker in this process.

    uv run python scripts/submit_document.py SYLLABUS.pdf --course 1INF33 --name "Bases de Datos"
"""

import argparse
import sys
from pathlib import Path

from iekg.ingestion import worker
from iekg.ingestion.declared import SYLLABUS
from iekg.ingestion.submission import SubmissionError, submit_document
from iekg.operational_store import OperationalStore
from iekg.settings import Settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("document", type=Path)
    parser.add_argument("--course", required=True, help="course code, as in the syllabus")
    parser.add_argument("--name", required=True, help="course name")
    parser.add_argument("--type", default=SYLLABUS, help=f"resource type (default: {SYLLABUS})")
    parser.add_argument("--no-worker", action="store_true", help="only record the pending run")
    args = parser.parse_args()
    settings = Settings.from_environment()
    with OperationalStore(settings.operational_db) as store:
        try:
            with args.document.open("rb") as content:
                run_id = submit_document(store, settings.documents_dir, content, file_name=args.document.name,
                                         resource_type=args.type, course_code=args.course, course_name=args.name)
        except (SubmissionError, OSError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
    print(f"Run {run_id} recorded as pending")
    return 0 if args.no_worker else worker.main()


if __name__ == "__main__":
    sys.exit(main())
