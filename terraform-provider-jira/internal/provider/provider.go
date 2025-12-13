// Copyright (c) md2jira
// SPDX-License-Identifier: MIT

package provider

import (
	"context"
	"os"

	"github.com/hashicorp/terraform-plugin-framework/datasource"
	"github.com/hashicorp/terraform-plugin-framework/path"
	"github.com/hashicorp/terraform-plugin-framework/provider"
	"github.com/hashicorp/terraform-plugin-framework/provider/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"github.com/hashicorp/terraform-plugin-log/tflog"
	"github.com/md2jira/terraform-provider-jira/internal/client"
)

// Ensure JiraProvider satisfies various provider interfaces.
var _ provider.Provider = &JiraProvider{}

// JiraProvider defines the provider implementation.
type JiraProvider struct {
	// version is set to the provider version on release.
	version string
}

// JiraProviderModel describes the provider data model.
type JiraProviderModel struct {
	URL      types.String `tfsdk:"url"`
	Email    types.String `tfsdk:"email"`
	APIToken types.String `tfsdk:"api_token"`
}

// New creates a new provider instance.
func New(version string) func() provider.Provider {
	return func() provider.Provider {
		return &JiraProvider{
			version: version,
		}
	}
}

// Metadata returns the provider type name.
func (p *JiraProvider) Metadata(ctx context.Context, req provider.MetadataRequest, resp *provider.MetadataResponse) {
	resp.TypeName = "jira"
	resp.Version = p.version
}

// Schema defines the provider-level schema for configuration data.
func (p *JiraProvider) Schema(ctx context.Context, req provider.SchemaRequest, resp *provider.SchemaResponse) {
	resp.Schema = schema.Schema{
		Description: "Terraform provider for managing Jira issues, epics, and subtasks as infrastructure-as-code.",
		MarkdownDescription: `
# Jira Provider

The Jira provider allows you to manage Jira issues, epics, and subtasks using Terraform.

## Example Usage

` + "```hcl" + `
provider "jira" {
  url       = "https://your-company.atlassian.net"
  email     = "your-email@company.com"
  api_token = var.jira_api_token
}

resource "jira_issue" "example" {
  project     = "PROJ"
  summary     = "Example story created by Terraform"
  description = "This issue was created using the Jira Terraform provider"
  issue_type  = "Story"
}
` + "```" + `

## Authentication

The provider requires Jira Cloud API credentials:
- **url**: Your Jira Cloud instance URL
- **email**: Your Atlassian account email
- **api_token**: API token from https://id.atlassian.com/manage-profile/security/api-tokens

These can also be set via environment variables:
- ` + "`JIRA_URL`" + `
- ` + "`JIRA_EMAIL`" + `
- ` + "`JIRA_API_TOKEN`" + `
`,
		Attributes: map[string]schema.Attribute{
			"url": schema.StringAttribute{
				Description: "Jira Cloud instance URL (e.g., https://company.atlassian.net). Can also be set via JIRA_URL environment variable.",
				Optional:    true,
			},
			"email": schema.StringAttribute{
				Description: "Jira account email. Can also be set via JIRA_EMAIL environment variable.",
				Optional:    true,
			},
			"api_token": schema.StringAttribute{
				Description: "Jira API token. Can also be set via JIRA_API_TOKEN environment variable.",
				Optional:    true,
				Sensitive:   true,
			},
		},
	}
}

// Configure prepares a Jira API client for data sources and resources.
func (p *JiraProvider) Configure(ctx context.Context, req provider.ConfigureRequest, resp *provider.ConfigureResponse) {
	tflog.Info(ctx, "Configuring Jira client")

	var config JiraProviderModel
	diags := req.Config.Get(ctx, &config)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	// Get configuration from environment or config
	url := os.Getenv("JIRA_URL")
	if !config.URL.IsNull() {
		url = config.URL.ValueString()
	}

	email := os.Getenv("JIRA_EMAIL")
	if !config.Email.IsNull() {
		email = config.Email.ValueString()
	}

	apiToken := os.Getenv("JIRA_API_TOKEN")
	if !config.APIToken.IsNull() {
		apiToken = config.APIToken.ValueString()
	}

	// Validate configuration
	if url == "" {
		resp.Diagnostics.AddAttributeError(
			path.Root("url"),
			"Missing Jira URL",
			"The provider requires a Jira URL to be set in the configuration or via the JIRA_URL environment variable.",
		)
	}

	if email == "" {
		resp.Diagnostics.AddAttributeError(
			path.Root("email"),
			"Missing Jira Email",
			"The provider requires a Jira email to be set in the configuration or via the JIRA_EMAIL environment variable.",
		)
	}

	if apiToken == "" {
		resp.Diagnostics.AddAttributeError(
			path.Root("api_token"),
			"Missing Jira API Token",
			"The provider requires a Jira API token to be set in the configuration or via the JIRA_API_TOKEN environment variable.",
		)
	}

	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Creating Jira client", map[string]any{
		"url":   url,
		"email": email,
	})

	// Create the Jira client
	jiraClient, err := client.NewJiraClient(url, email, apiToken)
	if err != nil {
		resp.Diagnostics.AddError(
			"Unable to Create Jira Client",
			"An error occurred when creating the Jira API client: "+err.Error(),
		)
		return
	}

	// Make the client available to data sources and resources
	resp.DataSourceData = jiraClient
	resp.ResourceData = jiraClient

	tflog.Info(ctx, "Configured Jira client", map[string]any{"url": url})
}

// Resources defines the resources implemented in the provider.
func (p *JiraProvider) Resources(ctx context.Context) []func() resource.Resource {
	return []func() resource.Resource{
		NewIssueResource,
		NewSubtaskResource,
	}
}

// DataSources defines the data sources implemented in the provider.
func (p *JiraProvider) DataSources(ctx context.Context) []func() datasource.DataSource {
	return []func() datasource.DataSource{
		NewIssueDataSource,
		NewProjectDataSource,
	}
}

