"""Exploratory NB coefficient plots and pointwise confidence bands for means."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def _save(directory, name):
    # Layout is set above, reserving space for the statistical captions.
    for extension in ('png', 'pdf'):
        plt.savefig(directory / f'{name}.{extension}', dpi=180, bbox_inches='tight')
    plt.close()



def mean_interval(design, beta, covariance):
    """One recorded day: exp(X beta +/- 1.96 sqrt(diag(X Cov(beta) X'))).

    These are pointwise Wald intervals for the conditional mean, not prediction
    intervals for individual counts or simultaneous confidence bands.
    """
    design = np.asarray(design, dtype=float)
    eta = design @ np.asarray(beta)
    variance = np.einsum('ij,jk,ik->i', design, np.asarray(covariance), design)
    if (variance < -1e-10).any() or not np.isfinite(variance).all():
        raise ValueError('Invalid prediction covariance')
    se = np.sqrt(np.maximum(variance, 0))
    return np.exp(eta), np.exp(eta - 1.96 * se), np.exp(eta + 1.96 * se)


def prediction_table(result, data):
    """Use each fitted gender's observed opening range; pooled median likes."""
    terms = [term for term in result.params.index if term != 'alpha']
    reference_likes = float(data.likes_per_recorded_day.median())
    rows = []
    education_model = any('C(education_group)' in term for term in terms)
    grouping = ['gender', 'education_group'] if education_model else ['gender']
    for key, group in data.groupby(grouping, observed=True, sort=True):
        gender = key[0] if isinstance(key, tuple) else key
        education = key[1] if education_model else None
        lo, hi = group.opens_per_recorded_day.min(), group.opens_per_recorded_day.max()
        opens = np.expm1(np.linspace(np.log1p(lo), np.log1p(hi), 150))
        grid = pd.DataFrame({'log_opens_rate': np.log1p(opens),
                             'log_likes_rate': np.log1p(reference_likes)}, index=range(len(opens)))
        # Reconstruct the explicit treatment-coded formulas fitted in models.py.
        # Preserve the fitted column order, including interaction terms.
        columns = []
        for term in terms:
            values = np.ones(len(opens))
            for factor in term.split(':'):
                if factor == 'Intercept':
                    continue
                if factor.startswith('C(gender)[T.') and factor.endswith(']'):
                    values *= float(str(gender) == factor[len('C(gender)[T.'):-1])
                elif factor.startswith('C(education_group)[T.') and factor.endswith(']'):
                    values *= float(str(education) == factor[len('C(education_group)[T.'):-1])
                else:
                    values *= grid[factor].to_numpy()
            columns.append(values)
        design = np.column_stack(columns)
        mean, low, high = mean_interval(design, result.params.loc[terms],
                                       result.cov_params().loc[terms, terms])
        rows.append(pd.DataFrame({'gender': str(gender), 'opens_per_recorded_day': opens,
            'reference_likes_per_recorded_day': reference_likes, 'recorded_days': 1,
            'expected_matches_per_recorded_day': mean, 'ci95_low': low, 'ci95_high': high}))
        if education_model:
            rows[-1]['education_group'] = str(education)
    return pd.concat(rows, ignore_index=True)


def make_model_figures(coefficients, fitted_results, output):
    """Only converged fits with finite parameters/SEs are supplied by fit_models."""
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    figures = []
    titles = {'gender_only': 'Model 1: gender only',
              'likes_and_activity': 'Model 2: likes and activity',
              'activity_interaction': 'Model 3: activity interaction',
              'education_adjusted': 'Model 4: source-listed education'}
    for name in fitted_results:
        table = coefficients.loc[(coefficients.model == name) &
                                 ~coefficients.term.isin(['Intercept', 'alpha'])].copy()
        table.to_csv(directory / f'coefficients_{name}.csv', index=False)
        fig, ax = plt.subplots(figsize=(9, max(3, 0.6 * len(table) + 1.5)))
        y = np.arange(len(table))
        ax.errorbar(table.rate_ratio, y,
            xerr=[table.rate_ratio - table.rate_ratio_ci95_low,
                  table.rate_ratio_ci95_high - table.rate_ratio], fmt='o', capsize=4)
        ax.axvline(1, color='0.5', linestyle='--')
        ax.set_yticks(y, table.term)
        ax.invert_yaxis()
        ax.set(xlabel='Rate ratio, 95% Wald confidence interval', title=titles[name])
        fig.text(0.5, 0.01, 'Exploratory associations. Continuous terms: +1 in log(1 + rate).\n'
                 'Interaction model: gender contrast is at zero opens; interaction is a ratio of rate ratios.',
                 ha='center', fontsize=8)
        fig.tight_layout(rect=(0, 0.12, 1, 1))
        filename = f'06_coefficients_{name}'
        _save(directory, filename)
        figures.append(filename)
    curve_models = [n for n in ('likes_and_activity', 'activity_interaction', 'education_adjusted') if n in fitted_results]
    if not curve_models:
        return figures
    fig, axes = plt.subplots(1, len(curve_models), figsize=(7 * len(curve_models), 5), squeeze=False, sharey=True)
    tables = []
    for ax, name in zip(axes[0], curve_models):
        result, data = fitted_results[name]
        table = prediction_table(result, data)
        table.insert(0, 'model', name)
        tables.append(table)
        grouping = ['gender', 'education_group'] if 'education_group' in table else ['gender']
        for key, group in table.groupby(grouping, observed=True, sort=True):
            gender = key[0] if isinstance(key, tuple) else key
            label = ' / '.join(map(str, key)) if isinstance(key, tuple) else str(key)
            line, = ax.plot(group.opens_per_recorded_day, group.expected_matches_per_recorded_day,
                            label=label, color='#1f77b4' if gender == 'Female' else '#ff7f0e',
                            linestyle='--' if 'education_group' in table and key[1] == 'Listed education' else '-')
            ax.fill_between(group.opens_per_recorded_day, group.ci95_low, group.ci95_high,
                            color=line.get_color(), alpha=0.2)
            mask = data.gender == gender
            if 'education_group' in table:
                mask &= data.education_group == key[1]
            observed = data.loc[mask, 'opens_per_recorded_day']
            # Rugs show observed support, without adding user-level data to CSVs.
            ax.plot(observed, np.full(len(observed), 0.015 if gender == 'Female' else 0.045),
                    '|', color=line.get_color(), alpha=0.15, transform=ax.get_xaxis_transform())
        ax.set_xscale('symlog', linthresh=1)
        ax.set(xlabel='App opens / recorded day (symlog scale)',
               ylabel='Expected matches / recorded day', title=titles[name])
        ax.legend()
        ax.grid(alpha=0.15)
    pd.concat(tables, ignore_index=True).to_csv(directory / 'model_prediction_curves.csv', index=False)
    fig.text(0.5, 0.01, 'Pointwise 95% confidence bands for the mean, not individual prediction intervals.\n'
             'Likes/day fixed at the fitted sample pooled median; each curve stays within its gender/education group observed opening range.\n'
             'Rugs show opening-rate support. Recorded days are log dates, not tenure. Exploratory, not causal.',
             ha='center', fontsize=9)
    fig.tight_layout(rect=(0, 0.15, 1, 1))
    filename = '07_model_match_rate_curves'
    _save(directory, filename)
    figures.append(filename)
    return figures
