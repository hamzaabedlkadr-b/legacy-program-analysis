# Anonymization Workspace

This folder groups all PII/anonymization work.

```text
scripts/                 local scan and pseudonymization utilities
docs/                    anonymization report and notes
artifacts/               generated scan reports, demo files, and watchlists
cobol-code-anonymizer/   separate local anonymizer Git repo
```

The main COBOL RAG pipeline does not depend on `cobol-code-anonymizer/` directly. It is kept here as a related external tool.

Generated reports and demo artifacts should stay under `unused/anonymization/artifacts/`.
