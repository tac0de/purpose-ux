# PurposeUX starter model card

## Release scope

PurposeUX 0.1.0 is an open-source research toolkit release. Its local LoRA training path produces a **synthetic starter adapter**, not a generally validated UX evaluator. A locally generated adapter must be identified by its own training configuration and evaluation reports; running the command alone establishes no performance claim.

The reference base model is [`mlx-community/Qwen3.5-0.8B-4bit`](https://huggingface.co/mlx-community/Qwen3.5-0.8B-4bit), revision `da28692b5f139cb0ec58a356b437486b7dac7462`, used through MLX-VLM 0.7.8. Base-model files are downloaded separately and are not relicensed by this repository. Check the upstream model card and license before downloading or redistributing model artifacts.

## Task and interface

The model receives a composite screenshot showing interface candidates `A` and `B`, an explicit purpose, and task context. Inference scores the next-token labels `A` and `B` under a fixed prompt and chooses between the interface candidates. It does not produce a validated free-form UX audit. Relative label scores are not calibrated probabilities that a screen is good or that a user will succeed.

Contract fixtures that exercise `T`/`N`/`U` are outside the trained binary head. Their presence does not mean the adapter has learned abstention, uncertainty, ties, or any other additional outcome.

## Training data

The original synthetic corpus contains 176 records in eight screen families, split into 128 training, 16 validation, and 32 test records. Entire screen families are held out: six for training, one for validation, and one for testing. Opposing-purpose examples for the same screen and candidate-order swaps remain in the same split.

Labels have the provenance `synthetic_rubric`. There are no human preference annotations and no measured task-success labels. See the [dataset card](DATASET_CARD.md) for the exact schema, generation method, licensing scope, and known confounds.

## Training and reproducibility

The supported reference environment is an Apple Silicon M4 MacBook Air with 16 GB of memory and Python 3.13. The implementation uses quantized base-model inference and LoRA adaptation through MLX-VLM. Other hardware and architectures are unqualified unless a separate run documents them.

Use the repository's `purposeux train` command and retain the resulting configuration, adapter files, package versions, data version, and evaluation reports. Iteration count is a run setting, not evidence that training converged. The README's short training command is a reproducible starting configuration rather than an optimized training recipe.

## Evaluation and claims

Run the same held-out data once without `--adapter` and once with the local adapter. Store the outputs separately, for example `reports/evaluation-base.json` and `reports/evaluation-adapter.json`. Compare matching prompts, records, runtime settings, and label-scoring behavior.

Interpret any result as agreement with the synthetic rubric for that run. The small test set has limited coverage, and related templates can share visual or textual shortcuts even when families are split. Candidate-order swaps and opposing-purpose pairs are useful diagnostics but do not eliminate those confounds.

No human-preference improvement, real-task benefit, accessibility compliance, robustness guarantee, or generalization to arbitrary interfaces is established by this release. A successful training run, a unit test, and a held-out score each establish different, limited facts.

## Intended use

- Reproduce a small local vision-language adaptation experiment.
- Study whether explicit purpose changes pairwise UX judgments.
- Inspect candidate-order sensitivity, purpose-pair failures, and data shortcuts.
- Build better datasets and evaluation methods before broader claims.

## Limitations and unsuitable uses

- The rubric reflects its authors' synthetic design assumptions, not a representative population.
- Rendered fixtures differ from live applications, interaction histories, and assistive-technology experiences.
- A screenshot omits behavior, errors, latency, keyboard navigation, and task outcomes.
- Binary choice forces a preference even if both candidates are poor or the evidence is insufficient.
- Language, visual style, purpose, accessibility, and cultural coverage are narrow.
- Adapter behavior can be sensitive to prompt formatting, label tokenization, model revision, and package version.

Do not use this adapter as the sole basis for consequential product decisions, an accessibility audit, or a claim about user welfare. External screenshots require appropriate permission and privacy handling. The [roadmap](ROADMAP.md) describes the evidence needed to broaden the supported claims.

## Licensing

The repository's [LICENSE](../LICENSE) covers its stated code scope. Base-model terms and external data terms remain separate. Do not assume that the repository license grants redistribution rights to a downloaded model or to third-party screenshots.
