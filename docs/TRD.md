# PurposeUX technical and release contract

## Define
Create an open-source, purpose-conditioned web-design/UX visual decision model
that genuinely trains, saves, reloads and executes on the user's M4 MacBook Air
with 16GB unified memory. Publish a regular GitHub release aimed at voluntary
sponsorship. The first trained artifact is a synthetic-rubric binary A/B baseline,
not a validated predictor of human task success or a universal UX evaluator.

Acceptance:
- L1: actual Metal-backed QLoRA steps change trainable weights with finite loss;
  record runtime, memory, image tokens and supervised targets.
- L2: saved adapter reloads onto the exact pinned base and preserves same-input
  A/B logits within an explicit numerical tolerance; CLI takes a purpose and image.
- D1: original screenshot data is family/group-disjoint across splits, balanced,
  with purpose and order counterfactuals grouped together and no target leakage.
- E1: report base and adapted held-out accuracy, order consistency and purpose
  counterfactual accuracy separately, plus image ablation evidence. Synthetic
  results are not real-world usability or calibration measurements.
- R1: installable source, original sample data, model card, actual results,
  adapter checksums, license/notices, contribution and funded roadmap, Sponsors
  link, public repository and a non-prerelease versioned GitHub release.

## Plan
Reuse MLX-VLM 0.7.8 and its fixed image-aware/completion-only Trainer API, rather
than implementing a transformer or classifier training stack from scratch.
Start with a short real backward/save/reload probe, then a bounded full baseline
run and a held-out comparison. Render original functional UIs headlessly. Keep
parallel writes separated into source/training, dataset and release prose.
Publish only after source, packaging and actual local execution are reviewed.
Do not deploy a website, buy compute, upload private screens, change payment
settings or claim sponsors/revenue have been obtained.

## Design / TRD
Base: mlx-community/Qwen3.5-0.8B-4bit, revision
da28692b5f139cb0ec58a356b437486b7dac7462 (Apache-2.0 base family).
Runtime: Python3.13, mlx0.32.4, mlx-vlm0.7.8. QLoRA freezes the quantized base;
rank8 adapters target language q_proj/v_proj. Images remain actual processor
inputs; completion-only loss supervises assistant A/B tokens and EOS. Inference
scores those two next-token logits in one forward pass, with no free-text decode.
Conditional A/B softmax values are not calibrated confidence or absolute quality.

Input: original composite screenshot labeled A/B, purpose string and task context.
Prompt allowlist excludes label/rationale/ID/family/order/source metadata.
Only bounded local regular PNG/JPEG images are accepted, no remote image URLs.
Preprocess images consistently to a bounded long side for train and inference;
preserve the source screenshots and record the transform. Fail on empty labels,
missing images, truncated-away supervision, nonfinite loss or invalid parameters.
Output: choice A/B, conditional probabilities, calibration=false, model revision
and adapter identification. T/N/U fixtures document future contract only.

Dataset:128 train/16validation/32test records, original synthetic_rubric labels,
six/one/one families respectively. Both purposes and image-order variants of each
group belong to one split. This is a tiny controlled demonstration benchmark.
No human annotators or observed user sessions are fabricated.

Data ERD (file-based, no service database): Family1:N Group; Split1:N Group;
Group1:N Render; Render1:N Example; Example references one Purpose and one label.
TrainRun references pinned BaseRevision, dataset digest and AdapterArtifact;
EvaluationRun references dataset digest, BaseRevision and optional AdapterArtifact.
Adapter stores training configuration and integrity metadata. No migrations.

CLI: purposeux doctor; purposeux train --data PATH --output DIR;
purposeux judge --data PATH --index N [--adapter DIR];
purposeux evaluate --data PATH [--adapter DIR] --output JSON.
Support explicit JSON records for user-owned screens. Keep failed requests local
and bounded; do not fetch screen URLs or execute supplied markup during judging.

Storage: one shared base snapshot and one .venv; generate training thumbnails in
a temporary directory with cleanup. No retained intermediate checkpoints; final
adapters and reports only. Git ignores weights/cache/venv. Release adapter archive
includes the adapter configuration and base revision, not copied base weights.

Risks: tiny synthetic data and style shortcuts, target leakage, small text after
resizing, A/B positional bias, prefix mismatch, quantized training compatibility,
thermal slowdown, peak unified memory and storage. Resolve compatibility with an
actual micropreflight; judge quality only within the recorded held-out scope.

## Verification and review strategy
Focused standard-library tests check contracts, prompt allowlist, grouped splits,
artifact verification and input rejection without downloading weights. A real
local pipeline command separately records image-aware training, finite nonzero
updates, fresh reload equality, baseline/adapted inference and evaluation. Directly
inspect representative dataset renders. Independent native review checks training
semantics, evaluation leakage, publication claims and release contents. Automated
checks do not establish human usability, universal visual quality or sponsorship.

## Research provenance
Research Intelligence package
pkg_4c7a0adf2bc6544645e49705cbd636d12cba0d692fbfbbf904d7c6d3dac50e18
contains pinned MLX-VLM0.7.8 source observations (caller-supplied acquisition;
static evidence only). Decision: reuse current Trainer/image masking/save-reload
APIs, conditional on actual local execution. REA may preserve the reference
bundle's integrity; it does not prove semantic correctness or training quality.
