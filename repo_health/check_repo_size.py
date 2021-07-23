"""
Checks repository size github.
"""
import json
import logging
import os
import re

import requests
from pytest_repo_health import add_key_to_metadata

logger = logging.getLogger(__name__)

module_dict_key = "check_repo_size"

URL_PATTERN = r"github.com[/:](?P<org_name>[^/]+)/(?P<repo_name>[^/]+).git"

# list of services with their respective size.
ONLY_SERVICES = [{'edx-platform': 11111, 'credentials': 9596, 'registrar': 3201}]


def get_api_response(repo_name):
    """
    get the repo information using api.
    """
    # For unauthenticated requests, the rate limit allows for up to 60 requests per hour.
    # https://developer.github.com/v3/#rate-limiting
    for data in ONLY_SERVICES:
        if repo_name in data:
            return requests.get(
                url=f'https://api.github.com/repos/edx/{repo_name}',
                headers={'Authorization': f'Bearer {os.environ["GITHUB_TOKEN"]}'}
            )


class GitHubIntegrationHandler:
    """
    sets up the operations and required  github actions workflow CI integration information on instance
    """

    def __init__(self, repo_name):
        self.repo_name = repo_name
        self.api_data = None
        self._set_github_actions_integration_data()

    def _set_github_actions_integration_data(self):
        self.api_response = get_api_response(self.repo_name)

    def handle(self):
        """
        initiates the process to fetch github repo info
        """
        if not self.api_response:
            logger.error(
                "An error occurred while fetching repo %s.",
                self.repo_name
            )
            return

        if self.api_response.status_code != 200:
            logger.error(
                "An error occurred while fetching %s. status code %s content info %s.",
                self.repo_name,
                self.api_response.status_code,
                self.api_response.content
            )
            return

        self.api_data = json.loads(self.api_response.content)

        if self.api_data and 'size' in self.api_data:
            return self.api_data.get('size')


@add_key_to_metadata(module_dict_key)
def check_repo_size(all_results, git_origin_url):
    """
    Checks repository size github.
    """
    match = re.search(URL_PATTERN, git_origin_url)
    repo_name = match.group("repo_name")
    integration_handler = GitHubIntegrationHandler(repo_name)
    all_results[module_dict_key] = integration_handler.handle()
