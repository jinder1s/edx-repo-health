import os
import pytest

from repo_health.check_travis_yml import (
    check_yaml_parsable,
    check_has_tests_with_py38,
    check_travis_python_versions,
    fixture_parsed_data,
    fixture_python_version,
    fixture_travis_yaml,
    module_dict_key
)


def get_repo_path(repo_name):
    tests_directory = os.path.dirname(__file__)
    return f"{tests_directory}/fake_repos/{repo_name}"


@pytest.mark.parametrize("repo_path, result", [
    (get_repo_path('travis_repo1'), True),
    (get_repo_path('travis_repo2'), True),
    (get_repo_path('docs_repo'), False)
])
def test_check_yaml_parsable(travis_yml, result):
    all_results = {module_dict_key: {}}
    check_yaml_parsable(travis_yml, all_results)

    assert all_results[module_dict_key]['parsable'] == result


@pytest.mark.parametrize("repo_path, result", [
    (get_repo_path('travis_repo1'), True),
    (get_repo_path('travis_repo2'), False),
    (get_repo_path('docs_repo'), False),
])
def test_check_has_tests_with_py38(python_versions_in_travis, result):
    all_results = {module_dict_key: {}}
    check_has_tests_with_py38(python_versions_in_travis, all_results)

    assert all_results[module_dict_key]['py38_tests'] == result


@pytest.mark.parametrize("repo_path, result_list", [
    (get_repo_path('travis_repo1'), [3.6, 3.8]),
    (get_repo_path('travis_repo2'), [3.5]),
    (get_repo_path('docs_repo'), [])
])
def test_check_travis_python_versions(python_versions_in_travis, result_list):
    all_results = {module_dict_key: {}}
    check_travis_python_versions(python_versions_in_travis, all_results)

    for field in all_results[module_dict_key]['python_versions']:
        assert field in result_list
