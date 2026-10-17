# Contributing to PurposeUX

Contributions should make purpose-conditioned UX evaluation easier to reproduce and harder to overclaim. Useful work includes bug fixes, diagnostic failures, data provenance review, evaluation improvements, and documentation corrections.

## Before changing code

Read the [README](README.md), [dataset card](docs/DATASET_CARD.md), and [model card](docs/MODEL_CARD.md). For a substantial change, open an issue describing the concrete problem, proposed scope, and evidence needed to assess it. Small, focused fixes can go directly to a pull request.

Use the editable installation and `purposeux doctor` command in the README to check your environment. Keep changes focused and preserve unrelated work. Include the closest relevant automated check or a reproducible command in your pull request; model-runtime changes also need a recorded real run on the affected path when hardware is available. State explicitly when runtime behavior remains unverified.

Do not commit model downloads, local adapters, caches, secrets, private screenshots, or machine-specific logs. Generated evaluation reports intended as evidence must identify the relevant data, model, adapter, and run configuration without exposing private paths or credentials.

## Report a failure

Use the [issue templates](https://github.com/tac0de/purpose-ux/issues/new/choose). Include the exact command, package and operating-system versions, relevant model identifier, expected behavior, observed behavior, and a minimal public reproduction. Remove personal data and secrets before uploading logs or screenshots.

For a model judgment, include the purpose, candidates, label order, data provenance, and why the expected answer follows from the stated rubric. Distinguish a rubric disagreement from an implementation bug. A surprising label is useful evidence but does not by itself show that training or inference is broken.

## Contribute data

- Use original or appropriately licensed screenshots and record provenance.
- Label synthetic, human-annotated, and measured task-outcome evidence separately.
- Keep all related screen variants, opposing-purpose pairs, and candidate-order swaps in the same split.
- Document ambiguous examples and disagreement instead of silently forcing consensus.
- Do not submit personal information, confidential product screens, or data you lack permission to share.

Changes to data or splits must include an updated dataset card and affected validation evidence. Do not tune on the held-out test set and then report it as an independent evaluation.

## Report results

Compare the base model and adapter under matching conditions. Report unsuccessful runs and limitations alongside favorable results. Keep claims proportional to the evidence: synthetic-rubric agreement is not measured human preference, accessibility compliance, or task success.

## Pull request checklist

- Explain the problem and resulting behavior.
- State the scope of validation and its result, including any unavailable hardware.
- Update documentation when commands, schemas, or supported behavior change.
- Attribute external code, models, and data and preserve their license terms.

Please discuss technical disagreements respectfully and focus on reproducible evidence. Sponsorship is welcome through [GitHub Sponsors](https://github.com/sponsors/tac0de), but no payment is required to report problems, use the toolkit, or contribute.
