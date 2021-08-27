"""
This package contains checks for edx repo standards
"""
import codecs
import os
from configparser import ConfigParser
import glob
import pytest
import dockerfile

__version__ = "0.1.6"


GITHUB_URL_PATTERN = r"github.com[/:](?P<org_name>[^/]+)/(?P<repo_name>[^/]+).*#egg=(?P<package>[^\/]+).*"
PYPI_PACKAGE_PATTERN = r"(?P<package_name>[^\/]+)==(?P<version>[^\/]+)"
DJANGO_DEPS_SHEET_URL = "https://docs.google.com/spreadsheets/d/" \
                        "19-BzpcX3XvqlazHcLhn1ZifBMVNund15EwY3QQM390M/export?format=csv"


def parse_config_file(path):
    """
    Get the parsed content of an INI-style config file (using ConfigParser).
    Used for pytest fixtures.
    """
    config = ConfigParser()
    if os.path.exists(path):
        config.read(path)
    return config


def get_file_content(path):
    """
    Get the content of the UTF-8 text file at the specified path.
    Used for pytest fixtures.
    """
    if not os.path.exists(path):
        return ""
    with codecs.open(path, "r", "utf-8") as f:
        return f.read()


def get_file_lines(path):
    """
    Get a list of the lines in the UTF-8 text file at the specified path.
    Strips leading and trailing whitespace from each line.
    Used for pytest fixtures.
    """
    if not os.path.exists(path):
        return []
    with codecs.open(path, "r", "utf-8") as f:
        return [line.strip() for line in f.readlines()]


def get_file_names(path, file_type):
    """
    Get a list of files with given file_type in path's directory and its subdirectories
    If the directory is large, this might take forever, so use with care
    """
    path_pattern = path + "**/*." + file_type
    files = glob.glob(path_pattern, recursive=True)
    return files


@pytest.fixture(name='readme')
def fixture_readme(repo_path):
    """Fixture producing the text of the readme file."""
    # These checks don't care what the readme is called, just that it has the
    # right information in it.  So try a bunch of possibilities.
    for readme_name in ["README.rst", "README.md", "README.txt", "README"]:
        try:
            with open(os.path.join(repo_path, readme_name), encoding="utf-8") as freadme:
                return freadme.read()
        except FileNotFoundError:
            continue

    # There is no README at all, so nothing to check.
    return None


def read_docker_file(path):
    """
    Read the docker file using dockerfile package.
    """
    if not os.path.exists(path):
        return None

    return dockerfile.parse_file(path)
