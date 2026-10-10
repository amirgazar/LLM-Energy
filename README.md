# LLM-Energy | ACIS 2026

This repository contains code and aggregate results for the ACIS 2026 study, paper 256, **When LLM-Simulated Survey Responses Get the Order Right but the Story Wrong: A Study of Public Opinion on Decarbonization**.

The study compares the 161 human responses in the original survey analysis with saved computer-generated survey responses. The results describe these files. They do not estimate the views of the New England population.

## Analysis approach

- Report differences and 95% intervals instead of treating a non-significant result as proof of equality.
- Retain the original response-level domain means and standard errors, pooling saved runs within each configuration. Provide a separate profile-level sensitivity check for repeated runs.
- Read the human benchmark from the original survey CSV, with the same selection and question mapping as Data Analysis.R. Survey-based model runs contain 171 input profiles. Compare aggregate results rather than claiming individual prediction accuracy.
- Treat the two local-model runs as exploratory. The available script reads ordinal answers from reasoning text, can misclassify ordinal answers, and does not ask the open-ended question.
- Separate refusals, missing values, and invalid outputs.
- Show the denominator for each theme percentage and include the original and sensitivity keyword dictionaries.

Study website: https://amirgazar.github.io/representation-theory-llms-study/

## Read the results

The `results` folder contains aggregate tables. `results.json` contains the same results for reuse. `source_manifest.json` records the exact source files and their checksums.

Human survey records are protected by the study's IRB approvals and are not published here. This includes participant profiles, identifiers, contact details, individual answers and verbatim written responses. Only aggregate study results are shared. Access keys and old notebook outputs are excluded. The original files remain in the authors' local archive. Access to restricted research data requires the authors' review of the study's consent and data-use terms. Third-party data remain subject to their own terms.

## Reproduce the analysis locally

Use Python 3.12 and install the packages:

```sh
python -m pip install -r requirements.txt
python analysis.py --source /path/to/LLM-Energy
python -m unittest tests.py
```

The analysis reads the original `1 Survey Results` and `5 Final Results` folders. It does not edit them, access the internet, or request new model responses. It writes aggregate outputs only.

The primary analysis follows the original script: select CSV rows whose `Believe valid` field starts with `Y`; map `Q9_1` through `Q9_15` to items 1 through 15; map the five importance labels to scores 1 through 5; and calculate each respondent's mean over available items. Configuration means and standard errors use all available response rows, including the pooled runs for configurations 1 to 3. The 161 human records include 160 usable domain scores. The human profile workbook is not used as the answer source.

Repeated runs from one profile are not independent people. Primary intervals describe the stored responses and do not cover all model or population uncertainty. `profile_sensitivity.csv` first averages repeated runs within each profile, then calculates intervals across profiles. This separate check does not replace the original figure method.

Domain indices are the mean of available numeric ordinal answers: visual and ecological items 1 to 4; economic items 5 to 8; environmental and health items 9 to 15. An index is missing when all its items are missing. Complete-item results are also provided. These domain labels are short names: the last group includes climate and Indigenous-community impacts as well as health.

The paired contrasts subtract two domain scores within a response. Primary contrasts pool response rows, as in the original script. The profile-level version is provided separately. Their intervals are not tests of equivalence. No minimum meaningful difference was set before the study, so no later choice of a threshold is presented as confirmatory evidence.

Item distance is half the sum of the absolute differences between human and generated response shares over the five answer options. It ranges from 0 for identical distributions to 1 for no overlap. It is descriptive and is calculated among valid ordinal answers.

Theme coding counts each keyword theme once per response. A response can match several themes. Shares of responses use coded written answers as the denominator. Blank entries and entries such as “no”, “none” and “nothing” are excluded. There are 37 such human answers and 12,791 generated answers. Shares of assignments use the sum of all theme matches. The dictionary cannot establish a person's reasons, distinguish every context, or prove that an absent keyword means an absent concern.

## Response collection code

`collect.py` provides a collection route for future controlled work. It reads a separate profile file and the supplied questionnaire. It accepts only a complete final answer, records completion status, and never reads an answer from reasoning text. The default is a dry run. This code does not describe an additional completed study run.

## Citation and reuse

Use the author list and title in the ACIS 2026 paper. Final proceedings details are pending. No new licence is asserted for the inherited data or code. Contact the authors about reuse beyond rights already granted by the relevant source.
