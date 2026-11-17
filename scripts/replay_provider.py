"""Development aid: a simulated language model provider for rehearsing an ingestion.

It answers the Chat Completions route of an OpenAI compatible provider with the
model output that a real run left in an operational store, whatever it is
asked. With ``IEKG_LLM_BASE_URL`` pointed at it, the worker reads the PDF,
assembles, validates, writes and audits as it does in production, but nothing
is sent to a provider and nothing is paid.

It is not a provider of the system and is not an entry point: it exists for the
technical walkthrough of CA-11 (the operator panel), which needs a run that
ends well without a real model. The output it replays was produced against the
graph as it was when that run started, so the rehearsal graph should be in that
same state (``load``, then ``reapply`` with the facts of the runs before it).

    uv run python scripts/replay_provider.py --operational-db var/medicion-r4/operational.sqlite --run 14
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROUTE = "/v1/chat/completions"
MODEL_NAME = "simulated-replay"


def stored_output(operational_db: Path, run_id: int) -> str:
    """The model output stored for ``run_id``; exits if there is none."""
    with sqlite3.connect(f"file:{operational_db.as_posix()}?mode=ro", uri=True) as connection:
        row = connection.execute("SELECT output FROM model_outputs WHERE run_id = ?", (run_id,)).fetchone()
    if row is None:
        sys.exit(f"error: run {run_id} has no stored model output in {operational_db}")
    return row[0]


def completion(output: str, request: dict, counter: int) -> dict:
    """A Chat Completions response whose only choice is ``output``."""
    return {
        "id": f"replay-{counter}",
        "object": "chat.completion",
        "created": int(time.time()),
        # The model the run records: it says the answer was simulated.
        "model": f"{MODEL_NAME} ({request.get('model', '?')})",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": output},
                "finish_reason": "stop",
            }
        ],
        # Nothing was generated: no tokens are reported.
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def describe(request: dict) -> str:
    """One line about what was asked, without the document."""
    response_format = request.get("response_format") or {}
    schema = response_format.get("json_schema") or {}
    characters = sum(len(str(message.get("content", ""))) for message in request.get("messages", []))
    return (
        f"model={request.get('model')} format={response_format.get('type')} "
        f"schema={schema.get('name')} strict={schema.get('strict')} "
        f"messages={len(request.get('messages', []))} characters={characters}"
    )


def make_handler(output: str):
    counter = {"requests": 0}

    class ReplayHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 (the name http.server calls)
            if self.path.rstrip("/") != ROUTE:
                self.send_error(404, f"only {ROUTE} is simulated")
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                request = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                self.send_error(400, "the request body is not JSON")
                return
            counter["requests"] += 1
            print(f"request {counter['requests']}: {describe(request)}", flush=True)
            body = json.dumps(completion(output, request, counter["requests"])).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A002 (signature of http.server)
            pass

    return ReplayHandler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--operational-db", type=Path, required=True, help="the store of the real run")
    parser.add_argument("--run", type=int, required=True, help="the run whose model output is replayed")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    arguments = parser.parse_args(argv)

    output = stored_output(arguments.operational_db, arguments.run)
    server = ThreadingHTTPServer((arguments.host, arguments.port), make_handler(output))
    print(
        f"replaying the output of run {arguments.run} ({len(output)} characters) "
        f"at http://{arguments.host}:{arguments.port}/v1",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
