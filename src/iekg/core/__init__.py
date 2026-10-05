"""Graph core: validator, repository and auditor.

The same code runs in the ingestion worker and in the build processes
(``#nucleo`` in docs/architecture/model.c4), so the reapplication reproduces
what the ingestion wrote and the rules are checked the same way everywhere.
"""
