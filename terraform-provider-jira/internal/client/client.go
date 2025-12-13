// Copyright (c) md2jira
// SPDX-License-Identifier: MIT

package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// JiraClient is the HTTP client for Jira API.
type JiraClient struct {
	BaseURL    string
	Email      string
	APIToken   string
	HTTPClient *http.Client
}

// Issue represents a Jira issue.
type Issue struct {
	ID          string                 `json:"id,omitempty"`
	Key         string                 `json:"key,omitempty"`
	Self        string                 `json:"self,omitempty"`
	Fields      IssueFields            `json:"fields"`
	Transitions []Transition           `json:"transitions,omitempty"`
}

// IssueFields contains the fields of a Jira issue.
type IssueFields struct {
	Summary     string      `json:"summary,omitempty"`
	Description interface{} `json:"description,omitempty"`
	Project     *Project    `json:"project,omitempty"`
	IssueType   *IssueType  `json:"issuetype,omitempty"`
	Status      *Status     `json:"status,omitempty"`
	Priority    *Priority   `json:"priority,omitempty"`
	Parent      *Parent     `json:"parent,omitempty"`
	Assignee    *User       `json:"assignee,omitempty"`
	Reporter    *User       `json:"reporter,omitempty"`
	Labels      []string    `json:"labels,omitempty"`
	// Custom fields can be added as needed
}

// Project represents a Jira project.
type Project struct {
	ID   string `json:"id,omitempty"`
	Key  string `json:"key,omitempty"`
	Name string `json:"name,omitempty"`
	Self string `json:"self,omitempty"`
}

// IssueType represents a Jira issue type.
type IssueType struct {
	ID   string `json:"id,omitempty"`
	Name string `json:"name,omitempty"`
	Self string `json:"self,omitempty"`
}

// Status represents a Jira status.
type Status struct {
	ID   string `json:"id,omitempty"`
	Name string `json:"name,omitempty"`
	Self string `json:"self,omitempty"`
}

// Priority represents a Jira priority.
type Priority struct {
	ID   string `json:"id,omitempty"`
	Name string `json:"name,omitempty"`
	Self string `json:"self,omitempty"`
}

// Parent represents a parent issue (for subtasks).
type Parent struct {
	ID  string `json:"id,omitempty"`
	Key string `json:"key,omitempty"`
}

// User represents a Jira user.
type User struct {
	AccountID    string `json:"accountId,omitempty"`
	DisplayName  string `json:"displayName,omitempty"`
	EmailAddress string `json:"emailAddress,omitempty"`
	Self         string `json:"self,omitempty"`
}

// Transition represents a workflow transition.
type Transition struct {
	ID   string `json:"id,omitempty"`
	Name string `json:"name,omitempty"`
	To   Status `json:"to,omitempty"`
}

// CreateIssueRequest is the request body for creating an issue.
type CreateIssueRequest struct {
	Fields IssueFields `json:"fields"`
}

// UpdateIssueRequest is the request body for updating an issue.
type UpdateIssueRequest struct {
	Fields IssueFields `json:"fields"`
}

// TransitionRequest is the request body for transitioning an issue.
type TransitionRequest struct {
	Transition TransitionID `json:"transition"`
}

// TransitionID identifies a transition.
type TransitionID struct {
	ID string `json:"id"`
}

// SearchResult is the response from a JQL search.
type SearchResult struct {
	StartAt    int     `json:"startAt"`
	MaxResults int     `json:"maxResults"`
	Total      int     `json:"total"`
	Issues     []Issue `json:"issues"`
}

// ErrorResponse represents a Jira API error.
type ErrorResponse struct {
	ErrorMessages []string          `json:"errorMessages,omitempty"`
	Errors        map[string]string `json:"errors,omitempty"`
}

func (e *ErrorResponse) Error() string {
	var parts []string
	parts = append(parts, e.ErrorMessages...)
	for field, msg := range e.Errors {
		parts = append(parts, fmt.Sprintf("%s: %s", field, msg))
	}
	return strings.Join(parts, "; ")
}

// NewJiraClient creates a new Jira API client.
func NewJiraClient(baseURL, email, apiToken string) (*JiraClient, error) {
	// Normalize URL
	baseURL = strings.TrimSuffix(baseURL, "/")
	if !strings.HasSuffix(baseURL, "/rest/api/3") {
		baseURL = baseURL + "/rest/api/3"
	}

	return &JiraClient{
		BaseURL:  baseURL,
		Email:    email,
		APIToken: apiToken,
		HTTPClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}, nil
}

// doRequest performs an HTTP request to the Jira API.
func (c *JiraClient) doRequest(method, endpoint string, body interface{}) ([]byte, error) {
	url := c.BaseURL + endpoint

	var reqBody io.Reader
	if body != nil {
		jsonBytes, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonBytes)
	}

	req, err := http.NewRequest(method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.SetBasicAuth(c.Email, c.APIToken)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	if resp.StatusCode >= 400 {
		var errResp ErrorResponse
		if json.Unmarshal(respBody, &errResp) == nil && (len(errResp.ErrorMessages) > 0 || len(errResp.Errors) > 0) {
			return nil, fmt.Errorf("API error (%d): %s", resp.StatusCode, errResp.Error())
		}
		return nil, fmt.Errorf("API error (%d): %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}

// GetIssue retrieves an issue by key.
func (c *JiraClient) GetIssue(key string) (*Issue, error) {
	body, err := c.doRequest("GET", "/issue/"+key, nil)
	if err != nil {
		return nil, err
	}

	var issue Issue
	if err := json.Unmarshal(body, &issue); err != nil {
		return nil, fmt.Errorf("failed to parse issue: %w", err)
	}

	return &issue, nil
}

// CreateIssue creates a new issue.
func (c *JiraClient) CreateIssue(req *CreateIssueRequest) (*Issue, error) {
	body, err := c.doRequest("POST", "/issue", req)
	if err != nil {
		return nil, err
	}

	var issue Issue
	if err := json.Unmarshal(body, &issue); err != nil {
		return nil, fmt.Errorf("failed to parse created issue: %w", err)
	}

	return &issue, nil
}

// UpdateIssue updates an existing issue.
func (c *JiraClient) UpdateIssue(key string, req *UpdateIssueRequest) error {
	_, err := c.doRequest("PUT", "/issue/"+key, req)
	return err
}

// DeleteIssue deletes an issue.
func (c *JiraClient) DeleteIssue(key string) error {
	_, err := c.doRequest("DELETE", "/issue/"+key, nil)
	return err
}

// GetTransitions retrieves available transitions for an issue.
func (c *JiraClient) GetTransitions(key string) ([]Transition, error) {
	body, err := c.doRequest("GET", "/issue/"+key+"/transitions", nil)
	if err != nil {
		return nil, err
	}

	var result struct {
		Transitions []Transition `json:"transitions"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse transitions: %w", err)
	}

	return result.Transitions, nil
}

// TransitionIssue transitions an issue to a new status.
func (c *JiraClient) TransitionIssue(key string, transitionID string) error {
	req := TransitionRequest{
		Transition: TransitionID{ID: transitionID},
	}
	_, err := c.doRequest("POST", "/issue/"+key+"/transitions", req)
	return err
}

// SearchIssues searches for issues using JQL.
func (c *JiraClient) SearchIssues(jql string, maxResults int) (*SearchResult, error) {
	body := map[string]interface{}{
		"jql":        jql,
		"maxResults": maxResults,
		"fields":     []string{"summary", "description", "status", "issuetype", "project", "priority", "parent", "labels"},
	}

	respBody, err := c.doRequest("POST", "/search", body)
	if err != nil {
		return nil, err
	}

	var result SearchResult
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse search results: %w", err)
	}

	return &result, nil
}

// GetProject retrieves a project by key.
func (c *JiraClient) GetProject(key string) (*Project, error) {
	body, err := c.doRequest("GET", "/project/"+key, nil)
	if err != nil {
		return nil, err
	}

	var project Project
	if err := json.Unmarshal(body, &project); err != nil {
		return nil, fmt.Errorf("failed to parse project: %w", err)
	}

	return &project, nil
}

// GetCurrentUser retrieves the authenticated user.
func (c *JiraClient) GetCurrentUser() (*User, error) {
	body, err := c.doRequest("GET", "/myself", nil)
	if err != nil {
		return nil, err
	}

	var user User
	if err := json.Unmarshal(body, &user); err != nil {
		return nil, fmt.Errorf("failed to parse user: %w", err)
	}

	return &user, nil
}

// TextToADF converts plain text to Atlassian Document Format.
func TextToADF(text string) map[string]interface{} {
	if text == "" {
		return nil
	}

	// Split text into paragraphs
	paragraphs := strings.Split(text, "\n\n")
	content := make([]map[string]interface{}, 0, len(paragraphs))

	for _, para := range paragraphs {
		if strings.TrimSpace(para) == "" {
			continue
		}

		// Handle single newlines within paragraphs
		lines := strings.Split(para, "\n")
		textContent := make([]map[string]interface{}, 0)

		for i, line := range lines {
			if i > 0 {
				textContent = append(textContent, map[string]interface{}{
					"type": "hardBreak",
				})
			}
			if line != "" {
				textContent = append(textContent, map[string]interface{}{
					"type": "text",
					"text": line,
				})
			}
		}

		content = append(content, map[string]interface{}{
			"type":    "paragraph",
			"content": textContent,
		})
	}

	return map[string]interface{}{
		"type":    "doc",
		"version": 1,
		"content": content,
	}
}

// ADFToText converts Atlassian Document Format to plain text.
func ADFToText(adf interface{}) string {
	if adf == nil {
		return ""
	}

	doc, ok := adf.(map[string]interface{})
	if !ok {
		// If it's already a string, return it
		if str, ok := adf.(string); ok {
			return str
		}
		return ""
	}

	content, ok := doc["content"].([]interface{})
	if !ok {
		return ""
	}

	var result strings.Builder
	for i, item := range content {
		if i > 0 {
			result.WriteString("\n\n")
		}
		result.WriteString(extractText(item))
	}

	return result.String()
}

func extractText(node interface{}) string {
	nodeMap, ok := node.(map[string]interface{})
	if !ok {
		return ""
	}

	nodeType, _ := nodeMap["type"].(string)

	switch nodeType {
	case "text":
		text, _ := nodeMap["text"].(string)
		return text
	case "hardBreak":
		return "\n"
	default:
		// Recursively extract text from content
		content, ok := nodeMap["content"].([]interface{})
		if !ok {
			return ""
		}

		var result strings.Builder
		for _, item := range content {
			result.WriteString(extractText(item))
		}
		return result.String()
	}
}

