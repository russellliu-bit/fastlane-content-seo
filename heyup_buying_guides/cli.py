from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_workflow_config
from .artifacts import ArtifactStore
from .orchestrator import run_discovery, run_workflow
from .seed_query_generator import generate_seed_query_plan
from .storage import StateStore
from .utils import ensure_dir
from uuid import uuid4


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Heyup buying guides workflow.")
    parser.add_argument("command", choices=["run", "discover", "seed"], help="Command to execute")
    parser.add_argument("--config", required=True, help="Path to workflow config JSON")
    args = parser.parse_args()

    config = load_workflow_config(Path(args.config))
    if args.command == "discover":
        run_id = uuid4().hex[:12]
        artifacts = ArtifactStore(ensure_dir(config.artifact_root), run_id)
        store = StateStore(config.state_db_path)
        topics, _seed_plan = run_discovery(config, artifacts, run_id, store)
        print(json.dumps([item.to_dict() for item in topics], indent=2))
        return
    if args.command == "seed":
        if not config.raw_keyword:
            raise SystemExit("raw_keyword is required for the seed command.")
        run_id = uuid4().hex[:12]
        artifacts = ArtifactStore(ensure_dir(config.artifact_root), run_id)
        plan = generate_seed_query_plan(config.raw_keyword, config.article_type, config, artifacts=artifacts)
        print(json.dumps(plan.to_dict(), indent=2))
        return
    report = run_workflow(config)
    print(json.dumps(report.to_dict(), indent=2))


if __name__ == "__main__":
    main()
