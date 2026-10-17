# Reproduction and storage

The published adapter depends on the exact base revision in `purposeux.json`.
`purposeux judge` verifies adapter/config checksums before loading. Original base
weights are downloaded from Hugging Face into its shared cache; they are not
copied into every run or bundled with the adapter.

## Run the published artifact

After installing the project as described in the README:

```sh
mkdir -p artifacts
curl -fL https://github.com/tac0de/purpose-ux/releases/download/v0.1.0/purposeux-0.1.0-adapter.tar.gz -o artifacts/purposeux-0.1.0-adapter.tar.gz
curl -fL https://github.com/tac0de/purpose-ux/releases/download/v0.1.0/SHA256SUMS -o artifacts/SHA256SUMS
(cd artifacts && shasum -a 256 -c SHA256SUMS)
tar -xzf artifacts/purposeux-0.1.0-adapter.tar.gz -C artifacts
purposeux judge --data data/test.jsonl --index 0 --adapter artifacts/purposeux-0.1.0
```

The checksums detect accidental file changes; trust in the release source is a
separate consideration. Keep `adapters.safetensors`, `adapter_config.json` and
`purposeux.json` together. `training-report.json` describes the actual training.

## Reproduce the local experiment

Python3.13 and Apple Silicon Metal are required for model execution. Install the
tested dependency versions, then the editable source without changing them:

```sh
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
purposeux doctor
python -m unittest discover -s tests -v
python scripts/local_acceptance.py --iters 64
```

The acceptance command requires an empty `artifacts/local` directory. It genuinely
trains, reloads the adapter onto a fresh base, compares A/B logits and evaluates
both models. It also measures blank-image changes in the A-minus-B margin;
common shifts of both logits do not count as decision sensitivity. It writes
local generated JSON into `reports/`, which is ignored by Git and published as
release assets. The test split is not used to select iterations or learning rate.

`fit_seconds` measures `Trainer.train()`. `training_seconds` includes thumbnail
preparation and a reference inference, but excludes fresh reload verification.
MLX peak memory is not total macOS/system memory. Forward latency excludes image
preprocessing and initial model download/load; it is not end-to-end API latency.
Results may vary across package versions, thermal conditions and hardware.

## Data and bounded artifacts

`node scripts/build_dataset.mjs --check` checks the committed data without
launching a browser. Regeneration requires the documented Playwright CLI in
[DATASET_CARD.md](DATASET_CARD.md); it uses an owned headless browser and closes it.

Use one `.venv` and the shared Hugging Face cache. Training thumbnails live in a
TemporaryDirectory and are removed on exit. A run writes one final adapter and
configuration; there are no per-step checkpoint copies. Existing nonempty run
directories are rejected, so deletion or archival is an explicit owner action.
Retain the published adapter and provenance; remove failed local probe folders
when their evidence is no longer needed. Public release assets contain no private
kernel receipt paths, usernames, credentials or machine identifiers.
