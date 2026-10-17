"""Actual Metal training/reload/evaluation acceptance, no simulated model outputs."""
import argparse
import json
from pathlib import Path
import time

from purposeux.model import environment, evaluate, train


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--iters',type=int,default=64)
    args=parser.parse_args()
    reports=Path('reports');reports.mkdir(exist_ok=True)
    if not environment()['metal_available']:
        raise RuntimeError('Acceptance requires an actual Metal device')
    started=time.perf_counter()
    result=train('data/train.jsonl','artifacts/local',iters=args.iters)
    (reports/'local-run.json').write_text(json.dumps(result,indent=2)+'\n')
    baseline=evaluate('data/test.jsonl',ablate=False)
    (reports/'evaluation-base.json').write_text(json.dumps(baseline,indent=2)+'\n')
    adapted=evaluate('data/test.jsonl','artifacts/local',ablate=True)
    (reports/'evaluation-adapter.json').write_text(json.dumps(adapted,indent=2)+'\n')
    if not any(p['image_margin_delta']>1e-5 for p in adapted['predictions']):
        raise RuntimeError('No detectable image sensitivity')
    summary={'release':'0.1.0','hardware':'Apple M4 MacBook Air, 16GB unified memory',
             'training_seconds':result['training_seconds'],'fit_seconds':result['fit_seconds'],
             'mlx_peak_gib':result['mlx_peak_gib'],
             'iterations':args.iters,'weights_changed':result['weights_changed'],'reload':result['reload'],
             'trainable_parameters':result['training']['trainable_parameters'],
             'base_accuracy':baseline['accuracy'],'adapter_accuracy':adapted['accuracy'],
             'accuracy_delta':adapted['accuracy']-baseline['accuracy'],
             'order_consistency':adapted['order_consistency'],
             'purpose_flip_consistency':adapted['purpose_flip_consistency'],
             'test_records':adapted['count'],'test_groups':adapted['group_count'],
             'total_seconds':time.perf_counter()-started,
             'limits':['Synthetic rubric labels and one held-out family; not human UX evidence.',
                       'Conditional A/B probabilities are not calibrated confidence.',
                       'A regular toolkit release; model is a small synthetic starter baseline.']}
    (reports/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
