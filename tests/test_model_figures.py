import pytest
import numpy as np
import pandas as pd
from dating_research.model_figures import mean_interval, prediction_table, make_model_figures, opens_likes_prediction_table
from dating_research.models import fit_models


def test_mean_interval_uses_off_diagonal_covariance():
    design = np.array([[1., 2.]])
    covariance = np.array([[0.04, -0.01], [-0.01, 0.09]])
    mean, low, high = mean_interval(design, [0.2, 0.3], covariance)
    eta = 0.8
    se = np.sqrt(0.04 + 4 * 0.09 - 4 * 0.01)
    np.testing.assert_allclose([mean[0], low[0], high[0]],
                              np.exp([eta, eta - 1.96 * se, eta + 1.96 * se]))


def test_prediction_design_agrees_with_fitted_model(tmp_path):
    rng = np.random.default_rng(204)
    n = 400
    d = pd.DataFrame({'gender': ['Female'] * (n // 2) + ['Male'] * (n // 2),
                      'recorded_days': rng.integers(5, 30, n),
                      'likes_per_recorded_day': rng.uniform(0, 20, n),
                      'opens_per_recorded_day': rng.uniform(0, 10, n)})
    d['log_likes_rate'] = np.log1p(d.likes_per_recorded_day)
    d['log_opens_rate'] = np.log1p(d.opens_per_recorded_day)
    eta = -1 + 0.3 * (d.gender == 'Male') + 0.4 * d.log_opens_rate + 0.2 * d.log_likes_rate
    mu = d.recorded_days * np.exp(eta)
    d['matches'] = rng.negative_binomial(2, 2 / (2 + mu))
    fitted = {}
    coefficients, diagnostics = fit_models(d, fitted_results=fitted)
    assert len(fitted) == 4, diagnostics
    for name in ('likes_and_activity', 'activity_interaction', 'opens_likes_interaction'):
        result, sample = fitted[name]
        table = prediction_table(result, sample)
        grid = pd.DataFrame({'gender': table.gender,
            'log_likes_rate': np.log1p(table.reference_likes_per_recorded_day),
            'log_opens_rate': np.log1p(table.opens_per_recorded_day)})
        expected = result.predict(grid, offset=np.zeros(len(grid)))
        np.testing.assert_allclose(table.expected_matches_per_recorded_day, expected)
        assert (table.ci95_low <= table.expected_matches_per_recorded_day).all()
        assert (table.ci95_high >= table.expected_matches_per_recorded_day).all()
        for gender, group in table.groupby('gender'):
            observed = sample.loc[sample.gender == gender, 'opens_per_recorded_day']
            assert np.isclose(group.opens_per_recorded_day.min(), observed.min())
            assert np.isclose(group.opens_per_recorded_day.max(), observed.max())
    figures = make_model_figures(coefficients, fitted, tmp_path)
    interaction, sample = fitted['opens_likes_interaction']
    assert 'log_opens_rate:log_likes_rate' in interaction.params.index
    assert not any('gender' in term and ':' in term for term in interaction.params.index)
    diag = next(x for x in diagnostics if x['name'] == 'opens_likes_interaction')
    lr = diag['opens_likes_interaction_likelihood_ratio_test']
    assert lr['df'] == 1 and lr['n'] == n and 0 <= lr['p_value'] <= 1
    scenarios = opens_likes_prediction_table(interaction, sample)
    assert len(scenarios) == 900
    assert set(scenarios.likes_quantile) == {0.25, 0.5, 0.75}
    for q, group in scenarios.groupby('likes_quantile'):
        np.testing.assert_allclose(group.reference_likes_per_recorded_day,
                                   sample.likes_per_recorded_day.quantile(q))
    grid = pd.DataFrame({'gender': scenarios.gender,
        'log_opens_rate': np.log1p(scenarios.opens_per_recorded_day),
        'log_likes_rate': np.log1p(scenarios.reference_likes_per_recorded_day)})
    np.testing.assert_allclose(scenarios.expected_matches_per_recorded_day,
                              interaction.predict(grid, offset=np.zeros(len(grid))))
    assert len(figures) == 6
    assert all((tmp_path / f'{name}.{ext}').is_file() for name in figures for ext in ('png', 'pdf'))


def test_no_model_plots_for_skipped_fits(tmp_path):
    assert make_model_figures(pd.DataFrame(), {}, tmp_path) == []
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('category,name,levels', [
    ('education_group', 'education', ['No listed education', 'Listed education']),
    ('employment_group', 'employment', ['Unemployed (assumed)', 'Employed (assumed)']),
])
def test_category_fit_tests_and_prediction_design(category, name, levels):
    rng = np.random.default_rng(82)
    n = 400
    d = pd.DataFrame({'gender': np.tile(['Female', 'Male'], n // 2),
        category: pd.Categorical(np.tile([levels[0]] * 2 + [levels[1]] * 2, n // 4),
            categories=levels),
        'recorded_days': rng.integers(5, 30, n),
        'log_likes_rate': rng.uniform(0, 3, n), 'log_opens_rate': rng.uniform(0, 2, n)})
    mu = d.recorded_days * np.exp(-1 + 0.3 * d.log_likes_rate +
        0.4 * d.log_opens_rate + 0.8 * (d[category] == levels[1]))
    d['matches'] = rng.negative_binomial(3, 3 / (3 + mu))
    fitted = {}
    coefficients, diagnostics = fit_models(d, fitted_results=fitted)
    result, sample = fitted[name]
    diag = next(x for x in diagnostics if x['name'] == name)
    test = diag[category.removesuffix('_group') + '_likelihood_ratio_test']
    assert test['n'] == n and test['df'] == 1 and 0 <= test['p_value'] <= 1
    term = coefficients.loc[(coefficients.model == name) &
                            coefficients.term.str.startswith(f'C({category})')]
    assert len(term) == 1 and term.p_value.between(0, 1).all()
    table = prediction_table(result, sample)
    assert len(table) == 600
    grid = pd.DataFrame({'gender': table.gender, category: table[category],
        'log_opens_rate': np.log1p(table.opens_per_recorded_day),
        'log_likes_rate': np.log1p(table.reference_likes_per_recorded_day)})
    np.testing.assert_allclose(table.expected_matches_per_recorded_day,
                              result.predict(grid, offset=np.zeros(len(grid))))
