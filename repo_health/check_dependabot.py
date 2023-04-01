"""
Checks to identify whether the Dependabot file exists and which ecosystems are covered under Dependabot
"""
from collections import OrderedDict

import pytest
import yaml
from pytest_repo_health import add_key_to_metadata, health_metadata

from repo_health import get_file_content

module_dict_key = "dependabot"
dependabot_path=".github/dependabot.yml"


@pytest.fixture(name="dependabot_yml")
def fixture_dependabot_yml():
    """Fixture containing the text content of dependabot.yml"""
    return get_file_content(dependabot_path)


@add_key_to_metadata((module_dict_key, "exists"))
def check_dependabot_exists(dependabot_yml, all_results):
    """
    Is dependabot.yml file exists
    """
    all_results[module_dict_key]["exists"] = bool(dependabot_yml)


@health_metadata(
    [module_dict_key, "has_ecosystem"],
    {
        "github_action": "ecosystem to check github actions version upgrades ",
        "pip": "ecosystem to check pip package version upgrades",
        "npm": "ecosystem to check node package version upgrades"
    },
)
def check_has_ecosystems(dependabot_yml, all_results):
    """
    Is dependabot.yml has github_action, pip, npm ecosystems/sections
    """
    ecosystems = ["pip", "npm", "github-actions"]
    all_results[module_dict_key]["has_ecosystem"] = {}
    for ecosystem in ecosystems:
        found = False
        if dependabot_yml:
            dependabot_elements = []
            with open(dependabot_path) as file_stream:
                dependabot_elements = OrderedDict(
                    yaml.safe_load(file_stream.read())
                )
            dependabot_elements['updates'] = dependabot_elements.get('updates') or []
            for index in dependabot_elements['updates']:
                if ecosystem == index.get('package-ecosystem'):
                    found = True
        all_results[module_dict_key]["has_ecosystem"][ecosystem] = found
