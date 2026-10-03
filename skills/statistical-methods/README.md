# Statistical method selection

Start with the scientific question and estimand, not a familiar test name. Specify the unit of analysis, outcome scale, exposure/comparison, target population, dependence structure, missing-data rule, and multiplicity plan before choosing a method.

| Situation | Typical starting family | Check before use |
| --- | --- | --- |
| Continuous outcome, two independent groups | Difference in means or a regression model | Distributional shape, unequal variance, covariate adjustment, independence. |
| Continuous paired or repeated outcomes | Paired model or mixed/repeated-measures regression | Pairing, time/order, within-subject correlation. |
| Binary outcome | Logistic regression or an exact/contingency approach for small data | Separation, sparse cells, covariates, event count. |
| Counts or rates | Poisson or negative-binomial regression | Exposure offset, overdispersion, zero inflation, dependence. |
| Time to event | Survival model or nonparametric survival comparison | Censoring mechanism, proportional hazards if applicable, competing risks. |
| Many features tested | Feature-level model plus multiplicity correction | Predefined family, dependence, effect sizes and uncertainty. |
| Nonlinear, poorly behaved, or small-sample statistic | Permutation, bootstrap, or robust alternative | Exchangeability, resampling unit, computational budget. |

Report the estimand, effect size, uncertainty interval, sample counts, exclusions, diagnostics, and multiplicity treatment. A p-value, model score, or Jev judgment is not evidence by itself. Do not silently convert missingness to zero, and do not use a convenience test to repair an unclear causal or sampling design.

This guide is a compact decision aid inspired by standard method-selection teaching material, including the linked STAT H400 note; it is original OncoJev guidance and does not replace statistical review for consequential claims.
