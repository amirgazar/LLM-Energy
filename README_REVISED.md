# Survey response study for ACIS 2026

This repository contains the revised analysis for paper 256, **When LLM-Simulated Survey Responses Get the Order Right but the Story Wrong: A Study of Public Opinion on Decarbonization**.

The study compares a screened human sample with saved computer-generated survey responses. The results describe these files. They do not estimate the views of the New England population.

## Main corrections

- Report differences and 95% intervals instead of treating a non-significant result as proof of equality.
- Average repeated runs within each source profile before calculating standard errors.
- Distinguish the 161 screened human respondents from the 171 profiles used in the archived survey-based runs. These sets have different identifiers. A verified link is not available.
- Treat the two local-model runs as exploratory. The available script reads ratings from reasoning text, can misclassify ratings, and does not ask the open-ended question.
- Separate refusals, missing values, and invalid outputs.
- Show the denominator for each theme percentage and include the original and revised keyword dictionaries.

## Read the results

The `results_REVISED` folder contains aggregate tables. `results_REVISED.json` contains the same results for reuse. `source_manifest_REVISED.json` records the exact source files and their checksums.

No participant contact details, raw survey rows, open-ended text, access keys, or old notebook output are included. The original files remain in the authors' local archive. Access to restricted research data requires the authors' review of the study's consent and data-use terms. Third-party data remain subject to their own terms.

## Reproduce the analysis locally

Use Python 3.12 and install the packages:

```sh
python -m pip install -r requirements_REVISED.txt
python analysis_REVISED.py --source /path/to/LLM-Energy
python -m unittest tests_REVISED.py
```

The analysis reads the original `1 Survey Results` and `5 Final Results` folders. It does not edit them, access the internet, or request new model responses. It writes aggregate outputs only.

The source profile is the unit used for intervals. For configurations 1 to 3, the three saved runs are averaged within each profile. The human intervals describe variation within the convenience sample. The generated intervals describe variation across source profiles and do not account for all uncertainty in the model or public opinion.

Domain indices are the mean of available numeric ratings: visual and ecological items 1 to 4; economic items 5 to 8; environmental and health items 9 to 15. An index is missing when all its items are missing. Complete-item results are also provided. These domain labels are short names: the last group includes climate and Indigenous-community impacts as well as health.

The paired contrasts subtract two domain scores within a response. They are then averaged within profiles for repeated runs. Their intervals are not tests of equivalence. No minimum meaningful difference was set before the study, so no later choice of a threshold is presented as confirmatory evidence.

Item distance is half the sum of the absolute differences between human and generated response shares over the five rating options. It ranges from 0 for identical distributions to 1 for no overlap. It is descriptive and is calculated among valid ratings.

Theme coding counts each keyword theme once per response. A response can match several themes. Shares of responses use all non-empty responses as the denominator. Shares of assignments use the sum of all theme matches. The dictionary cannot establish a person's reasons, distinguish every context, or prove that an absent keyword means an absent concern.

## New response collection

`collect_REVISED.py` provides a corrected collection route for a future controlled rerun. It reads a separate profile file and the supplied questionnaire. It accepts only a complete final answer, records completion status, and never reads an answer from reasoning text. The default is a dry run. New collection has not been carried out for this revision and must not be described as completed.

## Citation and reuse

Use the author list and title in the revised paper. Final proceedings details are pending. No new licence is asserted for the inherited data or code. Contact the authors about reuse beyond rights already granted by the relevant source.
