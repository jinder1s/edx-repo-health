"""
Checks to see if setup.py follows minimum standards
And gathers info
"""

import re

from pytest_repo_health import add_key_to_metadata

from .fixtures.config_files import (fixture_python_version, fixture_setup_cfg,  # pylint: disable=unused-import
                                    fixture_setup_py)

module_dict_key = "setup_py"


@add_key_to_metadata((module_dict_key, "py38_classifiers"))
def check_has_python_38_classifiers(fixture_python_version, all_results):
    """
    Are there classifiers with python 3.8?
    """
    all_results[module_dict_key]["py38_classifiers"] = "3.8" in fixture_python_version


@add_key_to_metadata((module_dict_key, "python_versions"))
def check_travis_python_versions(fixture_python_version, all_results):
    """
    Add list of python versions to the results
    """
    all_results[module_dict_key]["python_versions"] = fixture_python_version


def set_pypi_name(all_results, fixture_setup_py, fixture_setup_cfg):
    """"
    A generic function that is use to set pypi name in the all_results dict
    """
    # Look in setup.py for:     name="package",
    py_names = re.findall(r"""(?m)^\s+name\s?=\s?['"]([\w-]+)['"],""", fixture_setup_py)
    # Look in setup.cfg for:    name=package
    cfg_names = re.findall(r"""(?m)^name\s?=\s?([\w-]+)""", fixture_setup_cfg)

    names = py_names + cfg_names
    # If the name doesn't match the expected format, don't fill it into the results.
    if names and len(names) == 1:
        all_results[module_dict_key]["pypi_name"] = names[0]
    return all_results


def set_repo_url(all_results, fixture_setup_py, fixture_setup_cfg):
    """
    A generic function that is use to set repo url in the all_results dict
    """
    py_urls = re.findall(r"""(?m)^\s*url\s*=\s*['"]([^'"]+)['"]""", fixture_setup_py)
    cfg_urls = re.findall(r"""(?m)^url\s*=\s*(\S+)""", fixture_setup_cfg)
    urls = py_urls + cfg_urls
    if urls:
        assert len(urls) == 1
        all_results[module_dict_key]["repo_url"] = urls[0]
    return all_results


def set_project_urls(all_results, fixture_setup_py, fixture_setup_cfg):
    """
    A generic function that is use to set project url in the all_results dict
    """
    py_urls = re.findall(r"""(?ms)^\s*project_urls\s*=\s*({[^}]+})""", fixture_setup_py)
    cfg_urls = re.findall(r"""(?ms)^project_urls\s*=\s*(.*?)(?:^\S|^$)""", fixture_setup_cfg)
    urls = py_urls + cfg_urls
    if urls:
        assert len(urls) == 1
        all_results[module_dict_key]["project_urls"] = urls[0]
    return all_results


@add_key_to_metadata((module_dict_key, "pypi_name"))
def check_pypi_name(fixture_setup_py, fixture_setup_cfg, all_results):
    """
    Get the name of the PyPI package for this repo.
    """
    all_results = set_pypi_name(
        all_results,
        fixture_setup_py,
        fixture_setup_cfg
    )


@add_key_to_metadata((module_dict_key, "repo_url"))
def check_repo_url(fixture_setup_py, fixture_setup_cfg, all_results):
    """
    Get the repo URL.
    """
    all_results = set_repo_url(
        all_results,
        fixture_setup_py,
        fixture_setup_cfg
    )


@add_key_to_metadata((module_dict_key, "project_urls"))
def check_project_urls(fixture_setup_py, fixture_setup_cfg, all_results):
    """
    Get the additional project URLs.
    TODO: This captures the multi-line junk without parsing them out individually.
    """
    all_results = set_project_urls(
        all_results,
        fixture_setup_py,
        fixture_setup_cfg
    )
