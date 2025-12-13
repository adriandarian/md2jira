# Basic Example - Manage a Jira Story with Subtasks
#
# This example demonstrates how to create a Story with subtasks using Terraform.

terraform {
  required_providers {
    jira = {
      source  = "md2jira/jira"
      version = "~> 1.0"
    }
  }
}

# Configure the Jira Provider
provider "jira" {
  # Credentials can be set via environment variables:
  # - JIRA_URL
  # - JIRA_EMAIL
  # - JIRA_API_TOKEN
  #
  # Or configured here (not recommended for api_token):
  # url       = "https://your-company.atlassian.net"
  # email     = "your-email@company.com"
  # api_token = var.jira_api_token
}

# Variables
variable "project_key" {
  description = "Jira project key"
  type        = string
  default     = "PROJ"
}

# Create a User Story
resource "jira_issue" "user_login" {
  project     = var.project_key
  summary     = "US-001: User Login Feature"
  issue_type  = "Story"
  priority    = "Medium"
  labels      = ["authentication", "sprint-1"]

  description = <<-EOT
    As a user
    I want to login to the application
    So that I can access my personalized dashboard

    ## Acceptance Criteria
    - User can enter email and password
    - System validates credentials
    - User is redirected to dashboard on success
    - Error message shown on invalid credentials
  EOT
}

# Create subtasks for the story
resource "jira_subtask" "backend_api" {
  project     = var.project_key
  parent_key  = jira_issue.user_login.key
  summary     = "Implement authentication API"
  story_points = 3
  
  description = <<-EOT
    Create REST endpoint for user authentication:
    - POST /api/auth/login
    - Validate credentials against database
    - Return JWT token on success
  EOT
}

resource "jira_subtask" "frontend_form" {
  project     = var.project_key
  parent_key  = jira_issue.user_login.key
  summary     = "Create login form component"
  story_points = 2
  
  description = <<-EOT
    Build React login form:
    - Email and password inputs
    - Form validation
    - Submit handler
    - Error display
  EOT
}

resource "jira_subtask" "integration" {
  project     = var.project_key
  parent_key  = jira_issue.user_login.key
  summary     = "Integrate frontend with backend"
  story_points = 2
  
  description = <<-EOT
    Connect login form to API:
    - API client for auth endpoint
    - Token storage in localStorage
    - Redirect logic
  EOT
}

resource "jira_subtask" "testing" {
  project     = var.project_key
  parent_key  = jira_issue.user_login.key
  summary     = "Write tests for login feature"
  story_points = 2
  
  description = <<-EOT
    Test coverage:
    - Unit tests for API endpoint
    - Unit tests for React components
    - Integration tests for full flow
    - E2E test with Cypress
  EOT
}

# Outputs
output "story_key" {
  description = "The created story key"
  value       = jira_issue.user_login.key
}

output "subtask_keys" {
  description = "All subtask keys"
  value = [
    jira_subtask.backend_api.key,
    jira_subtask.frontend_form.key,
    jira_subtask.integration.key,
    jira_subtask.testing.key,
  ]
}

