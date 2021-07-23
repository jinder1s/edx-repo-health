"""
Checks to see if travis.yml follows minimum standards
And gathers info
"""
import os
from collections.abc import Iterable
import pytest
import yaml
from pytest_repo_health import add_key_to_metadata
from repo_health import get_file_content


module_dict_key = "travis_yml"


@pytest.fixture(name="travis_yml")
def fixture_travis_yaml(repo_path):
    """Fixture containing the text content of travis.yml"""
    full_path = os.path.join(repo_path, ".travis.yml")
    return get_file_content(full_path)


@pytest.fixture(name="parsed_data_travis")
def fixture_parsed_data(travis_yml):
    """
    Parses travis.yml returns resulting dict.
    """
    try:
        data = yaml.safe_load(travis_yml)
        if data is None:
            return {}
        return data
    except yaml.YAMLError:
        return {}


@add_key_to_metadata((module_dict_key, "parsable"))
def check_yaml_parsable(travis_yml, all_results):
    """
    Is the travis.yml file computer parsable
    """
    try:
        data = yaml.safe_load(travis_yml)
        all_results[module_dict_key]["parsable"] = bool(data)
    except yaml.YAMLError:
        all_results[module_dict_key]["parsable"] = False


def get_python_versions(travis_python_versions):
    """
    @return list of float python versions
    """
    python_versions = []
    if isinstance(travis_python_versions, Iterable) and not isinstance(travis_python_versions, str):
        for python_version in travis_python_versions:
            python_versions.append(float(python_version))
        return python_versions
    else:
        return [float(travis_python_versions)]


@pytest.fixture(name="python_versions_in_travis")
def fixture_python_version(parsed_data_travis):
    """
    The list of python versions in travis tests
    """
    python_versions = set()

    if "python" in parsed_data_travis.keys():
        python_versions = get_python_versions(parsed_data_travis["python"])
        python_versions = set(python_versions)

    if "matrix" in parsed_data_travis.keys():
        workers = None
        if isinstance(parsed_data_travis["matrix"], dict):
            if "include" in parsed_data_travis["matrix"].keys():
                workers = parsed_data_travis["matrix"]["include"]
        elif isinstance(parsed_data_travis["matrix"], list):
            workers = parsed_data_travis["matrix"]
        if workers:
            for worker in workers:
                if isinstance(worker, dict) and "python" in worker.keys():
                    python_versions.add(worker["python"])

    if python_versions:
        python_versions = sorted(python_versions, key=str)
    else:
        python_versions = []
    return python_versions


@add_key_to_metadata((module_dict_key, "py38_tests"))
def check_has_tests_with_py38(python_versions_in_travis, all_results):
    """
    Are there tests with python 3.8?
    """
    all_results[module_dict_key]["py38_tests"] = 3.8 in python_versions_in_travis


@add_key_to_metadata((module_dict_key, "python_versions"))
def check_travis_python_versions(python_versions_in_travis, all_results):
    """
    Add list of python versions to the results
    """
    all_results[module_dict_key]["python_versions"] = python_versions_in_travis
