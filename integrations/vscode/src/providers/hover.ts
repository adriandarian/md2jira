/**
 * Hover provider for spectra
 *
 * Shows tracker issue details when hovering over story/epic IDs.
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';

interface TrackerIssueDetails {
    id: string;
    title: string;
    status: string;
    assignee?: string;
    priority?: string;
    storyPoints?: number;
    labels?: string[];
    created?: string;
    updated?: string;
    description?: string;
    url?: string;
}

// Cache for issue details to avoid repeated CLI calls
const issueCache = new Map<string, { details: TrackerIssueDetails; timestamp: number }>();
const CACHE_TTL_MS = 60000; // 1 minute cache

export class SpectraHoverProvider implements vscode.HoverProvider {
    private executable: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('spectra');
        this.executable = config.get<string>('executable') || 'spectra';
    }

    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        _token: vscode.CancellationToken
    ): Promise<vscode.Hover | undefined> {
        const config = vscode.workspace.getConfiguration('spectra');
        if (!config.get<boolean>('showHoverPreviews', true)) {
            return undefined;
        }

        const line = document.lineAt(position.line).text;

        // Find issue ID at cursor position
        const issueId = this.findIssueIdAtPosition(line, position.character);
        if (!issueId) {
            return undefined;
        }

        // Get issue details (from cache or CLI)
        const details = await this.getIssueDetails(issueId);
        if (!details) {
            return this.createBasicHover(issueId, line);
        }

        return this.createDetailedHover(details);
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

    private async getIssueDetails(issueId: string): Promise<TrackerIssueDetails | undefined> {
        // Check cache
        const cached = issueCache.get(issueId);
        if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
            return cached.details;
        }

        try {
            const details = await this.fetchIssueFromCLI(issueId);
            if (details) {
                issueCache.set(issueId, { details, timestamp: Date.now() });
            }
            return details;
        } catch {
            return undefined;
        }
    }

    private fetchIssueFromCLI(issueId: string): Promise<TrackerIssueDetails | undefined> {
        return new Promise((resolve) => {
            const cmd = `${this.executable} issue get ${issueId} --format json`;

            cp.exec(cmd, { timeout: 5000 }, (error: Error | null, stdout: string) => {
                if (error) {
                    resolve(undefined);
                    return;
                }

                try {
                    const data = JSON.parse(stdout);
                    resolve({
                        id: data.id || issueId,
                        title: data.title || data.summary || 'Unknown',
                        status: data.status || 'Unknown',
                        assignee: data.assignee?.name || data.assignee,
                        priority: data.priority,
                        storyPoints: data.story_points || data.storyPoints,
                        labels: data.labels,
                        created: data.created,
                        updated: data.updated,
                        description: data.description,
                        url: data.url,
                    });
                } catch {
                    resolve(undefined);
                }
            });
        });
    }

    private createBasicHover(issueId: string, line: string): vscode.Hover {
        const config = vscode.workspace.getConfiguration('spectra');
        const trackerUrl = config.get<string>('jiraUrl') || config.get<string>('trackerUrl');

        // Try to extract title from the line
        const titleMatch = line.match(new RegExp(`${issueId}:\\s*(.+?)(?:\\s*$|\\s*\\|)`));
        const title = titleMatch ? titleMatch[1].trim() : '';

        const markdown = new vscode.MarkdownString();
        markdown.isTrusted = true;
        markdown.supportHtml = true;

        markdown.appendMarkdown(`### 📋 ${issueId}\n\n`);

        if (title) {
            markdown.appendMarkdown(`**${title}**\n\n`);
        }

        if (trackerUrl) {
            const url = `${trackerUrl}/browse/${issueId}`;
            markdown.appendMarkdown(`[🔗 Open in Tracker](${url})\n\n`);
        }

        markdown.appendMarkdown(`---\n`);
        markdown.appendMarkdown(`*Hover details not available. Configure tracker connection for full details.*`);

        return new vscode.Hover(markdown);
    }

    private createDetailedHover(details: TrackerIssueDetails): vscode.Hover {
        const markdown = new vscode.MarkdownString();
        markdown.isTrusted = true;
        markdown.supportHtml = true;

        // Header with ID and title
        markdown.appendMarkdown(`### ${this.getStatusEmoji(details.status)} ${details.id}\n\n`);
        markdown.appendMarkdown(`**${details.title}**\n\n`);

        // Status badge
        markdown.appendMarkdown(`---\n\n`);

        // Details table
        const tableRows: string[] = [];

        tableRows.push(`| **Status** | ${this.formatStatus(details.status)} |`);

        if (details.priority) {
            tableRows.push(`| **Priority** | ${this.formatPriority(details.priority)} |`);
        }

        if (details.assignee) {
            tableRows.push(`| **Assignee** | 👤 ${details.assignee} |`);
        }

        if (details.storyPoints !== undefined) {
            tableRows.push(`| **Story Points** | 🎯 ${details.storyPoints} |`);
        }

        if (details.labels && details.labels.length > 0) {
            const labelStr = details.labels.map(l => `\`${l}\``).join(' ');
            tableRows.push(`| **Labels** | ${labelStr} |`);
        }

        if (details.updated) {
            const date = new Date(details.updated).toLocaleDateString();
            tableRows.push(`| **Updated** | 📅 ${date} |`);
        }

        markdown.appendMarkdown(`| | |\n|---|---|\n`);
        markdown.appendMarkdown(tableRows.join('\n') + '\n\n');

        // Description preview
        if (details.description) {
            const preview = details.description.substring(0, 200);
            const truncated = details.description.length > 200 ? '...' : '';
            markdown.appendMarkdown(`---\n\n`);
            markdown.appendMarkdown(`**Description:**\n\n`);
            markdown.appendMarkdown(`> ${preview}${truncated}\n\n`);
        }

        // Actions
        markdown.appendMarkdown(`---\n\n`);

        if (details.url) {
            markdown.appendMarkdown(`[🔗 Open in Tracker](${details.url}) | `);
        }

        markdown.appendMarkdown(`[📋 Copy ID](command:spectra.copyStoryIdArg?${encodeURIComponent(JSON.stringify(details.id))}) | `);
        markdown.appendMarkdown(`[🔄 Refresh](command:spectra.refreshIssueCache?${encodeURIComponent(JSON.stringify(details.id))})`);

        return new vscode.Hover(markdown);
    }

    private getStatusEmoji(status: string): string {
        const statusLower = status.toLowerCase();
        if (statusLower.includes('done') || statusLower.includes('closed') || statusLower.includes('complete')) {
            return '✅';
        }
        if (statusLower.includes('progress') || statusLower.includes('active') || statusLower.includes('started')) {
            return '🔄';
        }
        if (statusLower.includes('blocked') || statusLower.includes('hold')) {
            return '⏸️';
        }
        if (statusLower.includes('review')) {
            return '👀';
        }
        if (statusLower.includes('todo') || statusLower.includes('open') || statusLower.includes('backlog')) {
            return '📋';
        }
        return '📋';
    }

    private formatStatus(status: string): string {
        const emoji = this.getStatusEmoji(status);
        return `${emoji} ${status}`;
    }

    private formatPriority(priority: string): string {
        const priorityLower = priority.toLowerCase();
        if (priorityLower.includes('critical') || priorityLower.includes('highest')) {
            return `🔴 ${priority}`;
        }
        if (priorityLower.includes('high')) {
            return `🟠 ${priority}`;
        }
        if (priorityLower.includes('medium') || priorityLower.includes('normal')) {
            return `🟡 ${priority}`;
        }
        if (priorityLower.includes('low')) {
            return `🟢 ${priority}`;
        }
        return priority;
    }
}

/**
 * Clear the issue cache (called when refreshing)
 */
export function clearIssueCache(issueId?: string): void {
    if (issueId) {
        issueCache.delete(issueId);
    } else {
        issueCache.clear();
    }
}
