"""Ingestion pipeline: submission, orchestrator, extractor and declared facts.

Runs in the worker (``kms.worker`` in docs/architecture/model.c4). Everything
after the model's output is deterministic code, and only the graph core writes
(ADR-003).
"""
