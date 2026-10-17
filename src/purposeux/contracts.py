"""Input contracts intentionally independent of Metal/model downloads."""
import hashlib
import json
from pathlib import Path

BASE_MODEL = 'mlx-community/Qwen3.5-0.8B-4bit'
BASE_REVISION = 'da28692b5f139cb0ec58a356b437486b7dac7462'
CONTEXT_KEYS = ('audience', 'task', 'evidence_scope', 'viewport', 'language')
INSTRUCTION = ('Compare the two interface designs labeled A and B in the image. '
               'Which design better supports the stated purpose for this user? '
               'Use only the visible interface and given context. '
               'Answer with exactly one letter: A or B.\n')


def prompt(record):
    purpose = record.get('purpose')
    if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 2000:
        raise ValueError('purpose must contain 1..2000 characters')
    raw = record.get('context', {})
    if not isinstance(raw, dict):
        raise ValueError('context must be an object')
    context = {}
    for key in CONTEXT_KEYS:
        if key not in raw:
            continue
        if key == 'viewport':
            if not isinstance(raw[key], dict):
                raise ValueError('viewport must be an object')
            context[key] = {dimension: raw[key][dimension] for dimension in ('width', 'height') if dimension in raw[key]}
            if any(type(value) is not int or not 1 <= value <= 8192 for value in context[key].values()):
                raise ValueError('viewport dimensions must be integers in 1..8192')
        else:
            if not isinstance(raw[key], str) or len(raw[key]) > 2000:
                raise ValueError('context text fields must be strings of at most 2000 characters')
            context[key] = raw[key]
    text = json.dumps(context, ensure_ascii=False, sort_keys=True)
    if len(text) > 4000:
        raise ValueError('context is too long')
    return INSTRUCTION + 'Purpose: ' + purpose.strip() + '\nContext: ' + text


def read_records(path, labeled=False):
    path = Path(path).resolve()
    result = []
    text = path.read_text()
    lines = [json.dumps(json.loads(text))] if path.suffix == '.json' else text.splitlines()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f'line {number}: expected an object')
        prompt(record)
        if labeled and record.get('label') not in ('A', 'B'):
            raise ValueError('This release trains/evaluates binary A/B labels only')
        value = record.get('image')
        if not isinstance(value, str) or '://' in value:
            raise ValueError('image must name a local file, not a URL')
        image = Path(value)
        if not image.is_absolute():
            root = path.parent.parent if value.startswith('data/') and path.parent.name == 'data' else path.parent
            image = root / image
        image = image.resolve(strict=True)
        if not image.is_file() or image.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
            raise ValueError('image must be a local regular PNG/JPEG file')
        if image.stat().st_size > 10 * 1024 ** 2:
            raise ValueError('image exceeds 10MiB limit')
        record['_image_path'] = str(image)
        result.append(record)
    if not result:
        raise ValueError('dataset is empty')
    return result


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_adapter(directory):
    directory = Path(directory)
    metadata = json.loads((directory / 'purposeux.json').read_text())
    if metadata['base_model'] != BASE_MODEL or metadata['base_revision'] != BASE_REVISION:
        raise ValueError('Adapter base model/revision mismatch')
    for name in ('adapters.safetensors', 'adapter_config.json'):
        if sha256(directory / name) != metadata['sha256'][name]:
            raise ValueError('Adapter integrity mismatch: ' + name)
    if metadata.get('labels') != ['A', 'B']:
        raise ValueError('Unsupported adapter label contract')
    return metadata
