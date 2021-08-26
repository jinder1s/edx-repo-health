import os
import pytest

from repo_health.check_django_dependencies_compatibility import (
    MODULE_DICT_KEY,
    check_django_dependencies_status,
)

TEST_CSV_PATH = os.path.join(os.path.dirname(__file__), 'data/mock_django_dependencies_sheet.csv')


def get_repo_path(repo_name):
    tests_directory = os.path.dirname(__file__)
    return f"{tests_directory}/fake_repos/{repo_name}"


@pytest.mark.parametrize("repo_path", [get_repo_path("python_repo")])
def test_django_deps_upgrade(repo_path):
    all_results = {MODULE_DICT_KEY: {}}
    check_django_dependencies_status(repo_path, all_results, TEST_CSV_PATH)

    assert all_results[MODULE_DICT_KEY]
    assert all_results[MODULE_DICT_KEY]['total']['count'] == 3
    assert all_results[MODULE_DICT_KEY]['django_32']['count'] == 2
    assert all_results[MODULE_DICT_KEY]['upgraded']['count'] == 1

    assert 'django-waffle' in all_results[MODULE_DICT_KEY]['total']['list']
    assert 'django-waffle' not in all_results[MODULE_DICT_KEY]['django_32']['list']

    assert 'edx-django-utils' in all_results[MODULE_DICT_KEY]['django_32']['list']

    assert 'edx-django-utils' not in all_results[MODULE_DICT_KEY]['upgraded']['list']
    assert 'djangorestframework' in all_results[MODULE_DICT_KEY]['upgraded']['list']


@pytest.mark.parametrize("repo_path", [get_repo_path("js_repo")])
def test_django_deps_upgrade_non_django_repo(repo_path):
    all_results = {MODULE_DICT_KEY: {}}
    check_django_dependencies_status(repo_path, all_results, TEST_CSV_PATH)

    assert all_results[MODULE_DICT_KEY]
    assert all_results[MODULE_DICT_KEY]['total']['count'] == 0
    assert all_results[MODULE_DICT_KEY]['django_32']['count'] == 0
    assert all_results[MODULE_DICT_KEY]['upgraded']['count'] == 0
