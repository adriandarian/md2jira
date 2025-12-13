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
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/int64planmodifier"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/planmodifier"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/stringplanmodifier"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"github.com/hashicorp/terraform-plugin-log/tflog"
	"github.com/md2jira/terraform-provider-jira/internal/client"
)

// Ensure provider defined types fully satisfy framework interfaces.
var _ resource.Resource = &SubtaskResource{}
var _ resource.ResourceWithImportState = &SubtaskResource{}

// NewSubtaskResource creates a new subtask resource.
func NewSubtaskResource() resource.Resource {
	return &SubtaskResource{}
}

// SubtaskResource defines the resource implementation.
type SubtaskResource struct {
	client *client.JiraClient
}

// SubtaskResourceModel describes the resource data model.
type SubtaskResourceModel struct {
	ID          types.String `tfsdk:"id"`
	Key         types.String `tfsdk:"key"`
	Project     types.String `tfsdk:"project"`
	ParentKey   types.String `tfsdk:"parent_key"`
	Summary     types.String `tfsdk:"summary"`
	Description types.String `tfsdk:"description"`
	StoryPoints types.Int64  `tfsdk:"story_points"`
	Status      types.String `tfsdk:"status"`
}

// Metadata returns the resource type name.
func (r *SubtaskResource) Metadata(ctx context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_subtask"
}

// Schema defines the schema for the resource.
func (r *SubtaskResource) Schema(ctx context.Context, req resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Description: "Manages a Jira subtask under a parent issue.",
		MarkdownDescription: `
Manages a Jira subtask. Subtasks are child issues under a parent Story, Bug, or Task.

## Example Usage

` + "```hcl" + `
resource "jira_issue" "user_story" {
  project     = "PROJ"
  summary     = "User Login Feature"
  description = "Implement user login functionality"
  issue_type  = "Story"
}

resource "jira_subtask" "backend" {
  project     = "PROJ"
  parent_key  = jira_issue.user_story.key
  summary     = "Implement login API"
  description = "Create REST endpoint for authentication"
  story_points = 3
}

resource "jira_subtask" "frontend" {
  project     = "PROJ"
  parent_key  = jira_issue.user_story.key
  summary     = "Create login form"
  description = "Build React login component"
  story_points = 2
}

resource "jira_subtask" "tests" {
  project     = "PROJ"
  parent_key  = jira_issue.user_story.key
  summary     = "Write tests"
  description = "Unit and integration tests for login"
  story_points = 2
}
` + "```" + `

## Import

Subtasks can be imported using the issue key:

` + "```bash" + `
terraform import jira_subtask.example PROJ-456
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
				Description: "The Jira issue key (e.g., PROJ-456).",
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
			"parent_key": schema.StringAttribute{
				Description: "The parent issue key (e.g., PROJ-123).",
				Required:    true,
				PlanModifiers: []planmodifier.String{
					stringplanmodifier.RequiresReplace(),
				},
			},
			"summary": schema.StringAttribute{
				Description: "The subtask summary/title.",
				Required:    true,
			},
			"description": schema.StringAttribute{
				Description: "The subtask description.",
				Optional:    true,
			},
			"story_points": schema.Int64Attribute{
				Description: "Story points estimate.",
				Optional:    true,
				PlanModifiers: []planmodifier.Int64{
					int64planmodifier.UseStateForUnknown(),
				},
			},
			"status": schema.StringAttribute{
				Description: "The subtask status (read-only).",
				Computed:    true,
			},
		},
	}
}

// Configure adds the provider configured client to the resource.
func (r *SubtaskResource) Configure(ctx context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
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
func (r *SubtaskResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	var data SubtaskResourceModel
	resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Creating Jira subtask", map[string]any{
		"project":    data.Project.ValueString(),
		"parent_key": data.ParentKey.ValueString(),
		"summary":    data.Summary.ValueString(),
	})

	// Build the issue fields
	fields := client.IssueFields{
		Project:   &client.Project{Key: data.Project.ValueString()},
		Parent:    &client.Parent{Key: data.ParentKey.ValueString()},
		Summary:   data.Summary.ValueString(),
		IssueType: &client.IssueType{Name: "Sub-task"},
	}

	if !data.Description.IsNull() {
		fields.Description = client.TextToADF(data.Description.ValueString())
	}

	// Create the subtask
	issue, err := r.client.CreateIssue(&client.CreateIssueRequest{Fields: fields})
	if err != nil {
		resp.Diagnostics.AddError("Failed to create subtask", err.Error())
		return
	}

	// Fetch the created issue
	createdIssue, err := r.client.GetIssue(issue.Key)
	if err != nil {
		resp.Diagnostics.AddError("Failed to read created subtask", err.Error())
		return
	}

	// Update state
	data.ID = types.StringValue(createdIssue.ID)
	data.Key = types.StringValue(createdIssue.Key)
	if createdIssue.Fields.Status != nil {
		data.Status = types.StringValue(createdIssue.Fields.Status.Name)
	}

	tflog.Info(ctx, "Created Jira subtask", map[string]any{
		"key":        createdIssue.Key,
		"parent_key": data.ParentKey.ValueString(),
	})

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

// Read refreshes the Terraform state with the latest data.
func (r *SubtaskResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
	var data SubtaskResourceModel
	resp.Diagnostics.Append(req.State.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Reading Jira subtask", map[string]any{
		"key": data.Key.ValueString(),
	})

	issue, err := r.client.GetIssue(data.Key.ValueString())
	if err != nil {
		if strings.Contains(err.Error(), "404") {
			resp.State.RemoveResource(ctx)
			return
		}
		resp.Diagnostics.AddError("Failed to read subtask", err.Error())
		return
	}

	// Update state
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

	if issue.Fields.Status != nil {
		data.Status = types.StringValue(issue.Fields.Status.Name)
	}

	if issue.Fields.Parent != nil {
		data.ParentKey = types.StringValue(issue.Fields.Parent.Key)
	}

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

// Update updates the resource.
func (r *SubtaskResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	var data SubtaskResourceModel
	resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Updating Jira subtask", map[string]any{
		"key": data.Key.ValueString(),
	})

	fields := client.IssueFields{
		Summary: data.Summary.ValueString(),
	}

	if !data.Description.IsNull() {
		fields.Description = client.TextToADF(data.Description.ValueString())
	}

	err := r.client.UpdateIssue(data.Key.ValueString(), &client.UpdateIssueRequest{Fields: fields})
	if err != nil {
		resp.Diagnostics.AddError("Failed to update subtask", err.Error())
		return
	}

	// Fetch updated issue
	issue, err := r.client.GetIssue(data.Key.ValueString())
	if err != nil {
		resp.Diagnostics.AddError("Failed to read updated subtask", err.Error())
		return
	}

	if issue.Fields.Status != nil {
		data.Status = types.StringValue(issue.Fields.Status.Name)
	}

	tflog.Info(ctx, "Updated Jira subtask", map[string]any{
		"key": data.Key.ValueString(),
	})

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

// Delete deletes the resource.
func (r *SubtaskResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	var data SubtaskResourceModel
	resp.Diagnostics.Append(req.State.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Deleting Jira subtask", map[string]any{
		"key": data.Key.ValueString(),
	})

	err := r.client.DeleteIssue(data.Key.ValueString())
	if err != nil {
		if !strings.Contains(err.Error(), "404") {
			resp.Diagnostics.AddError("Failed to delete subtask", err.Error())
			return
		}
	}

	tflog.Info(ctx, "Deleted Jira subtask", map[string]any{
		"key": data.Key.ValueString(),
	})
}

// ImportState imports the resource.
func (r *SubtaskResource) ImportState(ctx context.Context, req resource.ImportStateRequest, resp *resource.ImportStateResponse) {
	resource.ImportStatePassthroughID(ctx, path.Root("key"), req, resp)
}

