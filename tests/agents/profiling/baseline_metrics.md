# Baseline Metrics for Novel Generation Stability

## Methodology
- Synthetic workload: 15 chapters with per-chapter words [2000, 3000, 5000].
- Memory measured with tracemalloc; token usage estimated from text length and recorded via TokenTracker.
- 3 independent runs; results reported as mean ± standard deviation.

## Metrics by milestone
- Milestone 10000 words: memory=0.101MB (±0.000MB), time=0.000s (±0.000s), snapshot=49999B (±0B), tokens=12495 (±0)
- Milestone 25000 words: memory=0.251MB (±0.000MB), time=0.000s (±0.000s), snapshot=124999B (±0B), tokens=31240 (±0)
- Milestone 50000 words: memory=0.502MB (±0.000MB), time=0.000s (±0.000s), snapshot=249999B (±0B), tokens=62485 (±0)

## Per-chapter timing (grouped into 3 blocks of 5 chapters)
Chapters 1-5, 6-10, and 11-15 have separate timing data per run; see individual run entries for details.