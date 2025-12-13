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
var _ datasource.DataSource = &ProjectDataSource{}

// NewProjectDataSource creates a new project data source.
func NewProjectDataSource() datasource.DataSource {
	return &ProjectDataSource{}
}

// ProjectDataSource defines the data source implementation.
type ProjectDataSource struct {
	client *client.JiraClient
}

// ProjectDataSourceModel describes the data source data model.
type ProjectDataSourceModel struct {
	Key  types.String `tfsdk:"key"`
	ID   types.String `tfsdk:"id"`
	Name types.String `tfsdk:"name"`
}

// Metadata returns the data source type name.
func (d *ProjectDataSource) Metadata(ctx context.Context, req datasource.MetadataRequest, resp *datasource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_project"
}

// Schema defines the schema for the data source.
func (d *ProjectDataSource) Schema(ctx context.Context, req datasource.SchemaRequest, resp *datasource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Description: "Fetches a Jira project by key.",
		MarkdownDescription: `
Fetches a Jira project by its key.

## Example Usage

` + "```hcl" + `
data "jira_project" "main" {
  key = "PROJ"
}

output "project_name" {
  value = data.jira_project.main.name
}
` + "```" + `
`,
		Attributes: map[string]schema.Attribute{
			"key": schema.StringAttribute{
				Description: "The project key (e.g., PROJ).",
				Required:    true,
			},
			"id": schema.StringAttribute{
				Description: "The project ID.",
				Computed:    true,
			},
			"name": schema.StringAttribute{
				Description: "The project name.",
				Computed:    true,
			},
		},
	}
}

// Configure adds the provider configured client to the data source.
func (d *ProjectDataSource) Configure(ctx context.Context, req datasource.ConfigureRequest, resp *datasource.ConfigureResponse) {
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
func (d *ProjectDataSource) Read(ctx context.Context, req datasource.ReadRequest, resp *datasource.ReadResponse) {
	var data ProjectDataSourceModel
	resp.Diagnostics.Append(req.Config.Get(ctx, &data)...)
	if resp.Diagnostics.HasError() {
		return
	}

	tflog.Debug(ctx, "Reading Jira project", map[string]any{
		"key": data.Key.ValueString(),
	})

	project, err := d.client.GetProject(data.Key.ValueString())
	if err != nil {
		resp.Diagnostics.AddError("Failed to read project", err.Error())
		return
	}

	data.ID = types.StringValue(project.ID)
	data.Name = types.StringValue(project.Name)

	resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}

