"""Measure candidate-source length with the frozen tokenizer; never select test items.

The text reconstruction joins the pinned .whole units with one ASCII space.
Even fitting without task instructions does not prove that a final transfer
prompt fits or that its intervention and annotations are scientifically valid.
"""

import argparse
import csv
import hashlib
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from mim_llm.foundation.codec import FrozenTokenizer
from mim_llm.foundation.plan import load_plan
from mim_llm.q3a.io import read_json, sha256, source_sha256, write_json


def audit(directory, plan_path, candidates_path):
    directory = Path(directory)
    candidates = read_json(candidates_path)
    source = next(s for s in candidates['sources'] if s['id'] == 'naturalstories')
    for name, expected in source['files'].items():
        if sha256(directory / name) != expected:
            raise ValueError(f'Candidate source bytes changed: {name}')
    units = defaultdict(dict)
    with (directory / 'words.tsv').open(encoding='utf-8', newline='') as handle:
        for code, text in csv.reader(handle, delimiter='\t'):
            story, position, level = code.split('.')
            if level != 'whole':
                continue
            position = int(position)
            if position in units[story]:
                raise ValueError('Duplicate whole-unit position')
            units[story][position] = text
    if len(units) != source['source_story_clusters_observed']:
        raise ValueError('Changed parent story count')
    plan = load_plan(plan_path)
    tokenizer = FrozenTokenizer(plan['tokenizer'], plan['tokenizer_spec'])
    context = plan['config']['context']
    reserve = plan['config']['decoding']['max_new_tokens']
    stories = []
    for story in sorted(units, key=int):
        positions = units[story]
        if sorted(positions) != list(range(1, len(positions) + 1)):
            raise ValueError('Noncontiguous whole-unit positions')
        text = ' '.join(positions[p] for p in range(1, len(positions) + 1))
        tokens = tokenizer.encode(text, bos=True)
        if tokenizer.eos_id in tokens[1:]:
            raise ValueError('Reserved token literal inside candidate story')
        remaining = context - reserve - len(tokens)
        stories.append({
            'source_story_id': story,
            'whole_units': len(positions),
            'reconstructed_utf8_bytes': len(text.encode('utf-8')),
            'reconstructed_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'BPE_input_tokens_including_BOS': len(tokens),
            'remaining_tokens_before_any_task_instructions': remaining,
            'fits_without_any_task_instructions': remaining >= 0,
        })
    if sum(s['whole_units'] for s in stories) != source['whole_units_observed']:
        raise ValueError('Changed whole-unit count')
    return {
        'utc': datetime.now(UTC).isoformat(),
        'purpose': 'candidate context measurement only, not transfer-set acceptance',
        'repository': source['repository'], 'revision': source['revision'],
        'source_file_sha256': source['files'], 'license': source['license'],
        'plan_id': plan['plan_id'], 'tokenizer_sha256': plan['tokenizer_spec']['sha256'],
        'context': context, 'illustrative_generation_reserve_from_foundation': reserve,
        'reconstruction': 'join pinned .whole units with one ASCII space; not recovered original punctuation formatting',
        'stories': stories,
        'any_full_story_fits_without_task_instructions': any(s['fits_without_any_task_instructions'] for s in stories),
        'final_prompt_fits_verified': False, 'accepted_transfer_pairs': 0,
        'human_semantic_labels': 0, 'model_loaded': False, 'optimizer_updates': 0,
        'primary_test_access': False, 'final_transfer_manifest': None,
        'candidate_inventory_sha256': sha256(candidates_path),
        'implementation_sha256': source_sha256(__file__),
        'limitations': [
            'Counts refer to declared reconstruction and current frozen tokenizer; task instructions and semantic obligations need additional context.',
            'No truncation, window selection, intervention creation or model output; any future excerpts require a self-contained-context human audit.',
            'Ten parent stories remain ten source clusters; token windows are not independent stories.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--candidates', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = audit(args.directory, args.plan, args.candidates)
    write_json(args.output, result)
    print({
        'source_stories': len(result['stories']),
        'BPE_range_including_BOS': [
            min(s['BPE_input_tokens_including_BOS'] for s in result['stories']),
            max(s['BPE_input_tokens_including_BOS'] for s in result['stories']),
        ],
        'any_full_story_fits_without_task_instructions': result['any_full_story_fits_without_task_instructions'],
        'accepted_transfer_pairs': 0,
    })


if __name__ == '__main__':
    main()
