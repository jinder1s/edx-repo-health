"""
 contains check that reads/parses dependencies of a repo
"""
import csv
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from packaging.version import parse

import pytest
import requests
from pytest_repo_health import health_metadata

from repo_health import get_file_lines, DJANGO_DEPS_SHEET_URL, GITHUB_URL_PATTERN, PYPI_PACKAGE_PATTERN
logger = logging.getLogger(__name__)

MODULE_DICT_KEY = "django_packages"


@pytest.fixture(scope='session')
def csv_filepath():
    tmpdir = tempfile.mkdtemp()
    return os.path.join(tmpdir, "django_dependencies_sheet.csv")


@pytest.fixture(name='django_deps_sheet', scope="session")
def django_dependency_sheet_fixture(csv_filepath):  # pylint: disable=redefined-outer-name
    """
    Returns the path for csv file which contains django dependencies status.
    Also, makes a request for latest sheet & dumps response into the csv file if request was successful.
    """
    res = requests.get(DJANGO_DEPS_SHEET_URL)
    if res.status_code == 200:
        with open(csv_filepath, 'w', encoding="utf8") as fp:
            fp.write(res.text)

    return csv_filepath


class DjangoDependencyReader:
    """
    Django dependency reader class
    """

    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.dependencies = {}

    def _is_python_repo(self) -> bool:
        return os.path.exists(os.path.join(self.repo_path, "requirements"))

    def _read_dependencies(self):
        """
        Method processing python requirements files
        """

        requirement_files = [str(file) for file
                             in Path(os.path.join(self.repo_path, "requirements")).rglob('*.txt')
                             if 'constraints' not in str(file)]

        for file_path in requirement_files:
            lines = get_file_lines(file_path)
            stripped_lines = [re.sub(r' +[;#].*', "", line).replace('-e ', "") for line in lines if line
                              and not any(line.startswith(start) for start in ['#', '-c', '-r'])]

            for line in stripped_lines:
                if 'git+http' in line:
                    name, version = self.extract_from_github_link(line)
                else:
                    name, version = self.extract_from_pypi_package(line)

                self.dependencies[name] = version

    @staticmethod
    def extract_from_github_link(github_dep) -> tuple:
        """
        Extracts the package name from Github URL
        """
        match = re.search(GITHUB_URL_PATTERN, github_dep)

        return match.group("package"), '' if match else ''

    @staticmethod
    def extract_from_pypi_package(pypi_dependency) -> tuple:
        """
        Sanitizes the package name from any version constraint and extra spaces
        """
        pypi_dependency = "".join(pypi_dependency.split())
        match = re.match(PYPI_PACKAGE_PATTERN, pypi_dependency)

        if match:
            return match.group('package_name'), match.group('version')

        return '', ''

    def read(self) -> dict:
        """
        Entry method for reading data
        """
        if not self._is_python_repo():
            return {}
        self._read_dependencies()

        return self.dependencies


def get_upgraded_dependencies_count(repo_path, django_dependency_sheet) -> tuple:
    """
    entry point to read parse and read dependencies
    @param repo_path:
    @param django_dependency_sheet:
    @return: dependencies_output
    """
    reader_instance = DjangoDependencyReader(repo_path)
    deps = reader_instance.read()
    django_deps = []
    deps_support_django32 = []
    upgraded_in_repo = []

    csv_path = django_dependency_sheet
    with open(csv_path, encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
        for line in csv_reader:
            package_name = line["Django Package Name"]
            if package_name in deps.keys():
                django_deps.append(package_name)

                if line["Django 3.2"] and line["Django 3.2"] != '-':
                    deps_support_django32.append(package_name)

                    if parse(deps[package_name]) >= parse(line["Django 3.2"]):
                        upgraded_in_repo.append(package_name)

    django_deps = list(set(django_deps))
    deps_support_django32 = list(set(deps_support_django32))
    upgraded_in_repo = list(set(upgraded_in_repo))

    return django_deps, deps_support_django32, upgraded_in_repo


@health_metadata(
    [MODULE_DICT_KEY],
    {
        "total": "Dependencies that depend on Django",
        "django_32": "Dependencies that support Django 3.2",
        "upgraded": "Dependencies that are upgraded to support Django 3.2"
    },
)
def check_django_dependencies_status(repo_path, all_results, django_deps_sheet):
    """
    Test to find the django dependencies compatibility
    """
    django_deps, support_django32_deps, upgraded_in_repo = get_upgraded_dependencies_count(
        repo_path, django_deps_sheet)

    all_results[MODULE_DICT_KEY] = {
        'total': {
            'count': len(django_deps),
            'list': json.dumps(django_deps),
        },
        'django_32': {
            'count': len(support_django32_deps),
            'list': json.dumps(support_django32_deps)
        },
        'upgraded': {
            'count': len(upgraded_in_repo),
            'list': json.dumps(upgraded_in_repo)
        }
    }
