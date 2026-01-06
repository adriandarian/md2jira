/**
 * Definition provider for spectra
 *
 * Enables Cmd+Click on issue IDs to open them in the browser.
 */

import * as vscode from 'vscode';

export class SpectraDefinitionProvider implements vscode.DefinitionProvider {
    provideDefinition(
        document: vscode.TextDocument,
        position: vscode.Position,
        _token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.Definition | vscode.LocationLink[]> {
        const config = vscode.workspace.getConfiguration('spectra');
        if (!config.get<boolean>('enableGoToTracker', true)) {
            return undefined;
        }

        const line = document.lineAt(position.line).text;

        // Find issue ID at cursor position
        const issueId = this.findIssueIdAtPosition(line, position.character);
        if (!issueId) {
            return undefined;
        }

        // Get tracker URL
        const trackerUrl = config.get<string>('jiraUrl') || config.get<string>('trackerUrl');
        if (!trackerUrl) {
            // Show message to configure tracker URL
            vscode.window.showInformationMessage(
                `Configure tracker URL in settings to enable Cmd+Click for ${issueId}`,
                'Open Settings'
            ).then((selection: string | undefined) => {
                if (selection === 'Open Settings') {
                    vscode.commands.executeCommand(
                        'workbench.action.openSettings',
                        'spectra.jiraUrl'
                    );
                }
            });
            return undefined;
        }

        // Open the issue in the browser
        const issueUrl = this.buildIssueUrl(trackerUrl, issueId);
        vscode.env.openExternal(vscode.Uri.parse(issueUrl));

        // Return undefined to not navigate in the editor
        // The browser open is the "definition"
        return undefined;
    }

    private findIssueIdAtPosition(line: string, character: number): string | undefined {
        // Pattern for issue IDs (PROJ-123 format)
        const issuePattern = /[A-Z][A-Z0-9]*-\d+/g;
        let match;

        while ((match = issuePattern.exec(line)) !== null) {
            const start = match.index;
            const end = start + match[0].length;

            if (character >= start && character <= end) {
                return match[0];
            }
        }

        return undefined;
    }

    private buildIssueUrl(baseUrl: string, issueId: string): string {
        // Remove trailing slash
        const url = baseUrl.replace(/\/$/, '');

        // Detect tracker type and build appropriate URL
        if (url.includes('atlassian.net') || url.includes('jira')) {
            return `${url}/browse/${issueId}`;
        }
        if (url.includes('github.com')) {
            // GitHub issues: https://github.com/owner/repo/issues/123
            // For GitHub, issue ID might be REPO-123 or just 123
            const issueNum = issueId.replace(/[A-Z]+-/, '');
            return `${url}/issues/${issueNum}`;
        }
        if (url.includes('gitlab')) {
            // GitLab issues
            const issueNum = issueId.replace(/[A-Z]+-/, '');
            return `${url}/-/issues/${issueNum}`;
        }
        if (url.includes('linear.app')) {
            // Linear: https://linear.app/team/issue/TEAM-123
            return `${url}/issue/${issueId}`;
        }
        if (url.includes('shortcut.com') || url.includes('clubhouse.io')) {
            // Shortcut (formerly Clubhouse)
            const storyNum = issueId.replace(/[A-Z]+-/, '');
            return `${url}/story/${storyNum}`;
        }
        if (url.includes('youtrack')) {
            // YouTrack
            return `${url}/issue/${issueId}`;
        }
        if (url.includes('azure') || url.includes('dev.azure.com')) {
            // Azure DevOps
            const workItemId = issueId.replace(/[A-Z]+-/, '');
            return `${url}/_workitems/edit/${workItemId}`;
        }
        if (url.includes('trello.com')) {
            // Trello - needs card ID
            return `${url}/c/${issueId}`;
        }
        if (url.includes('asana.com')) {
            // Asana
            const taskId = issueId.replace(/[A-Z]+-/, '');
            return `${url}/0/0/${taskId}`;
        }
        if (url.includes('monday.com')) {
            // Monday.com
            const pulseId = issueId.replace(/[A-Z]+-/, '');
            return `${url}/boards/pulse/${pulseId}`;
        }
        if (url.includes('clickup.com')) {
            // ClickUp
            const taskId = issueId.replace(/[A-Z]+-/, '');
            return `${url}/t/${taskId}`;
        }
        if (url.includes('notion.so')) {
            // Notion
            return `${url}/${issueId}`;
        }
        if (url.includes('plane.so') || url.includes('plane')) {
            // Plane
            return `${url}/issues/${issueId}`;
        }
        if (url.includes('pivotaltracker.com')) {
            // Pivotal Tracker
            const storyId = issueId.replace(/[A-Z]+-/, '');
            return `${url}/story/show/${storyId}`;
        }
        if (url.includes('basecamp.com')) {
            // Basecamp
            return `${url}/todos/${issueId}`;
        }

        // Default: assume Jira-like browse URL
        return `${url}/browse/${issueId}`;
    }
}

/**
 * Document link provider for clickable issue IDs
 *
 * Makes issue IDs in the document clickable links.
 */
export class SpectraDocumentLinkProvider implements vscode.DocumentLinkProvider {
    provideDocumentLinks(
        document: vscode.TextDocument,
        _token: vscode.CancellationToken
    ): vscode.DocumentLink[] | undefined {
        const config = vscode.workspace.getConfiguration('spectra');
        if (!config.get<boolean>('enableGoToTracker', true)) {
            return undefined;
        }

        const trackerUrl = config.get<string>('jiraUrl') || config.get<string>('trackerUrl');
        if (!trackerUrl) {
            return undefined;
        }

        const links: vscode.DocumentLink[] = [];
        const text = document.getText();
        const issuePattern = /[A-Z][A-Z0-9]*-\d+/g;
        let match;

        while ((match = issuePattern.exec(text)) !== null) {
            const startPos = document.positionAt(match.index);
            const endPos = document.positionAt(match.index + match[0].length);
            const range = new vscode.Range(startPos, endPos);

            const issueUrl = this.buildIssueUrl(trackerUrl, match[0]);
            const link = new vscode.DocumentLink(range, vscode.Uri.parse(issueUrl));
            link.tooltip = `Open ${match[0]} in tracker`;

            links.push(link);
        }

        return links;
    }

    private buildIssueUrl(baseUrl: string, issueId: string): string {
        const url = baseUrl.replace(/\/$/, '');

        // Same logic as definition provider
        if (url.includes('atlassian.net') || url.includes('jira')) {
            return `${url}/browse/${issueId}`;
        }
        if (url.includes('linear.app')) {
            return `${url}/issue/${issueId}`;
        }
        if (url.includes('youtrack')) {
            return `${url}/issue/${issueId}`;
        }

        // Default
        return `${url}/browse/${issueId}`;
    }
}
