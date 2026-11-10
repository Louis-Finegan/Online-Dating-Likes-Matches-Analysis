"""Negative binomial count models, exploratory only (never causal)."""
from __future__ import annotations

import warnings
from scipy.stats import chi2
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def fit_models(df: pd.DataFrame, *, fitted_results: dict | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Six negative-binomial models with a log(recorded_days) offset.

    Optionally populate fitted_results with supported fits and their plot data;
    the existing two-value return interface is preserved.

    Model 1: gender only. Model 2: adds activity and likes rates.
    Model 3 interaction tests
    whether the association of app opens with matches varies by gender.
    Model 4 adds categorical source-listed education to Model 2 (no interactions).
    Model 5 instead adds the requested assumed-employment proxy, without education.
    Model 6 adds opens x likes, with additive gender and no other features.
    """
    specs = [
        ('gender_only', 'matches ~ C(gender)'),
        ('likes_and_activity', 'matches ~ C(gender) + log_likes_rate + log_opens_rate'),
        ('activity_interaction', 'matches ~ C(gender) * log_opens_rate + log_likes_rate'),
        ('education', 'matches ~ C(gender) + log_likes_rate + log_opens_rate + C(education_group)'),
        ('employment', 'matches ~ C(gender) + log_likes_rate + log_opens_rate + C(employment_group)'),
        ('opens_likes_interaction', 'matches ~ C(gender) + log_opens_rate * log_likes_rate'),
    ]
    output = []
    models = []
    for name, formula in specs:
        needed = ['matches', 'gender', 'recorded_days', 'log_likes_rate', 'log_opens_rate']
        category = {'education': 'education_group',
                    'employment': 'employment_group'}.get(name)
        if category:
            if category not in df or df[category].nunique() < 2:
                models.append({'name': name, 'status': 'skipped', 'reason': f'need two observed {category} categories'})
                continue
            needed.append(category)
        model_data = df[needed].replace([np.inf, -np.inf], np.nan).dropna().copy()
        counts = model_data['gender'].value_counts()
        model_data = model_data.loc[model_data['gender'].isin(counts[counts >= 10].index)]
        if category and (model_data[category].nunique() < 2 or
                         (model_data[category].value_counts() < 10).any()):
            models.append({'name': name, 'status': 'skipped', 'reason': f'need at least ten users per {category} category'})
            continue
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
            test_prefix = category.removesuffix('_group') if category else (
                'opens_likes_interaction' if name == 'opens_likes_interaction' else None)
            if test_prefix and converged and finite:
                # Compare nested models on exactly the same complete-case sample.
                reduced = smf.negativebinomial(
                    'matches ~ C(gender) + log_likes_rate + log_opens_rate',
                    data=model_data, offset=np.log(model_data.recorded_days)).fit(disp=0, maxiter=400)
                if reduced.mle_retvals.get('converged', False) and np.isfinite(reduced.llf):
                    statistic = float(2 * (result.llf - reduced.llf))
                    degrees = int(len(result.params) - len(reduced.params))
                    if statistic >= -1e-6 and degrees > 0:
                        models[-1][test_prefix + '_likelihood_ratio_test'] = {
                            'null': f'all {category} coefficients are zero' if category else 'opens x likes coefficient is zero',
                            'statistic': max(0., statistic), 'df': degrees,
                            'p_value': float(chi2.sf(max(0., statistic), degrees)),
                            'n': int(len(model_data)), 'reduced_log_likelihood': float(reduced.llf)}
            if converged and finite and fitted_results is not None:
                plot_data = model_data.assign(
                    likes_per_recorded_day=np.expm1(model_data.log_likes_rate),
                    opens_per_recorded_day=np.expm1(model_data.log_opens_rate))
                fitted_results[name] = (result, plot_data)
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
