#!/usr/bin/env python
"""
Package metadata for repo_health.
"""
import os
import re
import sys

from setuptools import setup


def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename, encoding="utf8").read()  # pylint: disable=consider-using-with
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns:
        list: Requirements file relative path strings
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split("#")[0].strip()
            for line in open(path, encoding="utf8").readlines()  # pylint: disable=consider-using-with
            if is_requirement(line.strip())
        )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.
    Returns:
        bool: True if the line is not blank, a comment, a URL, or an included file
    """
    return line and not line.startswith(("-r", "#", "-e", "git+", "-c"))


VERSION = "0.1.6"

if sys.argv[-1] == "tag":
    print("Tagging the version on github:")
    os.system("git tag -a %s -m 'version %s'" % (VERSION, VERSION))  # pylint: disable=consider-using-f-string
    os.system("git push --tags")
    sys.exit()

README = open(os.path.join(os.path.dirname(__file__), "README.rst"), encoding="utf8").read()  # pylint: disable=consider-using-with

setup(
    name="edx-repo-health",
    version=VERSION,
    description="""blah blah blah""",
    long_description=README,
    author="edX",
    author_email="oscm@edx.org",
    url="https://github.com/edx/edx-repo-health",
    include_package_data=True,
    install_requires=load_requirements("requirements/base.in"),
    packages=["repo_health_dashboard", "repo_health_dashboard.utils"],
    python_requires=">=3.5",
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords="Django edx",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    entry_points={
        "console_scripts": [
            "repo_health_dashboard = repo_health_dashboard.repo_health_dashboard:main",
            "run_checks = scripts.run_checks:main",
        ]
    },
)
