"""Issue tracker adapters - implementations for various platforms."""

from spectra.adapters.jira import JiraAdapter
from spectra.adapters.github import GitHubAdapter
from spectra.adapters.azure_devops import AzureDevOpsAdapter
from spectra.adapters.linear import LinearAdapter
from spectra.adapters.confluence import ConfluenceAdapter

__all__ = [
    "JiraAdapter",
    "GitHubAdapter",
    "AzureDevOpsAdapter",
    "LinearAdapter",
    "ConfluenceAdapter",
]

