# Data Sources Example - Read Existing Jira Data
#
# This example shows how to read existing Jira issues and projects.

terraform {
  required_providers {
    jira = {
      source  = "md2jira/jira"
      version = "~> 1.0"
    }
  }
}

provider "jira" {}

# Read an existing project
data "jira_project" "main" {
  key = "PROJ"
}

# Read an existing issue
data "jira_issue" "existing_epic" {
  key = "PROJ-100"
}

# Create a new story under the existing epic
resource "jira_issue" "new_story" {
  project     = data.jira_project.main.key
  summary     = "New Feature Story"
  description = "This story is created under an existing epic"
  issue_type  = "Story"
  parent_key  = data.jira_issue.existing_epic.key
}

# Create subtasks for the new story
resource "jira_subtask" "implementation" {
  project     = data.jira_project.main.key
  parent_key  = jira_issue.new_story.key
  summary     = "Implementation"
  description = "Implement the feature"
}

resource "jira_subtask" "testing" {
  project     = data.jira_project.main.key
  parent_key  = jira_issue.new_story.key
  summary     = "Testing"
  description = "Write tests for the feature"
}

# Outputs
output "project_info" {
  value = {
    key  = data.jira_project.main.key
    name = data.jira_project.main.name
    id   = data.jira_project.main.id
  }
}

output "existing_epic" {
  value = {
    key         = data.jira_issue.existing_epic.key
    summary     = data.jira_issue.existing_epic.summary
    status      = data.jira_issue.existing_epic.status
    issue_type  = data.jira_issue.existing_epic.issue_type
  }
}

output "new_story" {
  value = {
    key     = jira_issue.new_story.key
    summary = jira_issue.new_story.summary
  }
}

