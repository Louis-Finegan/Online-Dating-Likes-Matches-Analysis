"""Negative binomial count models, exploratory only (never causal)."""
from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def fit_models(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Three negative-binomial models with a log(recorded_days) offset.

    Model 1: gender only. Model 2: adds activity and likes rates.
    Model 3 interaction tests
    whether the association of app opens with matches varies by gender.
    """
    specs = [
        ('gender_only', 'matches ~ C(gender)'),
        ('likes_and_activity', 'matches ~ C(gender) + log_likes_rate + log_opens_rate'),
        ('activity_interaction', 'matches ~ C(gender) * log_opens_rate + log_likes_rate'),
    ]
    output = []
    models = []
    for name, formula in specs:
        needed = ['matches', 'gender', 'recorded_days', 'log_likes_rate', 'log_opens_rate']
        model_data = df[needed].replace([np.inf, -np.inf], np.nan).dropna().copy()
        counts = model_data['gender'].value_counts()
        model_data = model_data.loc[model_data['gender'].isin(counts[counts >= 10].index)]
        if len(model_data) < 50 or model_data['gender'].nunique() < 2 or model_data['matches'].nunique() < 3:
            models.append({'name': name, 'status': 'skipped', 'reason': 'insufficient observations/groups/variation'})
            continue
        # Make explicit when the NB maximum likelihood optimisation does not converge.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                result = smf.negativebinomial(formula, data=model_data,
                     offset=np.log(model_data['recorded_days'])).fit(disp=0, maxiter=400)
            converged = bool(result.mle_retvals.get('converged', False))
            finite = bool(np.isfinite(result.params).all() and np.isfinite(result.bse).all())
            models.append({'name': name, 'status': 'fitted' if converged and finite else 'unstable',
                           'n': int(len(model_data)), 'formula': formula,
                           'offset': 'log(recorded_days)',
                           'converged': converged, 'log_likelihood': float(result.llf),
                           'aic': float(result.aic)})
            for term in result.params.index:
                estimate = float(result.params[term]); se = float(result.bse[term])
                is_dispersion = term == 'alpha'
                output.append({
                    'model': name, 'term': term, 'estimate': estimate,
                    'standard_error': se, 'p_value': float(result.pvalues[term]),
                    'rate_ratio': float(np.exp(estimate)) if not is_dispersion else np.nan,
                    'rate_ratio_ci95_low': float(np.exp(estimate - 1.96 * se)) if not is_dispersion else np.nan,
                    'rate_ratio_ci95_high': float(np.exp(estimate + 1.96 * se)) if not is_dispersion else np.nan,
                    'converged': converged,
                })
        except (ValueError, np.linalg.LinAlgError, ZeroDivisionError, OverflowError) as exc:
            models.append({'name': name, 'status': 'failed', 'reason': f'{type(exc).__name__}: {exc}'})
    return pd.DataFrame(output), models
