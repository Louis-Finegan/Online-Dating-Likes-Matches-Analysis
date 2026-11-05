import numpy as np
import pandas as pd
from dating_research.model_figures import mean_interval, prediction_table, make_model_figures
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
    assert len(fitted) == 3, diagnostics
    for name in ('likes_and_activity', 'activity_interaction'):
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
    assert len(figures) == 4
    assert all((tmp_path / f'{name}.{ext}').is_file() for name in figures for ext in ('png', 'pdf'))


def test_no_model_plots_for_skipped_fits(tmp_path):
    assert make_model_figures(pd.DataFrame(), {}, tmp_path) == []
    assert not list(tmp_path.iterdir())


def test_education_fit_tests_and_prediction_design():
    rng = np.random.default_rng(82)
    n = 400
    d = pd.DataFrame({'gender': np.tile(['Female', 'Male'], n // 2),
        'education_group': pd.Categorical(np.tile(['No listed education'] * 2 + ['Listed education'] * 2, n // 4),
            categories=['No listed education', 'Listed education']),
        'recorded_days': rng.integers(5, 30, n),
        'log_likes_rate': rng.uniform(0, 3, n), 'log_opens_rate': rng.uniform(0, 2, n)})
    mu = d.recorded_days * np.exp(-1 + 0.3 * d.log_likes_rate +
        0.4 * d.log_opens_rate + 0.8 * (d.education_group == 'Listed education'))
    d['matches'] = rng.negative_binomial(3, 3 / (3 + mu))
    fitted = {}
    coefficients, diagnostics = fit_models(d, fitted_results=fitted)
    result, sample = fitted['education_adjusted']
    diag = next(x for x in diagnostics if x['name'] == 'education_adjusted')
    test = diag['education_likelihood_ratio_test']
    assert test['n'] == n and test['df'] == 1 and 0 <= test['p_value'] <= 1
    term = coefficients.loc[(coefficients.model == 'education_adjusted') &
                            coefficients.term.str.startswith('C(education_group)')]
    assert len(term) == 1 and term.p_value.between(0, 1).all()
    table = prediction_table(result, sample)
    assert len(table) == 600
    grid = pd.DataFrame({'gender': table.gender, 'education_group': table.education_group,
        'log_opens_rate': np.log1p(table.opens_per_recorded_day),
        'log_likes_rate': np.log1p(table.reference_likes_per_recorded_day)})
    np.testing.assert_allclose(table.expected_matches_per_recorded_day,
                              result.predict(grid, offset=np.zeros(len(grid))))
