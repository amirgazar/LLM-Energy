# LLM-Energy | ACIS 2026

Current release: verified 161-profile analysis, updated 20 October 2026.

[Public study website and all 16 outcome questions](https://amirgazar.github.io/representation-theory-llms-study/). This repository remains private.

## Current findings

All seven configurations preserve the human domain order: economic and health impacts rank above visual/ecological impacts. Fast (gpt-oss-120b) meets the descriptive 0.5-point alignment threshold for all three means. Thinking (DeepSeek-V4.1-Flash, low reasoning) has a visual/ecological mean of 2.30 versus 2.97 for humans, outside that threshold. Fast and Thinking both have a mean item-level total variation distance of 0.246 after rounding; the unrounded values differ.

The analysis uses 161 verified matched profiles. Configurations 1 to 3 each have three runs per profile, averaged within each profile before intervals are calculated. Each local configuration has one run per profile. The two national configurations each use 5,626 profiles from a separate population. Human outcome answers were not supplied to the models.

There are 13,023 generated written answers and 15,794 theme occurrences. Reliability leads Fast (75.7%) and Thinking (60.2%) as a share of their theme occurrences. Six human answers contain nuclear keywords; no generated answer does. Keywords measure mentions, not support or opposition. The national configurations dominate pooled counts. Human written answers were optional and question wording differs.

## Current files

- `verified/`: current aggregate tables, website-compatible results, and both updated figures.
- `analysis_verified.py`: offline reproduction of the verified analysis using restricted inputs held separately.
- `verified_keywords.json`: both keyword dictionaries used in this analysis.
- `questions.json`: questionnaire for the collection example. The website also shows the local script's shorter impact wording.
- `collect.py`: existing dry-run-first collection example, not the code used to produce the completed DeepSeek run.
- `privacy_check.py`: checks the release files for likely credentials and participant records without printing matched values.

The older `results/`, `figures/`, `analysis.py` and `figures.py` describe the superseded analysis. They are retained for comparison only. Do not mix their results with `verified/`. See `HISTORICAL_README.md` for their original instructions.

## Reproduce the current analysis

Use Python 3.12. No third-party packages are required for `analysis_verified.py`.

```sh
python analysis_verified.py --runs-root /path/to/restricted/Local-Model-Checks --original-root /path/to/restricted/LLM-Energy --benchmark /path/to/restricted/Verified_161_Human_Benchmark_REVISED.json --output /path/to/aggregate-output
python privacy_check.py
```

The runs folder must retain the named verified commercial and local run subfolders used in the script. The original root supplies the two saved national datasets. The benchmark and run records require separate authorized access and are not included here. The script makes no service calls and exports aggregate results only. Website-shaped summaries in `verified/results.json` use the same aggregate analysis; they are also available from the public website. Figure PNGs are the checked manuscript figures.

## Limits and privacy

Intervals describe these profiles, not a representative population. A non-significant difference is not proof of equivalence. The 0.5-point alignment rule is descriptive. Differences between models do not isolate reasoning settings, and single local runs do not measure repeat variation.

No participant profiles, identifiers, individual answers, verbatim study answers, credentials or notebook outputs are included in this release. Keep restricted inputs outside this checkout. Fictional examples in tests are not study participants. The privacy check detects common patterns; it does not certify remote history or branches. Existing historical source manifests contain file-level checksums, not source data.

Use the author list and title in the ACIS 2026 paper 256. No new licence is asserted for inherited material.
