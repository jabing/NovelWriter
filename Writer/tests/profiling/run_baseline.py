#!/usr/bin/env python3
"""Baseline profiling for novel generation stability (synthetic workload).
This script uses existing performance utilities without touching production code.
"""

import time
import tracemalloc
from pathlib import Path
from statistics import mean, stdev

try:
    from src.utils.performance import get_memory_tracker, get_token_tracker
except Exception as e:  # pragma: no cover
    raise SystemExit(f"Failed to import performance utilities: {e}")


def generate_text(words: int) -> str:
    return " ".join(["word"] * words)


def run_once(run_id: int) -> dict[str, object]:
    memory = get_memory_tracker()
    tokens = get_token_tracker()
    # MemoryTracker has no public reset(); clear internal state for isolation
    if hasattr(memory, "_operations"):
        memory._operations.clear()
    tokens.reset()

    tracemalloc.start()
    base_curr, _ = tracemalloc.get_traced_memory()
    run_start = time.perf_counter()

    total_text_parts: list[str] = []
    chapter_times: list[float] = []
    total_words = 0
    milestone_map: dict[int, dict[str, float]] = {}
    milestones_hit = set()
    tokens_so_far = 0

    # 15 chapters: 1-5 -> 2000 each; 6-10 -> 3000 each; 11-15 -> 5000 each
    for ch in range(15):
        words = 2000 if ch < 5 else (3000 if ch < 10 else 5000)
        t0 = time.perf_counter()
        text = generate_text(words)
        t1 = time.perf_counter()
        total_text_parts.append(text)
        chapter_times.append(t1 - t0)
        total_words += words

        # Rough token estimation: 1 token per 4 chars
        tokens_this_chapter = max(1, int(len(text) / 4))
        tokens.record(tokens_this_chapter // 2, tokens_this_chapter - (tokens_this_chapter // 2))
        tokens_so_far += tokens_this_chapter

        current_text = " ".join(total_text_parts)
        if 10000 not in milestone_map and total_words >= 10000:
            cur, _ = tracemalloc.get_traced_memory()
            milestone_map[10000] = {
                "memory_bytes": max(0, cur - base_curr),
                "time_sec": sum(chapter_times[: ch + 1]),
                "snapshot_bytes": len(current_text.encode("utf-8")),
                "tokens": tokens_so_far,
            }
            milestones_hit.add(10000)
        if 25000 not in milestone_map and total_words >= 25000:
            cur, _ = tracemalloc.get_traced_memory()
            milestone_map[25000] = {
                "memory_bytes": max(0, cur - base_curr),
                "time_sec": sum(chapter_times[: ch + 1]),
                "snapshot_bytes": len(current_text.encode("utf-8")),
                "tokens": tokens_so_far,
            }
            milestones_hit.add(25000)
        if 50000 not in milestone_map and total_words >= 50000:
            cur, _ = tracemalloc.get_traced_memory()
            milestone_map[50000] = {
                "memory_bytes": max(0, cur - base_curr),
                "time_sec": sum(chapter_times[: ch + 1]),
                "snapshot_bytes": len(current_text.encode("utf-8")),
                "tokens": tokens_so_far,
            }
            milestones_hit.add(50000)

    total_time = time.perf_counter() - run_start
    total_snapshot = len((" ".join(total_text_parts)).encode("utf-8"))
    tracemalloc.stop()
    return {
        "run_id": run_id,
        "milestones": milestone_map,
        "chapter_times": chapter_times,
        "total_words": total_words,
        "total_time": total_time,
        "snapshot_size": total_snapshot,
    }


def write_md(results: list[dict[str, object]], path: str) -> None:
    lines: list[str] = []
    lines.append("# Baseline Metrics for Novel Generation Stability")
    lines.append("")
    lines.append("## Methodology")
    lines.append("- Synthetic workload: 15 chapters with per-chapter words [2000, 3000, 5000].")
    lines.append(
        "- Memory measured with tracemalloc; token usage estimated from text length and recorded via TokenTracker."
    )
    lines.append("- 3 independent runs; results reported as mean ± standard deviation.")
    lines.append("")

    milestones = [10000, 25000, 50000]
    lines.append("## Metrics by milestone")
    for m in milestones:
        mem_vals: list[float] = []
        time_vals: list[float] = []
        snap_vals: list[float] = []
        token_vals: list[float] = []
        for r in results:
            r_map = dict(r)
            mm = r_map.get("milestones")
            if isinstance(mm, dict) and m in mm:
                mv = mm[m]
                if isinstance(mv, dict):
                    if isinstance(mv.get("memory_bytes"), (int, float)):
                        mem_vals.append(mv["memory_bytes"])
                    if isinstance(mv.get("time_sec"), (int, float)):
                        time_vals.append(mv["time_sec"])
                    if isinstance(mv.get("snapshot_bytes"), (int, float)):
                        snap_vals.append(mv["snapshot_bytes"])
                    if isinstance(mv.get("tokens"), (int, float)):
                        token_vals.append(mv["tokens"])
        mem_mean = mean(mem_vals) if mem_vals else 0
        mem_sd = stdev(mem_vals) if len(mem_vals) > 1 else 0
        time_mean = mean(time_vals) if time_vals else 0
        time_sd = stdev(time_vals) if len(time_vals) > 1 else 0
        snap_mean = mean(snap_vals) if snap_vals else 0
        snap_sd = stdev(snap_vals) if len(snap_vals) > 1 else 0
        token_mean = mean(token_vals) if token_vals else 0
        token_sd = stdev(token_vals) if len(token_vals) > 1 else 0
        lines.append(
            f"- Milestone {m} words: memory={mem_mean / 1e6:.3f}MB (±{mem_sd / 1e6:.3f}MB), time={time_mean:.3f}s (±{time_sd:.3f}s), snapshot={snap_mean:.0f}B (±{snap_sd:.0f}B), tokens={token_mean:.0f} (±{token_sd:.0f})"
        )
    lines.append("")

    # Per-chapter timing summary placeholder (detailed per-chapter timing is available in run data)
    lines.append("## Per-chapter timing (grouped into 3 blocks of 5 chapters)")
    lines.append(
        "Chapters 1-5, 6-10, and 11-15 have separate timing data per run; see individual run entries for details."
    )

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    results: list[dict[str, object]] = []
    for i in range(3):
        results.append(run_once(i + 1))
    out = "tests/profiling/baseline_metrics.md"
    write_md(results, out)
    print(f"Baseline metrics written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
