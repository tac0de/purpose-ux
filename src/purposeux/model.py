"""Pinned MLX implementation; imports happen only for local model commands."""
import gc
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import tempfile
import time

from .contracts import BASE_MODEL, BASE_REVISION, prompt, read_records, sha256, verify_adapter


def environment():
    import mlx.core as mx
    return {'metal_available': mx.metal.is_available(),
            'versions': {name: version(name) for name in ('mlx', 'mlx-vlm', 'transformers', 'Pillow')},
            'base_model': BASE_MODEL, 'base_revision': BASE_REVISION}


def open_model(adapter=None):
    from mlx_vlm import load
    if adapter:
        verify_adapter(adapter)
    model, processor = load(BASE_MODEL, revision=BASE_REVISION,
                            adapter_path=str(adapter) if adapter else None)
    model.eval()
    return model, processor


def image_for(record, long_side=640, blank=False):
    from PIL import Image
    with Image.open(record['_image_path']) as source:
        if source.width * source.height > 32_000_000:
            raise ValueError('Image exceeds 32 megapixels')
        image = source.convert('RGB')
    image.thumbnail((long_side, long_side))
    if blank:
        image = Image.new('RGB', image.size, 'white')
    return image


def prepare(model, processor, record, blank=False):
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import process_inputs_with_fallback
    text = apply_chat_template(processor, model.config, prompt(record), num_images=1,
                               add_generation_prompt=True, enable_thinking=False)
    return process_inputs_with_fallback(processor=processor, prompts=[text],
                                        images=[image_for(record, blank=blank)], audio=None,
                                        add_special_tokens=False)


def score(model, processor, record, blank=False):
    import mlx.core as mx
    from mlx_vlm.trainer.vlm.sft.runtime import forward_vlm_logits
    model.eval()
    inputs = prepare(model, processor, record, blank=blank)
    tokenizer = getattr(processor, 'tokenizer', processor)
    tokens = [tokenizer.encode(label, add_special_tokens=False) for label in ('A', 'B')]
    if any(len(value) != 1 for value in tokens):
        raise ValueError('A/B labels must be single tokens in the pinned tokenizer')
    started = time.perf_counter()
    output = forward_vlm_logits(model, inputs['input_ids'], inputs['attention_mask'], inputs)
    logits = output[0, -1, mx.array([value[0] for value in tokens])]
    probabilities = mx.softmax(logits)
    mx.eval(logits, probabilities)
    values = probabilities.tolist()
    result = {'choice': ('A', 'B')[int(values[1] > values[0])],
              'choice_probabilities': dict(zip(('A', 'B'), values)),
              'calibrated': False, 'ab_logits': logits.tolist(),
              'forward_seconds': time.perf_counter() - started,
              'input_tokens': int(inputs['input_ids'].shape[-1])}
    del output, inputs, logits, probabilities
    mx.clear_cache()
    return result


def parameter_digest(model):
    import mlx.core as mx
    from mlx.utils import tree_flatten
    state = tree_flatten(model.trainable_parameters())
    digest = hashlib.sha256()
    count = 0
    for name, value in sorted(state):
        mx.eval(value)
        digest.update(name.encode())
        digest.update(value.astype(mx.float32).__array__().tobytes())
        count += value.size
    return digest.hexdigest(), count


def train(data, output, iters=64, learning_rate=0.0001, seed=17):
    import mlx.core as mx
    import numpy as np
    from mlx_vlm.trainer import Trainer, VLMTrainingArgs, prepare_model_for_training
    if not isinstance(iters, int) or iters < 1 or iters > 10000:
        raise ValueError('iters must be between 1 and 10000')
    if not math.isfinite(learning_rate) or learning_rate <= 0:
        raise ValueError('learning rate must be positive and finite')
    records = read_records(data, labeled=True)
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Choose an empty output directory; existing runs are never overwritten')
    output.mkdir(parents=True, exist_ok=True)
    mx.random.seed(seed)
    np.random.seed(seed)
    model, processor = open_model()
    prepare_model_for_training(model, lora_rank=8, lora_alpha=16,
                               target_modules=['q_proj', 'v_proj'])
    before, parameter_count = parameter_digest(model)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='purposeux-images-') as temporary:
        rows, resized = [], {}
        for record in records:
            image = record['_image_path']
            if image not in resized:
                path = Path(temporary) / (hashlib.sha256(image.encode()).hexdigest() + '.png')
                image_for(record).save(path)
                resized[image] = str(path)
            rows.append({'images': [resized[image]], 'messages': [
                {'role': 'user', 'content': prompt(record)},
                {'role': 'assistant', 'content': record['label']} ]})
        args = VLMTrainingArgs(iters=iters, batch_size=1, max_seq_length=1536,
            learning_rate=learning_rate, train_on_completions=True, assistant_id=None,
            grad_checkpoint=True, steps_per_report=max(1, min(8, iters)),
            steps_per_eval=None, steps_per_save=iters+1, cache_size=1,
            adapter_file=str(output / 'adapters.safetensors'))
        trainer = Trainer(model, args, train_dataset=rows, processing_class=processor, seed=seed)
        example = trainer.train_dataset[0]
        # MLX array indexing treats booleans differently from NumPy's selection.
        target_ids = np.asarray(example['input_ids'])[np.asarray(example['completion_mask'], dtype=bool)]
        tokenizer = getattr(processor, 'tokenizer', processor)
        probe = {'input_tokens': int(example['input_ids'].size),
                 'pixel_shape': list(example['pixel_values'].shape),
                 'image_grid_shape': list(example['image_grid_thw'].shape),
                 'supervised_tokens': int(target_ids.size),
                 'supervised_text': tokenizer.decode(target_ids.tolist())}
        if probe['input_tokens'] > args.max_seq_length:
            raise ValueError('Input would truncate completion targets; reduce resolution/prompt')
        if probe['supervised_tokens'] < 1 or records[0]['label'] not in probe['supervised_text']:
            raise ValueError('Expected A/B completion supervision missing')
        print(json.dumps({'image_supervision_probe': probe}), flush=True)
        fit_started = time.perf_counter()
        metrics = trainer.train()
        fit_seconds = time.perf_counter() - fit_started
        if not math.isfinite(float(metrics.get('train_loss', metrics.get('loss', float('nan'))))):
            raise ValueError('Nonfinite or missing training loss')
        trainer.save_adapter(output / 'adapters.safetensors')
        history = list(trainer.log_history)
        after, _ = parameter_digest(model)
        if before == after:
            raise ValueError('Training did not change adapter weights')
        model.eval()
        reference = score(model, processor, records[0])
    elapsed = time.perf_counter() - started
    peak = mx.get_peak_memory()/1024**3
    metadata = {'format_version': 1, 'base_model': BASE_MODEL, 'base_revision': BASE_REVISION,
                'labels': ['A', 'B'], 'calibrated': False, 'label_source': 'synthetic_rubric',
                'dataset_sha256': sha256(data), 'iterations': iters, 'seed': seed,
                'learning_rate': learning_rate, 'rank': 8, 'alpha': 16,
                'long_side': 640, 'trainable_parameters': parameter_count,
                'initial_weights_sha256': before, 'final_weights_sha256': after,
                'sha256': {name: sha256(output/name) for name in ('adapters.safetensors', 'adapter_config.json')}}
    (output/'purposeux.json').write_text(json.dumps(metadata, indent=2)+'\n')
    result = {'environment': environment(), 'training': metadata, 'probe': probe,
              'metrics': metrics, 'history': history, 'training_seconds': elapsed,
              'fit_seconds': fit_seconds,
              'mlx_peak_gib': peak, 'weights_changed': True}
    del trainer, model, processor
    gc.collect()
    mx.clear_cache()
    fresh, processor = open_model(output)
    reloaded = score(fresh, processor, records[0])
    difference = max(abs(a-b) for a,b in zip(reference['ab_logits'], reloaded['ab_logits']))
    if difference > 0.01 or reference['choice'] != reloaded['choice']:
        raise ValueError('Fresh adapter reload does not preserve logits/choice')
    result['reload'] = {'max_ab_logit_difference': difference, 'tolerance': 0.01,
                        'choice_equal': True, 'choice': reloaded['choice']}
    (output/'training-report.json').write_text(json.dumps(result, indent=2)+'\n')
    del fresh, processor
    gc.collect()
    mx.clear_cache()
    return result


def evaluate(data, adapter=None, limit=None, ablate=False):
    import mlx.core as mx
    records = read_records(data, labeled=True)
    if limit:
        records = records[:limit]
    model, processor = open_model(adapter)
    predictions = []
    for index, record in enumerate(records):
        prediction = score(model, processor, record)
        prediction.update(id=record['id'], group=record['group'], expected=record['label'])
        if ablate:
            blank = score(model, processor, record, blank=True)
            prediction['blank_ab_logits'] = blank['ab_logits']
            prediction['image_logit_delta'] = max(abs(a-b)for a,b in zip(prediction['ab_logits'],blank['ab_logits']))
            actual_margin = prediction['ab_logits'][0] - prediction['ab_logits'][1]
            blank_margin = blank['ab_logits'][0] - blank['ab_logits'][1]
            prediction['image_margin_delta'] = abs(actual_margin - blank_margin)
            prediction['image_probability_delta'] = abs(prediction['choice_probabilities']['A'] - blank['choice_probabilities']['A'])
        predictions.append(prediction)
        print(f'evaluated {index+1}/{len(records)}', flush=True)
    from collections import defaultdict
    groups = defaultdict(list)
    for value in predictions:
        groups[value['group']].append(value)
    accuracy = sum(p['choice']==p['expected'] for p in predictions)/len(predictions)
    # Each full group contains both goals and both candidate orders.
    complete = [values for values in groups.values() if len(values)==4]
    order_pairs, purpose_pairs = [], []
    by_id = {p['id']:p for p in predictions}
    for record in records:
        # Dataset IDs end in '-<order>-<goal>'; derive pairing without feeding IDs to model.
        parts = record['id'].rsplit('-', 2)
        if len(parts)!=3:
            continue
        group, order, goal = parts
        if order=='0' and (other:=by_id.get(f'{group}-1-{goal}')):
            order_pairs.append(by_id[record['id']]['choice'] != other['choice'])
        if goal=='focus' and (other:=by_id.get(f'{group}-{order}-explore')):
            purpose_pairs.append(by_id[record['id']]['choice'] != other['choice'])
    result={'dataset_sha256':sha256(data),'base_model':BASE_MODEL,'base_revision':BASE_REVISION,
            'adapter_sha256':sha256(Path(adapter)/'adapters.safetensors') if adapter else None,
            'label_source':'synthetic_rubric','count':len(predictions),'group_count':len(groups),
            'accuracy':accuracy,'complete_group_accuracy':sum(all(p['choice']==p['expected']for p in g)for g in complete)/len(complete) if complete else None,
            'order_consistency':sum(order_pairs)/len(order_pairs) if order_pairs else None,
            'purpose_flip_consistency':sum(purpose_pairs)/len(purpose_pairs) if purpose_pairs else None,
            'calibrated':False,'predictions':predictions,'mlx_peak_gib':mx.get_peak_memory()/1024**3,
            'limits':'Dependent synthetic comparisons, one held-out family; no human UX/task-success evidence.'}
    del model,processor
    gc.collect()
    mx.clear_cache()
    return result
