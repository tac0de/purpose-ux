# PurposeUX

Build a purpose-conditioned visual A/B decision model that trains and runs on an
Apple Silicon Mac. Preserve the user's actual Codex model, effort and authentication.

- Scope and acceptance are in docs/TRD.md. Synthetic rubric labels are not human
  preferences, real task-success observations or broad UX expertise.
- Split by family and group. Purpose counterfactuals and candidate-order swaps of
  the same screen stay together. Never feed labels, rationales, ordering metadata
  or IDs into inference prompts.
- Use one project .venv and the shared Hugging Face cache. Keep training outputs
  outside Git, one final adapter per named run, and no per-step checkpoint copies.
  Report images, weights, data provenance and limitations honestly.
- Follow the host's source-bound command-evidence policy where configured.
  Ordinary contributors can run the documented Python tests directly; no private
  maintainer tooling is a project dependency. Scope checks to changed behavior;
  do not force whole-product browser QA.
- Browser rendering uses repository scripts and Playwright CLI headless. Inspect
  representative rendered dataset screens. Do not deploy websites.
- Public GitHub release and Sponsors linking are authorized for this project.
  Do not expose local paths, secrets, private receipts or raw machine identifiers.
  Release metrics must come from actual executions; no invented testimonials.
