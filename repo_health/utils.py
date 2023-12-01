"""
Utility Functions
"""

import csv
import functools
import requests
import json
import operator
import os
import re
from pathlib import Path
from datetime import datetime

from packaging.version import parse

from repo_health import get_file_lines

GITHUB_DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"
GITHUB_URL_PATTERN = r"github.com[/:](?P<org_name>[^/]+)/(?P<repo_name>[^/]+).*#egg=(?P<package>[^\/]+).*"
PYPI_PACKAGE_PATTERN = r"(?P<package_name>[^\/]+)==(?P<version>[^\/]+)"


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

            for line in lines:
                stripped_line = self.strip_requirement(line)
                if not stripped_line:
                    continue

                if 'git+http' in stripped_line:
                    name, version = self.extract_from_github_link(stripped_line)
                else:
                    name, version = self.extract_from_pypi_package(stripped_line)

                self.dependencies[name] = version

    @staticmethod
    def strip_requirement(line):
        """
        Finds if the requirement line is actually a requirement & not a reference to other files
        """
        if line and not re.search('^[#-]', line):
            return re.sub(r' +[;#].*', "", line).replace('-e ', "")

        return None

    @staticmethod
    def extract_from_github_link(github_dep) -> tuple:
        """
        Extracts the package name from Github URL
        """
        match = re.search(GITHUB_URL_PATTERN, github_dep)

        if match:
            return match.group("package"), ''

        return '', ''

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
    Entry point to read, parse and calculate django dependencies
    @param repo_path: path for repo which we are calculating django deps
    @param django_dependency_sheet: csv which contains latest status of django deps
    @return: count for all + upgraded django deps in repo
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
            if package_name in deps.keys():  # pylint: disable=consider-iterating-dictionary
                django_deps.append(package_name)

                if line["Django 3.2"] and line["Django 3.2"] != '-':
                    deps_support_django32.append(package_name)

                    if parse(deps[package_name]) >= parse(line["Django 3.2"]):
                        upgraded_in_repo.append(package_name)

    django_deps = list(set(django_deps))
    deps_support_django32 = list(set(deps_support_django32))
    upgraded_in_repo = list(set(upgraded_in_repo))

    return django_deps, deps_support_django32, upgraded_in_repo


def file_exists(repo_path, file_name):
    full_path = os.path.join(repo_path, file_name)
    return os.path.isfile(full_path)


def dir_exists(repo_path, dir_name):
    full_path = os.path.join(repo_path, dir_name)
    return os.path.isdir(full_path)


def parse_build_duration_response(json_response):
    """
    This function is responsible for parsing Github GraphQL API response and calculating build duration.

    Returns None when repo is uninitialized.
    """
    build_checks = []
    first_started_at = None
    last_completed_at = None
    total_duration = ''

    # Handle uninitialized repos (missing default branch, or no commits on branch)
    try:
        latest_commits = functools.reduce(
            operator.getitem, ["node", "defaultBranchRef", "target", "history", "edges"], json_response)
    except TypeError:
        return None

    if not latest_commits:
        return None
    else:
        latest_commit = latest_commits[0]

    for check_suite in functools.reduce(operator.getitem, ['node', 'checkSuites', 'edges'], latest_commit):

        all_check_runs = check_suite['node']['checkRuns']['edges']
        for check_run in all_check_runs:
            # If check is still in progress, skip it
            if not check_run['node']['completedAt']:
                continue

            name = check_run['node']['name']
            started_at = datetime.strptime(check_run['node']['startedAt'], GITHUB_DATETIME_FMT)
            completed_at = datetime.strptime(check_run['node']['completedAt'], GITHUB_DATETIME_FMT)

            if not first_started_at or started_at < first_started_at:
                first_started_at = started_at
            if not last_completed_at or completed_at > last_completed_at:
                last_completed_at = completed_at

            job_duration = completed_at - started_at
            total_seconds = job_duration.total_seconds()
            minutes, remaining_seconds = divmod(total_seconds, 60)

            build_checks.append({
                'name': name,
                'duration': f'{int(minutes)} minutes {int(remaining_seconds)} seconds',
                'seconds': total_seconds
            })

    if build_checks:
        # sorting checks into descending order of duration to get slowest check on top
        build_checks = sorted(build_checks, key=lambda k: k['seconds'], reverse=True)
        for check in build_checks:
            del check['seconds']

        build_duration = last_completed_at - first_started_at
        minutes, remaining_seconds = divmod(build_duration.total_seconds(), 60)

        total_duration = f'{int(minutes)} minutes {int(remaining_seconds)} seconds'

    return total_duration, build_checks


URL_PATTERN = r"github.com[/:](?P<org_name>[^/]+)/(?P<repo_name>[^/]+).git"

def github_org_repo(git_origin_url):
    """Return the org and repo from a GitHub URL."""
    match = re.search(URL_PATTERN, git_origin_url)
    assert match is not None
    return match.groups()


def get_branch_or_pr_count(org_name, repo_name, pulls_or_branches):
    """
    Get the count for branches or pull requests using Github API and add the count to report
    """
    url = f"https://api.github.com/repos/{org_name}/{repo_name}/{pulls_or_branches}?per_page=1"
    count = 0

    response = requests.get(url=url, headers={'Authorization': f'Bearer {os.environ["GITHUB_TOKEN"]}'})
    if response.ok and json.loads(response.content):
        count = 1
        if 'last' in response.links:
            last_page = response.links['last']['url']
            count = int(re.findall(r'page=(\d+)', last_page)[1])

    return count


def set_branch_and_pr_count(all_results, git_origin_url, module_dict_key):
    """
    Takes all_results dict and update branch and pr counts using git_origin_url
    """
    org_name, repo_name = github_org_repo(git_origin_url)
    all_results[module_dict_key]['branch_count'] = get_branch_or_pr_count(org_name, repo_name, 'branches')
    all_results[module_dict_key]['pulls_count'] = get_branch_or_pr_count(org_name, repo_name, 'pulls')
    return all_results


def set_pypi_name(all_results, setup_py, setup_cfg, module_dict_key):
    # Look in setup.py for:     name="package",
    py_names = re.findall(r"""(?m)^\s+name\s?=\s?['"]([\w-]+)['"],""", setup_py)
    # Look in setup.cfg for:    name=package
    cfg_names = re.findall(r"""(?m)^name\s?=\s?([\w-]+)""", setup_cfg)

    names = py_names + cfg_names
    # If the name doesn't match the expected format, don't fill it into the results.
    if names and len(names) == 1:
        all_results[module_dict_key]["pypi_name"] = names[0]
    return all_results


def set_repo_url(all_results, setup_py, setup_cfg, module_dict_key):
    py_urls = re.findall(r"""(?m)^\s*url\s*=\s*['"]([^'"]+)['"]""", setup_py)
    cfg_urls = re.findall(r"""(?m)^url\s*=\s*(\S+)""", setup_cfg)
    urls = py_urls + cfg_urls
    if urls:
        assert len(urls) == 1
        all_results[module_dict_key]["repo_url"] = urls[0]
    return all_results


def set_project_urls(all_results, setup_py, setup_cfg, module_dict_key):
    py_urls = re.findall(r"""(?ms)^\s*project_urls\s*=\s*({[^}]+})""", setup_py)
    cfg_urls = re.findall(r"""(?ms)^project_urls\s*=\s*(.*?)(?:^\S|^$)""", setup_cfg)
    urls = py_urls + cfg_urls
    if urls:
        assert len(urls) == 1
        all_results[module_dict_key]["project_urls"] = urls[0]
    return all_results


def set_django_packages(repo_path, all_results, django_deps_sheet, module_dict_key):
    django_deps, support_django32_deps, upgraded_in_repo = get_upgraded_dependencies_count(
        repo_path, django_deps_sheet)

    all_results[module_dict_key] = {
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

    return all_results