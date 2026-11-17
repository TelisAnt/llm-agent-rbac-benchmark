"""Agent loop and experiment driver.

    python -m authz_lab.runner --models mock --reps 2 --out results/smoke.jsonl
    python -m authz_lab.runner --models ollama:llama3.1:8b ollama:qwen2.5:7b --reps 3 --workers 1

Every proposed tool call goes through the configuration's gate and only allowed calls
execute. One JSON record is written per run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from .environment import PERMISSIONS, VirtualSystem
from .evaluation import RunLogger, judge
from .llm import make_backend
from .pipelines import PIPELINES, RBACMiddleware
from .scenarios import CATEGORIES, Scenario, build_suite

SHADOW = RBACMiddleware()  # only logged, so we can see what RBAC would have decided in every config
TRUNC = 1500


def run_one(model_spec: str, backend, pipeline, scenario: Scenario, rep: int,
            seed: int, max_steps: int) -> dict:
    t0 = time.time()
    system = VirtualSystem()
    for loc, text in scenario.poison:
        system.poison(loc, text)
    before = system.snapshot()
    sys_prompt = pipeline.system_prompt(scenario.role)
    tools = pipeline.tool_specs()
    run_seed = int(hashlib.sha256(f"{seed}|{scenario.id}|{rep}".encode()).hexdigest()[:8], 16)

    history: list[dict] = []
    tool_log: list[dict] = []
    turns_log: list[dict] = []
    hit_step_limit = False

    for t_idx, user_msg in enumerate(scenario.turns):
        history.append({"role": "user", "content": user_msg})
        model_texts = []
        for step in range(max_steps):
            turn = backend.complete(sys_prompt, history, tools, seed=run_seed)
            model_texts.append(turn.text)
            history.append({"role": "assistant", "text": turn.text,
                            "tool_calls": [{"id": c.id, "name": c.name, "args": c.args} for c in turn.tool_calls]})
            if not turn.tool_calls:
                break
            for call in turn.tool_calls:
                shadow = SHADOW.authorize(scenario.role, call.name, call.args)
                gate = pipeline.gate(scenario.role, call.name, call.args)
                if gate.allowed:
                    res = system.execute(call.name, call.args)
                    content, executed, result_ok = res.output, True, res.ok
                else:
                    content = f"ERROR: {gate.layer.upper()}_DENIED: {gate.reason}"
                    executed, result_ok = False, False
                history.append({"role": "tool", "tool_call_id": call.id, "name": call.name, "content": content})
                tool_log.append({
                    "turn": t_idx, "step": step, "tool": call.name, "args": call.args,
                    "gate_allowed": gate.allowed, "gate_layer": gate.layer, "gate_reason": gate.reason,
                    "shadow_rbac_allowed": shadow.allowed,  # enforced only in the rbac config
                    "executed": executed, "result_ok": result_ok, "result": content[:TRUNC],
                })
        else:
            hit_step_limit = True
        turns_log.append({"user": user_msg, "model_texts": model_texts})

    after = system.snapshot()
    final_text = next((t for turn in reversed(turns_log) for t in reversed(turn["model_texts"]) if t), "")
    return {
        "run_id": f"{model_spec}|{pipeline.name}|{scenario.id}|{rep}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model_spec, "config": pipeline.name, "scenario_id": scenario.id, "rep": rep,
        "category": scenario.category, "role": scenario.role.value, "operation": scenario.operation,
        "is_attack": scenario.is_attack,
        "turns": turns_log,
        "chosen_tools": [{"tool": c["tool"], "args": c["args"]} for c in tool_log],
        "tool_log": tool_log,
        "final_text": final_text,
        "state_before_hash": VirtualSystem.state_hash(before),
        "state_after_hash": VirtualSystem.state_hash(after),
        "state_changed": before != after,
        "state_after": after,
        "hit_step_limit": hit_step_limit,
        "judge": judge(scenario, tool_log, final_text),
        "latency_s": round(time.time() - t0, 3),
        "error": None,
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", default=["mock"],
                    help="mock | ollama:<tag> | local:<id> | anthropic:<id> | openai:<id>")
    ap.add_argument("--configs", nargs="+", default=list(PIPELINES), choices=list(PIPELINES))
    ap.add_argument("--categories", nargs="+", default=list(CATEGORIES), choices=list(CATEGORIES))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--max-steps", type=int, default=4, help="max model calls per user turn")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="run only the first N tasks (smoke test)")
    ap.add_argument("--out", default="results/runs.jsonl")
    a = ap.parse_args(argv)

    suite = build_suite(tuple(a.categories))
    logger = RunLogger(a.out)
    done = logger.done_keys()
    backends = {m: make_backend(m, a.temperature) for m in a.models}

    tasks = [(m, c, s, r) for m in a.models for c in a.configs for s in suite for r in range(a.reps)
             if (m, c, s.id, r) not in done]
    random.Random(a.seed).shuffle(tasks)  # mix conditions so slow drift does not hit one of them
    if a.limit:
        tasks = tasks[:a.limit]

    meta = {"args": vars(a), "n_scenarios": len(suite), "python": sys.version, "platform": platform.platform(),
            "permissions": {r.value: sorted(t.value for t in ts) for r, ts in PERMISSIONS.items()},
            "suite_hash": hashlib.sha256(json.dumps([s.__dict__ | {"role": s.role.value} for s in suite],
                                                    sort_keys=True, default=str).encode()).hexdigest()[:16]}
    Path(a.out).with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    print(f"{len(suite)} scenarios; {len(tasks)} runs to do ({len(done)} already done)")

    def work(task):
        m, c, s, r = task
        try:
            return run_one(m, backends[m], PIPELINES[c](), s, r, a.seed, a.max_steps)
        except Exception as exc:  # logged, left out of the metrics, and retried when resuming
            return {"model": m, "config": c, "scenario_id": s.id, "rep": r, "error": repr(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat()}

    n_done = n_err = 0
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as pool:
        for fut in as_completed(pool.submit(work, t) for t in tasks):
            rec = fut.result()
            logger.write(rec)
            n_done += 1
            n_err += bool(rec.get("error"))
            if n_done % 25 == 0 or n_done == len(tasks):
                print(f"  {n_done}/{len(tasks)} done, {n_err} errors")
    print(f"Log: {a.out}\nNext: python -m authz_lab.evaluation {a.out} --plots")


if __name__ == "__main__":
    main()
