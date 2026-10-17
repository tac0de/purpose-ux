# PurposeUX

[학습 어댑터와 실제 실행 보고서](https://github.com/tac0de/purpose-ux/releases/tag/v0.1.0)는 정규 릴리스 자산으로 제공합니다.
[재현·저장공간 안내](docs/REPRODUCIBILITY.md)에서 어댑터 실행 방법을 확인할 수 있습니다.

**화면을 그 목적에 맞춰 평가합니다.**

PurposeUX는 명시적인 사용자 목적과 스크린샷을 함께 보고, 화면 안의 두 인터페이스 후보 중 하나를 고르는 로컬 연구 도구입니다. 이미 정한 항목을 바로 선택하는 일과 여러 항목을 비교하는 일에는 서로 다른 설계가 필요합니다.

`0.1.0`은 합성 스크린샷 데이터, Apple Silicon용 어댑터 학습, 고정 라벨 추론, 기본 모델과 어댑터의 재현 가능한 비교 평가를 제공하는 정식 도구 릴리스입니다. 시작 모델은 합성 평가 기준을 학습합니다. **일반적인 UX 전문가로 검증되지 않았으며**, 라벨은 사람의 선호도·사용성·접근성·과제 성공률을 측정한 결과가 아닙니다.

[English](README.md) · [데이터 카드](docs/DATASET_CARD.md) · [모델 카드](docs/MODEL_CARD.md) · [로드맵](docs/ROADMAP.md) · [후원](https://github.com/sponsors/tac0de)

## 제공 기능

- 인터페이스 후보 `A`와 `B`를 담은 직접 생성한 합성 화면에 목적과 과제 맥락을 연결합니다.
- 같은 화면의 상반된 목적 예제와 후보 순서 교환 예제를 같은 분할에 유지해 학습·평가 간 누출을 줄입니다.
- Apple Silicon에서 MLX-VLM으로 소형 LoRA 어댑터를 학습합니다.
- 동일한 미사용 평가 레코드와 고정 `A`/`B` 라벨 점수로 기본 모델과 어댑터를 비교합니다.
- 평가 결과를 기계가 읽을 수 있는 파일로 저장해 확인과 재현을 돕습니다.

목적을 명시했을 때 모델의 판단이 달라지는지 살펴보기 위한 출발점입니다. 이 데이터에서 높은 점수를 얻더라도, 확인되는 것은 기록된 조건에서 합성 평가 기준과 일치했다는 사실이며 실제 UX 품질까지 입증하지는 않습니다.

## 빠른 시작

지원하는 로컬 학습 경로는 Apple Silicon Mac, Python 3.13, MLX-VLM 0.7.8입니다. 기준 개발 장비는 메모리 16 GB의 M4 MacBook Air입니다. 다른 운영체제, CUDA, 다른 모델 구조에서의 학습은 이번 릴리스에서 검증하지 않았습니다.

```sh
git clone https://github.com/tac0de/purpose-ux.git
cd purpose-ux
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
purposeux doctor
```

모델 실행에 필요한 기본 모델은 별도로 내려받습니다. 기본 모델의 라이선스와 접근 조건은 코드 라이선스와 별개이므로 [모델 카드](docs/MODEL_CARD.md)를 확인해 주세요.

로컬 시작 어댑터를 학습합니다.

```sh
purposeux train --data data/train.jsonl --output artifacts/local --iters 64
```

학습에 사용하지 않은 레코드 하나의 예측을 확인합니다.

```sh
purposeux judge --data data/test.jsonl --index 0 --adapter artifacts/local
```

기본 모델과 어댑터를 각각 평가합니다.

```sh
purposeux evaluate --data data/test.jsonl --output reports/evaluation-base.json
purposeux evaluate --data data/test.jsonl --adapter artifacts/local --output reports/evaluation-adapter.json
```

두 보고서와 학습 설정을 함께 보관하고, 레코드와 모델 조건이 같은지 확인한 뒤 비교해 주세요. 전체 정확도뿐 아니라 틀린 사례도 살펴보는 것이 좋습니다. 위 명령은 로컬에서 결과를 생성하며, 이 문서에는 실행 전에 가정한 점수를 실측 결과처럼 적지 않습니다.

## 데이터와 적용 범위

시작 데이터는 8개 화면 계열의 합성 레코드 176개로 구성됩니다. 학습 128개, 검증 16개, 시험 32개이며 화면 계열 단위로 각각 6개·1개·1개를 배정합니다. 스키마, 생성 출처, 분할 규칙과 한계는 [데이터 카드](docs/DATASET_CARD.md)에 정리되어 있습니다.

학습 정답의 근거는 `synthetic_rubric`입니다. 사람의 선호도 라벨이나 측정된 과제 성공률은 없습니다. `T`/`N`/`U` 계약 검사용 픽스처는 학습된 이진 `A`/`B` 헤드와 분리되어 있으며, 해당 출력의 학습 지원을 입증하지 않습니다.

## 결과 해석

가설 탐색, 목적에 대한 민감도 확인, 평가 데이터 개선에 사용해 주세요. 실제 사용자에게 영향을 주는 결정은 관련 UX·접근성 전문성을 갖춘 사람이 검토해야 합니다. 모델의 라벨을 사용성 조사, 접근성 감사, 인터페이스 효과의 증거로 제시해서는 안 됩니다.

외부 스크린샷에는 개인정보나 기밀이 포함될 수 있습니다. 기본 데이터는 합성 화면이지만, 추가하는 데이터에는 적절한 사용 권한·처리 방식·출처 기록이 필요합니다.

## 연구 후원

[GitHub Sponsors](https://github.com/sponsors/tac0de)를 통한 후원은 사람의 주석, 외부 과제 데이터, 보정 평가, 새로운 목적으로의 일반화 검증을 지원합니다. 예정 산출물과 확인 기준은 [로드맵](docs/ROADMAP.md)에 정리했습니다.

후원은 오픈소스 개발을 자발적으로 지원하는 방식입니다. 특정 결과나 납기, 모델 성능을 구매하거나 보장받는 방식은 아닙니다. 재현 가능한 실패 사례, 데이터 검토, 평가 개선도 도움이 됩니다. [기여 안내](CONTRIBUTING.md)를 확인해 주세요.

## 라이선스

저장소 라이선스는 [LICENSE](LICENSE)를 확인해 주세요. 기본 모델과 외부 데이터에는 각각의 이용 조건이 적용됩니다. 기본 데이터의 출처와 라이선스 범위는 [데이터 카드](docs/DATASET_CARD.md)에 기록합니다.
