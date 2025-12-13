// Copyright (c) md2jira
// SPDX-License-Identifier: MIT

package provider

import (
	"context"
	"fmt"

	"github.com/hashicorp/terraform-plugin-framework/datasource"
	"github.com/hashicorp/terraform-plugin-framework/datasource/schema"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"github.com/hashicorp/terraform-plugin-log/tflog"
	"github.com/md2jira/terraform-provider-jira/internal/client"
)

// Ensure provider defined types fully satisfy framework interfaces.
var _ datasource.DataSource = &IssueDataSource{}

// NewIssueDataSource creates a new issue data source.
func NewIssueDataSource() datasource.DataSource {
	return &IssueDataSource{}
}

// IssueDataSource defines the data source implementation.
type IssueDataSource struct {
	client *client.JiraClient
}

// IssueDataSourceModel describes the data source data model.
type IssueDataSourceModel struct {
	Key         types.String `tfsdk:"key"`
	ID          types.String `tfsdk:"id"`
	Project     types.String `tfsdk:"project"`
	Summary     types.String `tfsdk:"summary"`
	Description types.String `tfsdk:"description"`
	IssueType   types.String `tfsdk:"issue_type"`
	Status      types.String `tfsdk:"status"`
	Priority    types.String `tfsdk:"priority"`
	ParentKey   types.String `tfsdk:"parent_key"`
	Labels      types.List   `tfsdk:"labels"`
}

// Metadata returns the data source type name.
func (d *IssueDataSource) Metadata(ctx context.Context, req datasource.MetadataRequest, resp *datasource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_issue"
}

// Schema defines the schema for the data source.
func (d *IssueDataSource) Schema(ctx context.Context, req datasource.SchemaRequest, resp *datasource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Description: "Fetches a Jira issue by key.",
		MarkdownDescription: `
Fetches a Jira issue by its key.

## Example Usage

` + "```hcl" + `
data "jira_issue" "existing" {
  key = "PROJ-123"
}

output "issue_summary" {
  value = data.jira_issue.existing.summary
}

# Create a subtask under an existing issue
resource "jira_subtask" "new_task" {
  project    = data.jira_issue.existing.project
  parent_key = data.jira_issue.existing.key
  summary    = "Additional task"
}
` + "```" + `
`,
		Attributes: map[string]schema.Attribute{
			"key": schema.StringAttribute{
				Description: "The Jira issue key (e.g., PROJ-123).",
				Required:    true,
			},
			"id": schema.StringAttribute{
				Description: "The Jira issue ID.",
				Computed:    true,
			},
			"project": schema.StringAttribute{
				Description: "The project key.",
				Computed:    true,
			},
			"summary": schema.StringAttribute{
				Description: "The issue summary/title.",
				Computed:    true,
			},
			"description": schema.StringAttribute{
				Description: "The issue description (plain text).",
				Computed:    true,
			},
			"issue_type": schema.StringAttribute{
				Description: "The issue type.",
				Computed:    true,
			},
			"status": schema.StringAttribute{
				Description: "The issue status.",
				Computed:    true,
			},
			"priority": schema.StringAttribute{
				Description: "The issue priority.",
				Computed:    true,
			},
			"parent_key": schema.StringAttribute{
				Description: "Parent issue key (if this is a subtask or story in an epic).",
				Computed:    true,
			},
			"labels": schema.ListAttribute{
				Description: "Issue labels.",
				Computed:    true,
				ElementType: types.StringType,
			},
		},
	}
}

// Configure adds the provider configured client to the data source.
func (d *IssueDataSource) Configure(ctx context.Context, req datasource.ConfigureRequest, resp *datasource.ConfigureResponse) {
	if req.ProviderData == nil {
		return
	}

	client, ok := req.ProviderData.(*client.JiraClient)
	if !ok {
		resp.Diagnostics.AddError(
			"Unexpected Data Source Configure Type",
			fmt.Sprintf("Expected *client.JiraClient, got: %T", req.ProviderData),
		)
		return
	}

	d.client = client
}

// Read refreshes the Terraform state with the latest data.
func (d *IssueDataSource) Read(ctx context.Context, req datasource.ReadRequest, resp *datasource.ReadResponse) {
	var data IssueDataSourceModel
	resp.Diagnostics.Append(req.Config.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Reading Jira issue", map[string]any{
		"key": data.Key.ValueString(),
	})

	issue, err := d.client.GetIssue(data.Key.ValueString())
	if err != nil {
		resp.Diagnostics.AddError("Failed to read issue", err.Error())
		return
	}

	// Populate data from API response
	data.ID = types.StringValue(issue.ID)
	data.Summary = types.StringValue(issue.Fields.Summary)

	if issue.Fields.Description != nil {
		data.Description = types.StringValue(client.ADFToText(issue.Fields.Description))
	} else {
		data.Description = types.StringNull()
	}

	if issue.Fields.Project != nil {
		data.Project = types.StringValue(issue.Fields.Project.Key)
	}

	if issue.Fields.IssueType != nil {
		data.IssueType = types.StringValue(issue.Fields.IssueType.Name)
	}

	if issue.Fields.Status != nil {
		data.Status = types.StringValue(issue.Fields.Status.Name)
	}

	if issue.Fields.Priority != nil {
		data.Priority = types.StringValue(issue.Fields.Priority.Name)
	}

	if issue.Fields.Parent != nil {
		data.ParentKey = types.StringValue(issue.Fields.Parent.Key)
	} else {
		data.ParentKey = types.StringNull()
	}

	if len(issue.Fields.Labels) > 0 {
		labels, diags := types.ListValueFrom(ctx, types.StringType, issue.Fields.Labels)
		resp.Diagnostics.Append(diags...)
		data.Labels = labels
	} else {
		data.Labels = types.ListNull(types.StringType)
	}

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

