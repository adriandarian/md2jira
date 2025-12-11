"""
Jira API Client - Low-level HTTP client for Jira REST API.

This handles the raw HTTP communication with Jira.
The JiraAdapter uses this to implement the IssueTrackerPort.
"""

import logging
from typing import Any, Optional

import requests

from ...core.ports.issue_tracker import (
    IssueTrackerError,
    AuthenticationError,
    NotFoundError,
    PermissionError,
)


class JiraApiClient:
    """
    Low-level Jira REST API client.
    
    Handles authentication, request/response, and error handling.
    """
    
    API_VERSION = "3"
    
    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        dry_run: bool = True,
    ):
        """
        Initialize the Jira client.
        
        Args:
            base_url: Jira instance URL (e.g., https://company.atlassian.net)
            email: User email for authentication
            api_token: API token
            dry_run: If True, don't make write operations
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/rest/api/{self.API_VERSION}"
        self.auth = (email, api_token)
        self.dry_run = dry_run
        self.logger = logging.getLogger("JiraApiClient")
        
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        self._session = requests.Session()
        self._session.auth = self.auth
        self._session.headers.update(self.headers)
        
        self._current_user: Optional[dict] = None
    
    # -------------------------------------------------------------------------
    # Core Request Methods
    # -------------------------------------------------------------------------
    
    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Make an authenticated request to Jira API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., 'issue/PROJ-123')
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON response as dict
            
        Raises:
            IssueTrackerError: On API errors
        """
        url = f"{self.api_url}/{endpoint}"
        
        try:
            response = self._session.request(method, url, **kwargs)
            return self._handle_response(response, endpoint)
        except requests.exceptions.ConnectionError as e:
            raise IssueTrackerError(f"Connection failed: {e}", cause=e)
        except requests.exceptions.Timeout as e:
            raise IssueTrackerError(f"Request timed out: {e}", cause=e)
    
    def get(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """GET request."""
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, json: dict = None, **kwargs) -> dict[str, Any]:
        """POST request (checks dry_run for mutations)."""
        if self.dry_run and not endpoint.endswith("/search/jql"):
            self.logger.info(f"[DRY-RUN] Would POST to {endpoint}")
            return {}
        return self.request("POST", endpoint, json=json, **kwargs)
    
    def put(self, endpoint: str, json: dict = None, **kwargs) -> dict[str, Any]:
        """PUT request (checks dry_run)."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would PUT to {endpoint}")
            return {}
        return self.request("PUT", endpoint, json=json, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> dict[str, Any]:
        """DELETE request (checks dry_run)."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would DELETE {endpoint}")
            return {}
        return self.request("DELETE", endpoint, **kwargs)
    
    # -------------------------------------------------------------------------
    # Response Handling
    # -------------------------------------------------------------------------
    
    def _handle_response(
        self,
        response: requests.Response,
        endpoint: str
    ) -> dict[str, Any]:
        """Handle API response and errors."""
        if response.ok:
            if response.text:
                return response.json()
            return {}
        
        # Handle specific error codes
        status = response.status_code
        error_body = response.text[:500] if response.text else ""
        
        if status == 401:
            raise AuthenticationError(
                "Authentication failed. Check JIRA_EMAIL and JIRA_API_TOKEN."
            )
        
        if status == 403:
            raise PermissionError(
                f"Permission denied for {endpoint}",
                issue_key=endpoint
            )
        
        if status == 404:
            raise NotFoundError(
                f"Not found: {endpoint}",
                issue_key=endpoint
            )
        
        # Generic error
        raise IssueTrackerError(
            f"API error {status}: {error_body}",
            issue_key=endpoint
        )
    
    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------
    
    def get_myself(self) -> dict[str, Any]:
        """Get current authenticated user."""
        if self._current_user is None:
            self._current_user = self.get("myself")
        return self._current_user
    
    def get_current_user_id(self) -> str:
        """Get current user's account ID."""
        return self.get_myself()["accountId"]
    
    def search_jql(
        self,
        jql: str,
        fields: list[str],
        max_results: int = 100
    ) -> dict[str, Any]:
        """Execute JQL search."""
        return self.post(
            "search/jql",
            json={
                "jql": jql,
                "maxResults": max_results,
                "fields": fields,
            }
        )
    
    def test_connection(self) -> bool:
        """Test if connection is valid."""
        try:
            self.get_myself()
            return True
        except IssueTrackerError:
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._current_user is not None

