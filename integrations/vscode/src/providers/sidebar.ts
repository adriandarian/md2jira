/**
 * Sidebar Panel Provider for spectra
 *
 * Shows sync status, recent changes, and story overview in a sidebar panel.
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';

// Types
interface SyncStatus {
    lastSync?: string;
    lastSyncStatus?: 'success' | 'failed' | 'partial';
    pendingChanges: number;
    syncedStories: number;
    unsyncedStories: number;
}

interface RecentChange {
    id: string;
    title: string;
    changeType: 'created' | 'updated' | 'synced' | 'deleted';
    timestamp: string;
    file?: string;
}

interface StoryItem {
    id: string;
    title: string;
    status?: string;
    storyPoints?: number;
    line: number;
    file: string;
    synced: boolean;
}

// Tree item types
type SidebarItem = StatusTreeItem | RecentChangeTreeItem | StoryTreeItem | SectionHeaderItem;

/**
 * Sidebar Tree Data Provider
 */
export class SpectraSidebarProvider implements vscode.TreeDataProvider<SidebarItem>, vscode.Disposable {
    private _onDidChangeTreeData = new vscode.EventEmitter<SidebarItem | undefined | null | void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private syncStatus: SyncStatus = {
        pendingChanges: 0,
        syncedStories: 0,
        unsyncedStories: 0,
    };
    private recentChanges: RecentChange[] = [];
    private stories: StoryItem[] = [];
    private disposables: vscode.Disposable[] = [];
    private executable: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('spectra');
        this.executable = config.get<string>('executable') || 'spectra';

        // Auto-refresh on file changes
        this.disposables.push(
            vscode.window.onDidChangeActiveTextEditor(() => this.refresh()),
            vscode.workspace.onDidSaveTextDocument(() => this.refresh()),
            vscode.workspace.onDidChangeTextDocument(() => this.debouncedRefresh())
        );

        // Initial load
        this.refresh();
    }

    private refreshTimeout: ReturnType<typeof setTimeout> | undefined;
    private debouncedRefresh(): void {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }
        this.refreshTimeout = setTimeout(() => this.refresh(), 500);
    }

    async refresh(): Promise<void> {
        await this.loadData();
        this._onDidChangeTreeData.fire();
    }

    private async loadData(): Promise<void> {
        const editor = vscode.window.activeTextEditor;

        // Load stories from current file
        if (editor?.document.languageId === 'markdown') {
            this.stories = this.parseStories(editor.document);
        } else {
            this.stories = [];
        }

        // Try to load sync status from CLI
        await this.loadSyncStatus();

        // Load recent changes
        await this.loadRecentChanges();
    }

    private async loadSyncStatus(): Promise<void> {
        try {
            const result = await this.runCommand(['status', '--format', 'json']);
            if (result.code === 0 && result.stdout) {
                const data = JSON.parse(result.stdout);
                this.syncStatus = {
                    lastSync: data.last_sync,
                    lastSyncStatus: data.status,
                    pendingChanges: data.pending_changes || 0,
                    syncedStories: data.synced_stories || this.stories.filter(s => s.synced).length,
                    unsyncedStories: data.unsynced_stories || this.stories.filter(s => !s.synced).length,
                };
            }
        } catch {
            // Use local data
            this.syncStatus = {
                pendingChanges: this.stories.filter(s => !s.synced).length,
                syncedStories: this.stories.filter(s => s.synced).length,
                unsyncedStories: this.stories.filter(s => !s.synced).length,
            };
        }
    }

    private async loadRecentChanges(): Promise<void> {
        try {
            const result = await this.runCommand(['history', '--limit', '5', '--format', 'json']);
            if (result.code === 0 && result.stdout) {
                const data = JSON.parse(result.stdout);
                this.recentChanges = (data.changes || []).map((c: Record<string, unknown>) => ({
                    id: c.id as string,
                    title: c.title as string,
                    changeType: c.type as 'created' | 'updated' | 'synced' | 'deleted',
                    timestamp: c.timestamp as string,
                    file: c.file as string | undefined,
                }));
            }
        } catch {
            this.recentChanges = [];
        }
    }

    private parseStories(document: vscode.TextDocument): StoryItem[] {
        const stories: StoryItem[] = [];
        const text = document.getText();
        const lines = text.split('\n');

        const storyPattern = /^###\s+([📋✅🔄⏸️]*)\s*([A-Z]+-\d+)?:?\s*(.+)/;

        for (let i = 0; i < lines.length; i++) {
            const match = lines[i].match(storyPattern);
            if (match) {
                const emoji = match[1] || '';
                const id = match[2] || `US-${i + 1}`;
                const title = match[3]?.trim() || 'Untitled';

                let status: string | undefined;
                if (emoji.includes('✅')) status = 'done';
                else if (emoji.includes('🔄')) status = 'in_progress';
                else if (emoji.includes('⏸️')) status = 'blocked';

                // Check if synced (has a real ID)
                const synced = !!match[2] && match[2].match(/^[A-Z]+-\d+$/) !== null;

                stories.push({
                    id,
                    title,
                    status,
                    line: i + 1,
                    file: document.uri.fsPath,
                    synced,
                });
            }
        }

        return stories;
    }

    private runCommand(args: string[]): Promise<{ code: number; stdout: string; stderr: string }> {
        return new Promise((resolve) => {
            const cmd = [this.executable, ...args].join(' ');
            cp.exec(cmd, { timeout: 5000 }, (error: Error | null, stdout: string, stderr: string) => {
                resolve({
                    code: error ? 1 : 0,
                    stdout: stdout || '',
                    stderr: stderr || '',
                });
            });
        });
    }

    getTreeItem(element: SidebarItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: SidebarItem): SidebarItem[] {
        if (!element) {
            // Root level - return sections
            return [
                new SectionHeaderItem('sync-status', 'Sync Status', true),
                new SectionHeaderItem('stories', `Stories (${this.stories.length})`, true),
                new SectionHeaderItem('recent-changes', 'Recent Changes', this.recentChanges.length > 0),
            ];
        }

        // Section children
        if (element instanceof SectionHeaderItem) {
            switch (element.sectionId) {
                case 'sync-status':
                    return this.getSyncStatusItems();
                case 'stories':
                    return this.getStoryItems();
                case 'recent-changes':
                    return this.getRecentChangeItems();
            }
        }

        return [];
    }

    private getSyncStatusItems(): SidebarItem[] {
        const items: SidebarItem[] = [];

        // Last sync
        if (this.syncStatus.lastSync) {
            const date = new Date(this.syncStatus.lastSync);
            const statusIcon = this.syncStatus.lastSyncStatus === 'success' ? '✅' :
                              this.syncStatus.lastSyncStatus === 'failed' ? '❌' : '⚠️';
            items.push(new StatusTreeItem(
                `${statusIcon} Last sync: ${date.toLocaleString()}`,
                this.syncStatus.lastSyncStatus || 'unknown'
            ));
        } else {
            items.push(new StatusTreeItem('📋 No sync history', 'none'));
        }

        // Counts
        items.push(new StatusTreeItem(
            `🔗 Synced: ${this.syncStatus.syncedStories}`,
            'info'
        ));

        if (this.syncStatus.unsyncedStories > 0) {
            items.push(new StatusTreeItem(
                `📝 Unsynced: ${this.syncStatus.unsyncedStories}`,
                'warning'
            ));
        }

        if (this.syncStatus.pendingChanges > 0) {
            items.push(new StatusTreeItem(
                `⏳ Pending changes: ${this.syncStatus.pendingChanges}`,
                'info'
            ));
        }

        return items;
    }

    private getStoryItems(): SidebarItem[] {
        if (this.stories.length === 0) {
            return [new StatusTreeItem('No stories in current file', 'none')];
        }

        return this.stories.map(story => new StoryTreeItem(story));
    }

    private getRecentChangeItems(): SidebarItem[] {
        if (this.recentChanges.length === 0) {
            return [new StatusTreeItem('No recent changes', 'none')];
        }

        return this.recentChanges.map(change => new RecentChangeTreeItem(change));
    }

    dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this._onDidChangeTreeData.dispose();
    }
}

/**
 * Section Header Item
 */
class SectionHeaderItem extends vscode.TreeItem {
    constructor(
        public readonly sectionId: string,
        label: string,
        hasContent: boolean
    ) {
        super(label, hasContent ? vscode.TreeItemCollapsibleState.Expanded : vscode.TreeItemCollapsibleState.None);

        // Icons
        switch (sectionId) {
            case 'sync-status':
                this.iconPath = new vscode.ThemeIcon('sync');
                break;
            case 'stories':
                this.iconPath = new vscode.ThemeIcon('list-unordered');
                break;
            case 'recent-changes':
                this.iconPath = new vscode.ThemeIcon('history');
                break;
        }
    }
}

/**
 * Status Tree Item
 */
class StatusTreeItem extends vscode.TreeItem {
    constructor(label: string, status: string) {
        super(label, vscode.TreeItemCollapsibleState.None);

        switch (status) {
            case 'success':
                this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('terminal.ansiGreen'));
                break;
            case 'failed':
                this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('terminal.ansiRed'));
                break;
            case 'warning':
                this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('terminal.ansiYellow'));
                break;
            case 'info':
                this.iconPath = new vscode.ThemeIcon('info');
                break;
            default:
                this.iconPath = new vscode.ThemeIcon('circle-outline');
        }
    }
}

/**
 * Story Tree Item
 */
class StoryTreeItem extends vscode.TreeItem {
    constructor(story: StoryItem) {
        super(story.id, vscode.TreeItemCollapsibleState.None);

        this.description = story.title;
        this.tooltip = `${story.id}: ${story.title}\nStatus: ${story.status || 'unknown'}\nLine: ${story.line}`;

        // Icon based on status
        switch (story.status) {
            case 'done':
                this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('terminal.ansiGreen'));
                break;
            case 'in_progress':
                this.iconPath = new vscode.ThemeIcon('sync', new vscode.ThemeColor('terminal.ansiBlue'));
                break;
            case 'blocked':
                this.iconPath = new vscode.ThemeIcon('circle-slash', new vscode.ThemeColor('terminal.ansiRed'));
                break;
            default:
                this.iconPath = story.synced ?
                    new vscode.ThemeIcon('circle-filled') :
                    new vscode.ThemeIcon('circle-outline');
        }

        // Command to jump to story
        this.command = {
            command: 'vscode.open',
            title: 'Go to Story',
            arguments: [
                vscode.Uri.file(story.file),
                { selection: new vscode.Range(story.line - 1, 0, story.line - 1, 0) }
            ]
        };
    }
}

/**
 * Recent Change Tree Item
 */
class RecentChangeTreeItem extends vscode.TreeItem {
    constructor(change: RecentChange) {
        super(change.id, vscode.TreeItemCollapsibleState.None);

        const date = new Date(change.timestamp);
        const timeAgo = this.getTimeAgo(date);

        this.description = `${change.title} • ${timeAgo}`;
        this.tooltip = `${change.id}: ${change.title}\nType: ${change.changeType}\nTime: ${date.toLocaleString()}`;

        // Icon based on change type
        switch (change.changeType) {
            case 'created':
                this.iconPath = new vscode.ThemeIcon('add', new vscode.ThemeColor('terminal.ansiGreen'));
                break;
            case 'updated':
                this.iconPath = new vscode.ThemeIcon('edit', new vscode.ThemeColor('terminal.ansiBlue'));
                break;
            case 'synced':
                this.iconPath = new vscode.ThemeIcon('cloud-upload', new vscode.ThemeColor('terminal.ansiCyan'));
                break;
            case 'deleted':
                this.iconPath = new vscode.ThemeIcon('trash', new vscode.ThemeColor('terminal.ansiRed'));
                break;
        }

        // Command to open file if available
        if (change.file) {
            this.command = {
                command: 'vscode.open',
                title: 'Open File',
                arguments: [vscode.Uri.file(change.file)]
            };
        }
    }

    private getTimeAgo(date: Date): string {
        const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

        return date.toLocaleDateString();
    }
}

/**
 * Webview Panel for full dashboard
 */
export class SpectraDashboardPanel {
    public static currentPanel: SpectraDashboardPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;

        this._update();

        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.onDidChangeViewState(() => {
            if (this._panel.visible) {
                this._update();
            }
        }, null, this._disposables);
    }

    public static createOrShow(extensionUri: vscode.Uri): void {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        if (SpectraDashboardPanel.currentPanel) {
            SpectraDashboardPanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'spectraDashboard',
            'Spectra Dashboard',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
            }
        );

        SpectraDashboardPanel.currentPanel = new SpectraDashboardPanel(panel, extensionUri);
    }

    private _update(): void {
        this._panel.webview.html = this._getHtmlContent();
    }

    private _getHtmlContent(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spectra Dashboard</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
        }
        h1 { color: var(--vscode-titleBar-activeForeground); }
        .card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
        }
        .stat {
            text-align: center;
            padding: 12px;
            background: var(--vscode-editor-background);
            border-radius: 4px;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
        .stat-label {
            color: var(--vscode-descriptionForeground);
        }
        button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 8px;
        }
        button:hover {
            background: var(--vscode-button-hoverBackground);
        }
    </style>
</head>
<body>
    <h1>📊 Spectra Dashboard</h1>

    <div class="card">
        <h2>Quick Actions</h2>
        <button onclick="sync()">🔄 Sync (Dry Run)</button>
        <button onclick="validate()">✅ Validate</button>
        <button onclick="refresh()">🔃 Refresh</button>
    </div>

    <div class="card">
        <h2>Sync Status</h2>
        <div class="status-grid">
            <div class="stat">
                <div class="stat-value" id="synced-count">-</div>
                <div class="stat-label">Synced</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="pending-count">-</div>
                <div class="stat-label">Pending</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="total-count">-</div>
                <div class="stat-label">Total Stories</div>
            </div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function sync() {
            vscode.postMessage({ command: 'sync' });
        }
        function validate() {
            vscode.postMessage({ command: 'validate' });
        }
        function refresh() {
            vscode.postMessage({ command: 'refresh' });
        }
    </script>
</body>
</html>`;
    }

    public dispose(): void {
        SpectraDashboardPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}
