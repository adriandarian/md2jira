// Copyright (c) md2jira
// SPDX-License-Identifier: MIT

package provider

import (
	"context"
	"fmt"
	"strings"

	"github.com/hashicorp/terraform-plugin-framework/path"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/planmodifier"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/stringplanmodifier"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"github.com/hashicorp/terraform-plugin-log/tflog"
	"github.com/md2jira/terraform-provider-jira/internal/client"
)

// Ensure provider defined types fully satisfy framework interfaces.
var _ resource.Resource = &IssueResource{}
var _ resource.ResourceWithImportState = &IssueResource{}

// NewIssueResource creates a new issue resource.
func NewIssueResource() resource.Resource {
	return &IssueResource{}
}

// IssueResource defines the resource implementation.
type IssueResource struct {
	client *client.JiraClient
}

// IssueResourceModel describes the resource data model.
type IssueResourceModel struct {
	ID          types.String `tfsdk:"id"`
	Key         types.String `tfsdk:"key"`
	Project     types.String `tfsdk:"project"`
	Summary     types.String `tfsdk:"summary"`
	Description types.String `tfsdk:"description"`
	IssueType   types.String `tfsdk:"issue_type"`
	Priority    types.String `tfsdk:"priority"`
	Status      types.String `tfsdk:"status"`
	Labels      types.List   `tfsdk:"labels"`
	ParentKey   types.String `tfsdk:"parent_key"`
}

// Metadata returns the resource type name.
func (r *IssueResource) Metadata(ctx context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_issue"
}

// Schema defines the schema for the resource.
func (r *IssueResource) Schema(ctx context.Context, req resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Description: "Manages a Jira issue (Story, Bug, Task, Epic, etc.).",
		MarkdownDescription: `
Manages a Jira issue. This resource can create, read, update, and delete Jira issues.

## Example Usage

### Create a Story

` + "```hcl" + `
resource "jira_issue" "user_login" {
  project     = "PROJ"
  summary     = "US-001: User Login"
  description = "As a user, I want to login so that I can access my account."
  issue_type  = "Story"
  priority    = "Medium"
  labels      = ["sprint-1", "auth"]
}
` + "```" + `

### Create an Epic

` + "```hcl" + `
resource "jira_issue" "auth_epic" {
  project     = "PROJ"
  summary     = "Authentication System"
  description = "Epic for all authentication-related features"
  issue_type  = "Epic"
}

resource "jira_issue" "story_in_epic" {
  project     = "PROJ"
  summary     = "Login Feature"
  description = "Implement user login"
  issue_type  = "Story"
  parent_key  = jira_issue.auth_epic.key
}
` + "```" + `

## Import

Issues can be imported using the issue key:

` + "```bash" + `
terraform import jira_issue.example PROJ-123
` + "```" + `
`,
		Attributes: map[string]schema.Attribute{
			"id": schema.StringAttribute{
				Description: "The Jira issue ID.",
				Computed:    true,
				PlanModifiers: []planmodifier.String{
					stringplanmodifier.UseStateForUnknown(),
				},
			},
			"key": schema.StringAttribute{
				Description: "The Jira issue key (e.g., PROJ-123).",
				Computed:    true,
				PlanModifiers: []planmodifier.String{
					stringplanmodifier.UseStateForUnknown(),
				},
			},
			"project": schema.StringAttribute{
				Description: "The project key (e.g., PROJ).",
				Required:    true,
				PlanModifiers: []planmodifier.String{
					stringplanmodifier.RequiresReplace(),
				},
			},
			"summary": schema.StringAttribute{
				Description: "The issue summary/title.",
				Required:    true,
			},
			"description": schema.StringAttribute{
				Description: "The issue description (plain text, will be converted to ADF).",
				Optional:    true,
			},
			"issue_type": schema.StringAttribute{
				Description: "The issue type (Story, Bug, Task, Epic, etc.).",
				Required:    true,
				PlanModifiers: []planmodifier.String{
					stringplanmodifier.RequiresReplace(),
				},
			},
			"priority": schema.StringAttribute{
				Description: "The issue priority (Highest, High, Medium, Low, Lowest).",
				Optional:    true,
			},
			"status": schema.StringAttribute{
				Description: "The issue status (read-only, set via transitions).",
				Computed:    true,
			},
			"labels": schema.ListAttribute{
				Description: "Issue labels.",
				Optional:    true,
				ElementType: types.StringType,
			},
			"parent_key": schema.StringAttribute{
				Description: "Parent issue key (for stories in epics or subtasks).",
				Optional:    true,
			},
		},
	}
}

// Configure adds the provider configured client to the resource.
func (r *IssueResource) Configure(ctx context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
	if req.ProviderData == nil {
		return
	}

	client, ok := req.ProviderData.(*client.JiraClient)
	if !ok {
		resp.Diagnostics.AddError(
			"Unexpected Resource Configure Type",
			fmt.Sprintf("Expected *client.JiraClient, got: %T", req.ProviderData),
		)
		return
	}

	r.client = client
}

// Create creates the resource and sets the initial Terraform state.
func (r *IssueResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	var data IssueResourceModel
	resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Creating Jira issue", map[string]any{
		"project":    data.Project.ValueString(),
		"summary":    data.Summary.ValueString(),
		"issue_type": data.IssueType.ValueString(),
	})

	// Build the issue fields
	fields := client.IssueFields{
		Project:   &client.Project{Key: data.Project.ValueString()},
		Summary:   data.Summary.ValueString(),
		IssueType: &client.IssueType{Name: data.IssueType.ValueString()},
	}

	// Add optional fields
	if !data.Description.IsNull() {
		fields.Description = client.TextToADF(data.Description.ValueString())
	}

	if !data.Priority.IsNull() {
		fields.Priority = &client.Priority{Name: data.Priority.ValueString()}
	}

	if !data.ParentKey.IsNull() {
		fields.Parent = &client.Parent{Key: data.ParentKey.ValueString()}
	}

	// Add labels
	if !data.Labels.IsNull() {
		var labels []string
		resp.Diagnostics.Append(data.Labels.ElementsAs(ctx, &labels, false)...)
		if resp.Diagnostics.HasError() {
			return
		}
		fields.Labels = labels
	}

	// Create the issue
	issue, err := r.client.CreateIssue(&client.CreateIssueRequest{Fields: fields})
	if err != nil {
		resp.Diagnostics.AddError("Failed to create issue", err.Error())
		return
	}

	// Fetch the created issue to get all fields
	createdIssue, err := r.client.GetIssue(issue.Key)
	if err != nil {
		resp.Diagnostics.AddError("Failed to read created issue", err.Error())
		return
	}

	// Update state
	data.ID = types.StringValue(createdIssue.ID)
	data.Key = types.StringValue(createdIssue.Key)
	if createdIssue.Fields.Status != nil {
		data.Status = types.StringValue(createdIssue.Fields.Status.Name)
	}

	tflog.Info(ctx, "Created Jira issue", map[string]any{
		"key": createdIssue.Key,
	})

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

// Read refreshes the Terraform state with the latest data.
func (r *IssueResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
	var data IssueResourceModel
	resp.Diagnostics.Append(req.State.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Reading Jira issue", map[string]any{
		"key": data.Key.ValueString(),
	})

	issue, err := r.client.GetIssue(data.Key.ValueString())
	if err != nil {
		// Check if issue was deleted
		if strings.Contains(err.Error(), "404") {
			resp.State.RemoveResource(ctx)
			return
		}
		resp.Diagnostics.AddError("Failed to read issue", err.Error())
		return
	}

	// Update state from API response
	data.ID = types.StringValue(issue.ID)
	data.Key = types.StringValue(issue.Key)
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

	// Handle labels
	if len(issue.Fields.Labels) > 0 {
		labels, diags := types.ListValueFrom(ctx, types.StringType, issue.Fields.Labels)
		resp.Diagnostics.Append(diags...)
		data.Labels = labels
	} else {
		data.Labels = types.ListNull(types.StringType)
	}

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

// Update updates the resource and sets the updated Terraform state on success.
func (r *IssueResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	var data IssueResourceModel
	resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Updating Jira issue", map[string]any{
		"key": data.Key.ValueString(),
	})

	// Build update fields
	fields := client.IssueFields{
		Summary: data.Summary.ValueString(),
	}

	if !data.Description.IsNull() {
		fields.Description = client.TextToADF(data.Description.ValueString())
	}

	if !data.Priority.IsNull() {
		fields.Priority = &client.Priority{Name: data.Priority.ValueString()}
	}

	// Handle labels
	if !data.Labels.IsNull() {
		var labels []string
		resp.Diagnostics.Append(data.Labels.ElementsAs(ctx, &labels, false)...)
		if resp.Diagnostics.HasError() {
			return
		}
		fields.Labels = labels
	}

	// Update the issue
	err := r.client.UpdateIssue(data.Key.ValueString(), &client.UpdateIssueRequest{Fields: fields})
	if err != nil {
		resp.Diagnostics.AddError("Failed to update issue", err.Error())
		return
	}

	// Fetch updated issue
	issue, err := r.client.GetIssue(data.Key.ValueString())
	if err != nil {
		resp.Diagnostics.AddError("Failed to read updated issue", err.Error())
		return
	}

	if issue.Fields.Status != nil {
		data.Status = types.StringValue(issue.Fields.Status.Name)
	}

	tflog.Info(ctx, "Updated Jira issue", map[string]any{
		"key": data.Key.ValueString(),
	})

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

// Delete deletes the resource and removes the Terraform state on success.
func (r *IssueResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	var data IssueResourceModel
	resp.Diagnostics.Append(req.State.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Deleting Jira issue", map[string]any{
		"key": data.Key.ValueString(),
	})

	err := r.client.DeleteIssue(data.Key.ValueString())
	if err != nil {
		// Ignore 404 errors (already deleted)
		if !strings.Contains(err.Error(), "404") {
			resp.Diagnostics.AddError("Failed to delete issue", err.Error())
			return
		}
	}

	tflog.Info(ctx, "Deleted Jira issue", map[string]any{
		"key": data.Key.ValueString(),
	})
}

// ImportState imports the resource into Terraform state.
func (r *IssueResource) ImportState(ctx context.Context, req resource.ImportStateRequest, resp *resource.ImportStateResponse) {
	resource.ImportStatePassthroughID(ctx, path.Root("key"), req, resp)
}

