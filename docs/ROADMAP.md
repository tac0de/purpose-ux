# PurposeUX roadmap

PurposeUX starts with a local synthetic experiment. The next work should improve the evidence behind its judgments before expanding its claims. Funding and contributions support the public deliverables below; they do not guarantee a schedule, a score increase, or a commercial service.

## 0.1.0: reproducible synthetic starter

The initial toolkit release contains original synthetic screenshot records, family-based splits, local MLX-VLM LoRA training, fixed `A`/`B` inference, and base-versus-adapter evaluation. Its acceptance boundary is reproducibility and transparent provenance. It does not include human validation or measured task success.

Local model runs should retain configuration and evaluation artifacts. A completed command or favorable synthetic score does not close the research questions below.

## Next: human annotation

**Deliverables:** publish an annotation rubric, consent and data-handling approach, annotation interface or export format, and a small independently annotated evaluation set with documented annotator background and disagreement.

**Acceptance:** labels are traceable to an annotation protocol; disagreement and exclusion rules are reported; synthetic labels remain distinguishable from human labels. Any claim about human preference is limited to the sampled people and tasks.

**Why fund it:** this is the first check of whether the synthetic rubric reflects judgments people actually make. Funding can support annotation time and reproducible public tooling.

## External task datasets

**Deliverables:** add permissioned, attributable real-interface tasks or integrations with suitable published datasets, keeping original licenses, task context, and privacy constraints intact.

**Acceptance:** publish a dataset card and split audit, preserve interface/task identity across splits, and report failures separately from synthetic-fixture results. Task-success claims require actual outcome measurements.

**Why fund it:** synthetic screenshots cannot establish behavior on live interfaces. Dataset curation and legal provenance need careful work even when a dataset is freely available.

## Calibration and uncertainty

**Deliverables:** evaluate label-score reliability, candidate-order sensitivity, and the value of an explicitly trained abstention or uncertainty outcome.

**Acceptance:** define the measurement protocol before reporting results; keep calibration and evaluation data separate; report coverage and errors together. `T`/`N`/`U` contract fixtures alone do not count as trained uncertainty support.

**Why fund it:** a forced binary label can look more decisive than the available evidence warrants.

## Generalization to new purposes

**Deliverables:** create purpose-held-out and screen-family-held-out evaluations, analyze shortcuts and counterexamples, and document language and accessibility coverage.

**Acceptance:** prevent near-duplicate and purpose-pair leakage; publish the purpose taxonomy and per-group results; distinguish newly measured coverage from unsupported domains.

**Why fund it:** recognizing a familiar template is different from applying a purpose to an unfamiliar interface.

## How support is used

[Sponsor on GitHub](https://github.com/sponsors/tac0de) to support open-source implementation, annotation, evaluation, and documentation. Contributions of reproducible failure cases and carefully licensed data are also welcome through [CONTRIBUTING.md](../CONTRIBUTING.md).

Work is prioritized by evidence value, contributor availability, and available resources. Sponsorship is voluntary and does not buy a particular model judgment, delivery date, endorsement, or promised accuracy. Milestones should be marked complete only when their stated evidence is public.
