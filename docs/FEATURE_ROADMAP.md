# ReelMetrics feature roadmap

These are new candidates beyond the current local audit CLI, schema profiles, HTML summary export, fixed-dataset dashboard, review queue and decision export. They are hypotheses; build only after buyer evidence. First priority is private, repeatable file review.

| # | Feature | User problem and competitor gap to test | Impact | Effort |
|---:|---|---|---|---|
| 1 | Batch folder audit with per-file isolation | Catalog teams have many exports and want one repeatable run without combining customer files. | High | Medium |
| 2 | Before/after audit comparison | Operators need to prove which quality measures changed after cleanup. | High | Medium |
| 3 | Versioned YAML rule profiles with validation | Teams need reusable checks that are easier to share than bespoke setup in broader frameworks. | High | Medium |
| 4 | Column-mapping preview | Source exports use inconsistent headers and need a safe mapping before analysis. | High | Medium |
| 5 | Human-reviewed repair suggestions | Analysts want a shortlist of safe fixes while preserving the original row and requiring approval. | High | High |
| 6 | Duplicate clusters with explainable match reasons | Similar title records require evidence for a reviewer, not automatic deletion. | High | High |
| 7 | Privacy preflight for email/phone-like fields | Operators need to catch accidental personal data before sharing reports. | High | Medium |
| 8 | Offline HTML/PDF client report | A fixed-scope audit needs a presentable handoff that can be shared without a login. | High | Medium |
| 9 | Reproducible audit bundle with manifest/checksums | Buyers need to link a report to its exact input and rule version without exposing row values. | High | Medium |
| 10 | Approval/sign-off sheet with reviewer and timestamp fields | A catalog owner needs a clear human decision trail for flagged records. | Medium | Medium |
| 11 | Scheduled local audit via OS task/cron example | Repeat audits should run on the client's machine without uploading the source file. | Medium | Medium |
| 12 | CI action for synthetic or repository-owned catalogs | Developers want a failing quality gate before publishing a checked-in dataset. | Medium | High |
| 13 | Encoding/date/locale detection report | Analysts need to spot common parsing risks before transformations. | Medium | Medium |
| 14 | Optional Parquet input and output | Some teams receive typed columnar exports and want to avoid conversion work. | Medium | High |
| 15 | Local-only narrative explanation templates | Reviewers need plain-language rule explanations without sending private records to an AI provider. | Medium | Medium |

## Build gate

Implement features 1–4 and 7–9 only after an interview confirms private local audits are valuable. Each needs fixtures covering malformed input, clear UI/CLI status, tests, a privacy note and a reversible report flow. AI, shared customer uploads, hosted accounts, and billing are deferred: they add privacy/support cost without current willingness-to-pay evidence. Never auto-delete or silently rewrite source records.
