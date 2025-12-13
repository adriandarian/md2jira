# Epic Example - Manage an Epic with Stories
#
# This example shows how to create an Epic with multiple child Stories.

terraform {
  required_providers {
    jira = {
      source  = "md2jira/jira"
      version = "~> 1.0"
    }
  }
}

provider "jira" {}

variable "project_key" {
  description = "Jira project key"
  type        = string
  default     = "PROJ"
}

# Create the Epic
resource "jira_issue" "auth_epic" {
  project     = var.project_key
  summary     = "Authentication System"
  issue_type  = "Epic"
  priority    = "High"
  labels      = ["Q1-2024", "security"]

  description = <<-EOT
    Complete authentication system for the application.
    
    ## Goals
    - Secure user authentication
    - Password recovery
    - Session management
    - OAuth2 integration
    
    ## Timeline
    Sprint 1-3
  EOT
}

# Stories in the Epic
resource "jira_issue" "login_story" {
  project     = var.project_key
  summary     = "User Login"
  issue_type  = "Story"
  parent_key  = jira_issue.auth_epic.key
  priority    = "High"
  labels      = ["sprint-1"]

  description = <<-EOT
    As a user
    I want to login with my credentials
    So that I can access the application
  EOT
}

resource "jira_issue" "logout_story" {
  project     = var.project_key
  summary     = "User Logout"
  issue_type  = "Story"
  parent_key  = jira_issue.auth_epic.key
  priority    = "Medium"
  labels      = ["sprint-1"]

  description = <<-EOT
    As a user
    I want to logout from the application
    So that I can secure my session
  EOT
}

resource "jira_issue" "password_reset_story" {
  project     = var.project_key
  summary     = "Password Reset"
  issue_type  = "Story"
  parent_key  = jira_issue.auth_epic.key
  priority    = "Medium"
  labels      = ["sprint-2"]

  description = <<-EOT
    As a user
    I want to reset my password
    So that I can recover access to my account
  EOT
}

resource "jira_issue" "oauth_story" {
  project     = var.project_key
  summary     = "OAuth2 Integration"
  issue_type  = "Story"
  parent_key  = jira_issue.auth_epic.key
  priority    = "Low"
  labels      = ["sprint-3"]

  description = <<-EOT
    As a user
    I want to login with Google/GitHub
    So that I don't need to remember another password
  EOT
}

# Outputs
output "epic" {
  value = {
    key     = jira_issue.auth_epic.key
    summary = jira_issue.auth_epic.summary
  }
}

output "stories" {
  value = [
    { key = jira_issue.login_story.key, summary = jira_issue.login_story.summary },
    { key = jira_issue.logout_story.key, summary = jira_issue.logout_story.summary },
    { key = jira_issue.password_reset_story.key, summary = jira_issue.password_reset_story.summary },
    { key = jira_issue.oauth_story.key, summary = jira_issue.oauth_story.summary },
  ]
}

