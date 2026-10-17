# Purpose-UX synthetic comparison fixtures

This is an original, small synthetic dataset for a local proof of concept. Labels
come from an explicit author-written rubric, not human preference ratings, expert
consensus, usability tests, conversion measurements or production telemetry. A
model trained on these labels learns this narrow rubric; it does not become a
validated judge of general UX quality.

## Contents and input contract

Each JSONL row contains one **composite screenshot** showing Candidate A and
Candidate B, a short purpose brief (`purpose`), structured task context (`context`),
and a target label. Screens are static fictional interfaces made with HTML/CSS;
the visible buttons have no working service behind them. The examples need no
illustrative photos, outside screenshots, logos or third-party assets.

| File | Rows | Groups | Families | Labels |
| --- | ---: | ---: | ---: | --- |
| `data/train.jsonl` | 128 | 32 | 6 | 64 A / 64 B |
| `data/val.jsonl` | 16 | 4 | 1 | 8 A / 8 B |
| `data/test.jsonl` | 32 | 8 | 1 | 16 A / 16 B |
| `data/coverage.jsonl` | 6 | 6 | fixture-only | 2 T / 2 N / 2 U |

There are 88 main PNGs plus 6 coverage PNGs, all 960 × 640 CSS pixels. Each
candidate occupies one half of the same image. `data/html/` preserves editable
sources; `data/render_manifest.json` maps images to sources. `data/render_check.json`
records automatic geometry checks, not a human visual-quality rating.

Model input **must include only `purpose`, `context`, and image pixels**. Treat
`id`, `group`, `split`, `family`, image filenames, `label`, `label_source`,
`rationale`, `candidate_order`, and `rubric_version` as metadata. Do not serialize
the whole row into a training prompt. In particular, candidate order identifies
the generation template and would leak the answer when combined with the task.

## Rubric

For a returning visitor who has already chosen an option, prefer a visible direct
action for that named option over an interface that requires opening another
screen before taking that action. For a visitor who is still deciding, prefer
visible comparison criteria matching the stated purpose over a screen that
foregrounds one selected option and hides the alternatives.

- **A / B:** that candidate better satisfies the stated static-screen rubric.
- **T:** the supplied evidence supports a tie (the fixture uses identical designs).
- **N:** neither design provides the requested selected option/action.
- **U:** the question requires evidence missing from a static screenshot, such as
  measured successful enrollments over time.

T/N/U are **coverage fixtures only**, excluded from the A/B training, validation
and held-out test sets. Their presence does not mean the released model was
trained or evaluated adequately on those classes. A binary classifier must not
claim five-class competence.

Every main group has two screenshot orders, and each image is evaluated under two
opposing purposes. The same image therefore receives A for one purpose and B for
the other. Swapping candidates also flips the answer. These four rows remain in
the same split. They are dependent examples, not four independent observations.

## Split policy and provenance

Training families are courses, rail journeys, creative workshops, jobs, events and
workspaces (6, 6, 5, 5, 5, 5 groups). Library borrowing is validation-only (4 groups);
local civic services are test-only (8 groups). Family, group and byte-identical
images are isolated across train/validation/test. The coverage fixtures use a
separate fictional brand. All text, layouts, colors, HTML and screenshots were
authored for this repository in October 2026; there are no real providers, scraped
sites, external image assets, personal data or genuine operational statistics.

The shared renderer and two broad design patterns **do** cross splits. Family
holdout tests domain transfer within this generator; it does not establish
generalization to real websites, independent design systems, Korean interfaces,
mobile layouts, unseen interaction patterns or designer judgment. Content and
palette variations within a family are intentionally modest.

## Reproduction and checks

Requires Node.js, Microsoft Playwright CLI (`playwright-cli`) and its available
Chromium browser. No npm dependencies, web server or network assets are needed by
the builder. If the CLI is not on PATH, set `PLAYWRIGHT_CLI` to its executable.

```sh
node scripts/build_dataset.mjs                  # Write original sources and render all PNGs
node scripts/build_dataset.mjs --manifest-only  # Sources/JSONL only; does not create PNGs
node scripts/build_dataset.mjs --check          # Read-only dataset integrity checks
```

The renderer uses an isolated, explicitly headless browser, fixed viewport,
device scale factor 1, font readiness and an animation frame before capture. It
checks content boxes for overflow/clipping and closes only its own browser
session in a `finally` block. Private CLI state is temporary and outside the
repository. Exact pixels can change with browser, OS or Arial font availability;
the semantic fixtures and ordering are deterministic. A screenshot is not a
record of a working user flow.

Direct visual inspection covered `courses-01-original.png`,
`library-01-original.png` and `local_services-01-reversed.png`: both candidates,
their headings, comparison rows and primary actions were readable at the source
size with no visible clipping. Automatic geometry checks cover all 94 images.
This does not establish readability at every model preprocessing resolution,
actual keyboard/screen-reader behavior or responsive behavior.

## Limitations and intended use

Use this data to demonstrate purpose conditioning, candidate order sensitivity,
small local fine-tuning, and honest evaluation of a known synthetic task. The
sample is small, English-only, template-generated and correlated. Frequent phrases
and coarse direct-action/comparison patterns can be learned as shortcuts.
Purpose-only and image-only ablations and purpose-reversal consistency are useful
diagnostics; even strong held-out accuracy remains synthetic-rubric evidence.

Do not use scores as evidence of conversion lift, accessibility compliance,
security, fairness, legal compliance, actual task completion, general aesthetic
quality or readiness to replace human design work. Interaction, responsive layout,
loading, errors, real content and user needs require additional evidence.
