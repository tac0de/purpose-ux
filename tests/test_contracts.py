import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from purposeux.contracts import BASE_MODEL, BASE_REVISION, prompt, read_records, sha256, verify_adapter

ROOT = Path(__file__).resolve().parents[1]


class Contracts(unittest.TestCase):
    def test_prompt_excludes_targets_and_metadata(self):
        record={'purpose':'Compare options','label':'TARGET_SECRET','rationale':'RATIONAL_SECRET',
                'candidate_order':['SECRET_ORDER'],'id':'SECRET_ID','family':'SECRET_FAMILY',
                'context':{'audience':'reader','label':'NESTED_SECRET',
                           'viewport':{'width':960,'height':640,'label':'DEEP_SECRET'}}}
        result=prompt(record)
        self.assertIn('Compare options',result)
        self.assertNotIn('SECRET',result)

    def test_rejects_invalid_context_and_purpose(self):
        for record in [{},{'purpose':''},{'purpose':'x','context':[]},
                       {'purpose':'x','context':{'viewport':{'width':-1}}}]:
            with self.assertRaises(ValueError):prompt(record)

    def test_input_rejects_remote_missing_and_untrained_labels(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'records.jsonl'
            for image in ['https://example.org/a.png','missing.png']:
                path.write_text(json.dumps({'purpose':'x','image':image,'label':'A'}))
                with self.assertRaises((ValueError,OSError)):read_records(path,True)
            path.write_text(json.dumps({'purpose':'x','image':'missing.png','label':'T'}))
            with self.assertRaisesRegex(ValueError,'binary'):read_records(path,True)

    def test_local_sample_is_readable_without_label_required(self):
        rows=read_records(ROOT/'data/test.jsonl')
        self.assertEqual(len(rows),32)
        self.assertTrue(Path(rows[0]['_image_path']).is_file())

    def test_adapter_integrity_and_revision_are_enforced(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)
            for name in ['adapters.safetensors','adapter_config.json']:(path/name).write_text('fixture')
            metadata={'base_model':BASE_MODEL,'base_revision':BASE_REVISION,'labels':['A','B'],
                      'sha256':{name:sha256(path/name)for name in ['adapters.safetensors','adapter_config.json']}}
            (path/'purposeux.json').write_text(json.dumps(metadata));verify_adapter(path)
            (path/'adapters.safetensors').write_text('changed')
            with self.assertRaisesRegex(ValueError,'integrity'):verify_adapter(path)
            metadata['base_revision']='changed';(path/'purposeux.json').write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError,'revision'):verify_adapter(path)

    def test_group_family_and_image_separation_and_counterfactuals(self):
        splits={name:read_records(ROOT/f'data/{name}.jsonl',True)for name in ['train','val','test']}
        for field in ['family','group','image']:
            values=[{row[field]for row in rows}for rows in splits.values()]
            for i in range(3):
                for j in range(i):self.assertFalse(values[i]&values[j],field)
        for split,rows in splits.items():
            self.assertEqual(sum(r['label']=='A'for r in rows),len(rows)//2)
            for image in {r['image']for r in rows}:
                pair=[r for r in rows if r['image']==image]
                self.assertEqual(len(pair),2)
                self.assertNotEqual(pair[0]['label'],pair[1]['label'])
                self.assertNotEqual(pair[0]['purpose'],pair[1]['purpose'])

    def test_release_documents_and_funding(self):
        for file in ['LICENSE','README.md','README.ko.md','docs/MODEL_CARD.md','docs/DATASET_CARD.md','docs/ROADMAP.md']:
            self.assertTrue((ROOT/file).stat().st_size>20,file)
        self.assertIn('tac0de',(ROOT/'.github/FUNDING.yml').read_text())

    def test_cli_failure_is_local_and_nonzero(self):
        result=subprocess.run([sys.executable,'-m','purposeux','judge','--data','missing.jsonl'],
                              capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode,1)
        self.assertIn('purposeux:',result.stderr)


if __name__=='__main__':unittest.main()
