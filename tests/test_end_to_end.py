from pathlib import Path
import json
import hashlib
import subprocess
import sys
import numpy as np
import pandas as pd


def test_entire_analysis_on_synthetic_data(tmp_path):
    rng = np.random.default_rng(10)
    n = 130
    d = pd.DataFrame({'gender':['M']*65+['F']*65,
        'swipe_likes':rng.integers(15,400,n),
        'no_of_matches':rng.integers(0,70,n),
        'sum_app_opens':rng.integers(10,1000,n),
        'no_of_days':rng.integers(8,300,n)})
    data = tmp_path / 'synthetic.csv'
    d.to_csv(data, index=False)
    output = tmp_path / 'results'
    project = Path(__file__).resolve().parents[1]
    process = subprocess.run([sys.executable, '-m', 'scripts.run_analysis',
             '--input', str(data), '--output', str(output), '--bootstrap', '200', '--seed', '123'],
             cwd=project, capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert (output/'FINDINGS.md').exists()
    assert (output/'gender_summary.csv').exists()
    assert (output/'models.csv').exists()
    assert (output/'figures'/'05_lorenz_match_counts.png').exists()
    assert (output/'figures'/'05_lorenz_match_counts.pdf').exists()
    audit = json.loads((output/'audit.json').read_text())
    assert audit['usable_rows'] == 130
    manifest = json.loads((output/'dataset_manifest.json').read_text())
    assert manifest['sha256'] == hashlib.sha256(data.read_bytes()).hexdigest()
    assert manifest['original_rows'] == 130
    assert manifest['seed'] == 123
    assert manifest['bootstrap_draws_requested'] == 200
    assert 'Random seed: 123; requested bootstrap draws: 200.' in (output/'FINDINGS.md').read_text()


def test_one_command_reuses_existing_file_without_network(tmp_path):
    rng = np.random.default_rng(11)
    n = 75
    source = tmp_path / 'source.csv'
    pd.DataFrame({'gender':['M']*40+['F']*35,
        'swipe_likes':rng.integers(10,100,n),
        'no_of_matches':rng.integers(1,15,n),
        'sum_app_opens':rng.integers(5,100,n),
        'no_of_days':rng.integers(2,50,n)}).to_csv(source,index=False)
    output=tmp_path/'one-command-results'
    project=Path(__file__).resolve().parents[1]
    p=subprocess.run([sys.executable,'-m','scripts.run_study',
        '--data',str(source),'--output',str(output),'--bootstrap','200'],
        cwd=project,capture_output=True,text=True)
    assert p.returncode == 0,p.stderr
    assert (output/'FINDINGS.md').exists()
    assert 'already_exists' in p.stdout
