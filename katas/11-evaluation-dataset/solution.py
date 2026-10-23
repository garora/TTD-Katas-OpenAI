from __future__ import annotations
from pathlib import Path
from typing import Mapping
from evals.runner import load_cases,run_evaluations

def evaluate_dataset(dataset_path:Path,actual_results:Mapping[str,Mapping[str,object]]):
 """Load a versioned offline dataset and grade supplied observable results."""
 return run_evaluations(load_cases(dataset_path),actual_results)
