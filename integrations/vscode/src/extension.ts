/**
 * spectra VS Code Extension
 *
 * Provides integration with spectra CLI for syncing markdown with issue trackers.
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

// Providers
import { StoryCodeLensProvider } from './providers/codeLens';
import { StoryDecorationProvider } from './providers/decorations';
import { StoryTreeDataProvider } from './providers/treeView';
import { DiagnosticsProvider } from './providers/diagnostics';
import { SpectraCodeActionProvider } from './providers/codeActions';
import { SpectraHoverProvider, clearIssueCache } from './providers/hover';
import { SpectraDefinitionProvider, SpectraDocumentLinkProvider } from './providers/definition';
import { SpectraSidebarProvider, SpectraDashboardPanel } from './providers/sidebar';

// Types
interface Story {
    id: string;
    title: string;
    line: number;
    status?: string;
    points?: number;
}

interface Epic {
    id: string;
    title: string;
    line: number;
}

interface SpectraResult {
    code: number;
    stdout: string;
    stderr: string;
}

// Extension state
let statusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;
let diagnosticsProvider: DiagnosticsProvider;
let sidebarProvider: SpectraSidebarProvider;

/**
 * Extension activation
 */
export function activate(context: vscode.ExtensionContext) {
    console.log('spectra extension activated');

    // Create output channel
    outputChannel = vscode.window.createOutputChannel('spectra');

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.command = 'spectra.gotoStory';
    context.subscriptions.push(statusBarItem);

    // Create diagnostics provider
    diagnosticsProvider = new DiagnosticsProvider();
    context.subscriptions.push(diagnosticsProvider);

    // Create sidebar provider
    sidebarProvider = new SpectraSidebarProvider();
    context.subscriptions.push(sidebarProvider);
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('spectraSidebar', sidebarProvider)
    );

    // Register commands
    registerCommands(context);

    // Register providers
    registerProviders(context);

    // Register event handlers
    registerEventHandlers(context);

    // Update status bar for current editor
    updateStatusBar();
}

/**
 * Extension deactivation
 */
export function deactivate() {
    console.log('spectra extension deactivated');
}

/**
 * Register all commands
 */
function registerCommands(context: vscode.ExtensionContext) {
    // Validate command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.validate', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'markdown') {
                vscode.window.showWarningMessage('Open a markdown file to validate');
                return;
            }

            await runValidate(editor.document);
        })
    );

    // Sync (dry-run) command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.sync', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'markdown') {
                vscode.window.showWarningMessage('Open a markdown file to sync');
                return;
            }

            const epic = await getEpicKey(editor.document);
            if (!epic) return;

            await runSync(editor.document, epic, false);
        })
    );

    // Sync (execute) command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.syncExecute', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'markdown') {
                vscode.window.showWarningMessage('Open a markdown file to sync');
                return;
            }

            const epic = await getEpicKey(editor.document);
            if (!epic) return;

            const confirm = await vscode.window.showWarningMessage(
                `Sync to ${epic}? This will make changes in Jira.`,
                'Yes, Execute',
                'Cancel'
            );

            if (confirm === 'Yes, Execute') {
                await runSync(editor.document, epic, true);
            }
        })
    );

    // Dashboard command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.dashboard', async () => {
            const editor = vscode.window.activeTextEditor;
            const args = ['--dashboard'];

            if (editor?.document.languageId === 'markdown') {
                args.push('--markdown', editor.document.uri.fsPath);
                const epic = detectEpic(editor.document);
                if (epic) {
                    args.push('--epic', epic);
                }
            }

            const result = await runSpectra(args);
            showResultPanel('spectra Dashboard', result.stdout);
        })
    );

    // Init command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.init', async () => {
            const terminal = vscode.window.createTerminal('spectra init');
            terminal.show();
            terminal.sendText(getExecutable() + ' --init');
        })
    );

    // Generate command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.generate', async () => {
            const epicKey = await vscode.window.showInputBox({
                prompt: 'Enter Jira Epic Key',
                placeHolder: 'PROJ-123'
            });

            if (!epicKey) return;

            const result = await runSpectra(['--generate', '--epic', epicKey]);
            if (result.code === 0) {
                vscode.window.showInformationMessage('Template generated successfully');
                showResultPanel('Generated Template', result.stdout);
            } else {
                vscode.window.showErrorMessage('Failed to generate template');
                outputChannel.append(result.stderr);
            }
        })
    );

    // Go to story command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.gotoStory', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'markdown') {
                return;
            }

            const stories = parseStories(editor.document);
            if (stories.length === 0) {
                vscode.window.showInformationMessage('No stories found in this file');
                return;
            }

            const items = stories.map(s => ({
                label: s.id,
                description: s.title,
                detail: s.status ? `Status: ${s.status}` : undefined,
                story: s
            }));

            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select a story to jump to'
            });

            if (selected) {
                const position = new vscode.Position(selected.story.line - 1, 0);
                editor.selection = new vscode.Selection(position, position);
                editor.revealRange(
                    new vscode.Range(position, position),
                    vscode.TextEditorRevealType.InCenter
                );
            }
        })
    );

    // Copy story ID command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.copyStoryId', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const story = getStoryAtLine(editor.document, editor.selection.active.line);
            if (story) {
                await vscode.env.clipboard.writeText(story.id);
                vscode.window.showInformationMessage(`Copied: ${story.id}`);
            }
        })
    );

    // Open in Jira command
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.openInJira', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const config = vscode.workspace.getConfiguration('spectra');
            const trackerUrl = config.get<string>('trackerUrl') || config.get<string>('jiraUrl');

            if (!trackerUrl) {
                const url = await vscode.window.showInputBox({
                    prompt: 'Enter your tracker URL',
                    placeHolder: 'https://your-org.atlassian.net'
                });
                if (url) {
                    await config.update('trackerUrl', url, vscode.ConfigurationTarget.Global);
                }
                return;
            }

            const story = getStoryAtLine(editor.document, editor.selection.active.line);
            if (story) {
                const issueUrl = buildTrackerUrl(trackerUrl, story.id);
                vscode.env.openExternal(vscode.Uri.parse(issueUrl));
            }
        })
    );

    // Copy story ID with argument (for hover links)
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.copyStoryIdArg', async (storyId: string) => {
            await vscode.env.clipboard.writeText(storyId);
            vscode.window.showInformationMessage(`Copied: ${storyId}`);
        })
    );

    // Open epic in tracker
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.openEpicInTracker', async (epicId: string) => {
            const config = vscode.workspace.getConfiguration('spectra');
            const trackerUrl = config.get<string>('trackerUrl') || config.get<string>('jiraUrl');

            if (!trackerUrl) {
                vscode.window.showWarningMessage('Configure tracker URL in settings');
                return;
            }

            const issueUrl = buildTrackerUrl(trackerUrl, epicId);
            vscode.env.openExternal(vscode.Uri.parse(issueUrl));
        })
    );

    // Create story in tracker
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.createStoryInTracker', async (
            title: string,
            line: number,
            type: 'epic' | 'story' | 'subtask'
        ) => {
            const config = vscode.workspace.getConfiguration('spectra');
            const projectKey = config.get<string>('projectKey');

            if (!projectKey) {
                const key = await vscode.window.showInputBox({
                    prompt: 'Enter project key',
                    placeHolder: 'PROJ'
                });
                if (key) {
                    await config.update('projectKey', key, vscode.ConfigurationTarget.Global);
                }
                return;
            }

            // Run spectra CLI to create the issue
            const args = ['issue', 'create', '--type', type, '--title', title, '--project', projectKey];

            const result = await runSpectra(args);
            if (result.code === 0) {
                // Parse the created issue ID from output
                const match = result.stdout.match(/([A-Z]+-\d+)/);
                if (match) {
                    const issueId = match[1];

                    // Update the markdown file with the new ID
                    const editor = vscode.window.activeTextEditor;
                    if (editor) {
                        const lineText = editor.document.lineAt(line).text;
                        let newLineText: string;

                        if (type === 'epic') {
                            newLineText = lineText.replace(/^(#\s+)/, `$1🚀 ${issueId}: `);
                        } else if (type === 'subtask') {
                            newLineText = lineText.replace(/^(####\s+)/, `$1${issueId}: `);
                        } else {
                            newLineText = lineText.replace(/^(###\s+)/, `$1📋 ${issueId}: `);
                        }

                        await editor.edit(editBuilder => {
                            const lineRange = editor.document.lineAt(line).range;
                            editBuilder.replace(lineRange, newLineText);
                        });

                        vscode.window.showInformationMessage(`Created ${issueId} in tracker`);
                    }
                }
            } else {
                vscode.window.showErrorMessage(`Failed to create ${type}: ${result.stderr}`);
            }
        })
    );

    // Generate story ID locally
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.generateStoryId', async (line: number) => {
            const config = vscode.workspace.getConfiguration('spectra');
            const projectKey = config.get<string>('projectKey') || 'US';

            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            // Find the next available story number
            const stories = parseStories(editor.document);
            let maxNum = 0;
            for (const story of stories) {
                const match = story.id.match(/\d+$/);
                if (match) {
                    const num = parseInt(match[0], 10);
                    if (num > maxNum) maxNum = num;
                }
            }

            const newId = `${projectKey}-${String(maxNum + 1).padStart(3, '0')}`;
            const lineText = editor.document.lineAt(line).text;
            const newLineText = lineText.replace(/^(###\s+)/, `$1📋 ${newId}: `);

            await editor.edit(editBuilder => {
                const lineRange = editor.document.lineAt(line).range;
                editBuilder.replace(lineRange, newLineText);
            });
        })
    );

    // Update story status
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.updateStoryStatus', async (storyId: string, line: number) => {
            const status = await vscode.window.showQuickPick([
                { label: '📋 To Do', value: 'todo', emoji: '📋' },
                { label: '🔄 In Progress', value: 'in_progress', emoji: '🔄' },
                { label: '👀 In Review', value: 'review', emoji: '👀' },
                { label: '✅ Done', value: 'done', emoji: '✅' },
                { label: '⏸️ Blocked', value: 'blocked', emoji: '⏸️' },
            ], { placeHolder: 'Select new status' });

            if (!status) return;

            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const lineText = editor.document.lineAt(line).text;
            // Replace existing emoji with new one
            const newLineText = lineText.replace(/^(###\s+)[📋✅🔄⏸️👀]*\s*/, `$1${status.emoji} `);

            await editor.edit(editBuilder => {
                const lineRange = editor.document.lineAt(line).range;
                editBuilder.replace(lineRange, newLineText);
            });

            // Optionally sync to tracker
            const config = vscode.workspace.getConfiguration('spectra');
            if (config.get<boolean>('autoSync')) {
                await runSpectra(['issue', 'update', storyId, '--status', status.value]);
            }
        })
    );

    // Sync single story
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.syncSingleStory', async (storyId: string) => {
            const result = await runSpectra(['issue', 'sync', storyId]);
            if (result.code === 0) {
                vscode.window.showInformationMessage(`Synced ${storyId}`);
            } else {
                vscode.window.showErrorMessage(`Failed to sync ${storyId}`);
            }
        })
    );

    // Generate acceptance criteria with AI
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.generateAcceptanceCriteria', async (line: number) => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            // Find the story title from the previous lines
            let storyTitle = '';
            for (let i = line - 1; i >= 0; i--) {
                const text = editor.document.lineAt(i).text;
                const match = text.match(/^###\s+[📋✅🔄⏸️]*\s*(?:[A-Z]+-\d+)?:?\s*(.+)/);
                if (match) {
                    storyTitle = match[1].trim();
                    break;
                }
            }

            if (!storyTitle) {
                vscode.window.showWarningMessage('Could not find story title');
                return;
            }

            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Generating acceptance criteria...',
                cancellable: false
            }, async () => {
                const result = await runSpectra(['ai', 'generate-ac', '--title', storyTitle, '--format', 'markdown']);

                if (result.code === 0 && result.stdout) {
                    // Insert the generated AC after the current line
                    await editor.edit(editBuilder => {
                        const position = new vscode.Position(line + 1, 0);
                        editBuilder.insert(position, result.stdout + '\n');
                    });
                } else {
                    vscode.window.showErrorMessage('Failed to generate acceptance criteria');
                }
            });
        })
    );

    // Estimate story points with AI
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.estimateStoryPoints', async (line: number) => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            // Get story context
            const lineText = editor.document.lineAt(line).text;

            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Estimating story points...',
                cancellable: false
            }, async () => {
                const result = await runSpectra(['ai', 'estimate', '--context', lineText]);

                if (result.code === 0) {
                    const match = result.stdout.match(/(\d+)/);
                    if (match) {
                        const points = match[1];
                        const newLineText = lineText.replace(/Story Points:\s*(\?|TBD)/i, `Story Points: ${points}`);

                        await editor.edit(editBuilder => {
                            const lineRange = editor.document.lineAt(line).range;
                            editBuilder.replace(lineRange, newLineText);
                        });

                        vscode.window.showInformationMessage(`Estimated: ${points} story points`);
                    }
                } else {
                    vscode.window.showErrorMessage('Failed to estimate story points');
                }
            });
        })
    );

    // Refresh sidebar
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.refreshSidebar', () => {
            sidebarProvider.refresh();
        })
    );

    // Refresh issue cache
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.refreshIssueCache', (issueId?: string) => {
            clearIssueCache(issueId);
            vscode.window.showInformationMessage('Issue cache cleared');
        })
    );

    // Open settings
    context.subscriptions.push(
        vscode.commands.registerCommand('spectra.openSettings', () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'spectra');
        })
    );
}

/**
 * Register providers
 */
function registerProviders(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('spectra');
    const markdownSelector = { language: 'markdown', scheme: 'file' };

    // CodeLens provider
    if (config.get<boolean>('showCodeLens')) {
        context.subscriptions.push(
            vscode.languages.registerCodeLensProvider(
                markdownSelector,
                new StoryCodeLensProvider()
            )
        );
    }

    // Tree view provider (explorer sidebar)
    const treeDataProvider = new StoryTreeDataProvider();
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('spectraStories', treeDataProvider)
    );

    // Decoration provider
    if (config.get<boolean>('showStoryDecorations')) {
        const decorationProvider = new StoryDecorationProvider();
        context.subscriptions.push(decorationProvider);
    }

    // Code Actions provider (Quick Actions)
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            markdownSelector,
            new SpectraCodeActionProvider(),
            {
                providedCodeActionKinds: SpectraCodeActionProvider.providedCodeActionKinds
            }
        )
    );

    // Hover provider (Hover Previews)
    if (config.get<boolean>('showHoverPreviews', true)) {
        context.subscriptions.push(
            vscode.languages.registerHoverProvider(
                markdownSelector,
                new SpectraHoverProvider()
            )
        );
    }

    // Definition provider (Go to Tracker - Cmd+Click)
    if (config.get<boolean>('enableGoToTracker', true)) {
        context.subscriptions.push(
            vscode.languages.registerDefinitionProvider(
                markdownSelector,
                new SpectraDefinitionProvider()
            )
        );

        // Document link provider (clickable links)
        context.subscriptions.push(
            vscode.languages.registerDocumentLinkProvider(
                markdownSelector,
                new SpectraDocumentLinkProvider()
            )
        );
    }
}

/**
 * Register event handlers
 */
function registerEventHandlers(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('spectra');

    // Update status bar on editor change
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(() => {
            updateStatusBar();
        })
    );

    // Update status bar on document change
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument((e) => {
            if (e.document === vscode.window.activeTextEditor?.document) {
                updateStatusBar();
            }
        })
    );

    // Auto-validate on save
    if (config.get<boolean>('autoValidate')) {
        context.subscriptions.push(
            vscode.workspace.onDidSaveTextDocument(async (document) => {
                if (document.languageId === 'markdown') {
                    await runValidate(document, true);
                }
            })
        );
    }
}

/**
 * Run spectra validate
 */
async function runValidate(document: vscode.TextDocument, silent: boolean = false): Promise<void> {
    const args = ['--validate', '--markdown', document.uri.fsPath];

    if (!silent) {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Validating markdown...',
            cancellable: false
        }, async () => {
            const result = await runSpectra(args);
            diagnosticsProvider.updateDiagnostics(document, result);

            if (result.code === 0) {
                vscode.window.showInformationMessage('✓ Validation passed');
            } else {
                vscode.window.showErrorMessage('✗ Validation failed');
                showResultPanel('Validation Results', result.stdout);
            }
        });
    } else {
        const result = await runSpectra(args);
        diagnosticsProvider.updateDiagnostics(document, result);
    }
}

/**
 * Run spectra sync
 */
async function runSync(document: vscode.TextDocument, epicKey: string, execute: boolean): Promise<void> {
    const args = ['--markdown', document.uri.fsPath, '--epic', epicKey];

    if (execute) {
        args.push('--execute', '--no-confirm');
    }

    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: execute ? 'Syncing to Jira...' : 'Running dry-run sync...',
        cancellable: false
    }, async () => {
        const result = await runSpectra(args);

        if (result.code === 0) {
            const msg = execute ? '✓ Sync completed' : '✓ Dry-run completed';
            vscode.window.showInformationMessage(msg);
        } else {
            vscode.window.showErrorMessage('✗ Sync failed');
        }

        showResultPanel('Sync Results', result.stdout);
    });
}

/**
 * Get or prompt for epic key
 */
async function getEpicKey(document: vscode.TextDocument): Promise<string | undefined> {
    let epic = detectEpic(document);

    if (!epic) {
        epic = await vscode.window.showInputBox({
            prompt: 'Enter Jira Epic Key',
            placeHolder: 'PROJ-123'
        });
    }

    return epic;
}

/**
 * Detect epic key from document
 */
function detectEpic(document: vscode.TextDocument): string | undefined {
    const text = document.getText();
    const match = text.match(/([A-Z][A-Z0-9]+-\d+)/);
    return match ? match[1] : undefined;
}

/**
 * Parse stories from document
 */
function parseStories(document: vscode.TextDocument): Story[] {
    const stories: Story[] = [];
    const text = document.getText();
    const lines = text.split('\n');

    // Pattern: ### 📋 US-001: Title or ### US-001: Title
    const storyPattern = /^###\s+[📋✅🔄⏸️]*\s*([A-Z]+-\d+):\s*(.+)/;

    for (let i = 0; i < lines.length; i++) {
        const match = lines[i].match(storyPattern);
        if (match) {
            stories.push({
                id: match[1],
                title: match[2].trim(),
                line: i + 1
            });
        }
    }

    return stories;
}

/**
 * Get story at specific line
 */
function getStoryAtLine(document: vscode.TextDocument, line: number): Story | undefined {
    const stories = parseStories(document);

    // Find the story that contains this line
    for (let i = stories.length - 1; i >= 0; i--) {
        if (stories[i].line - 1 <= line) {
            return stories[i];
        }
    }

    return undefined;
}

/**
 * Update status bar
 */
function updateStatusBar(): void {
    const config = vscode.workspace.getConfiguration('spectra');
    if (!config.get<boolean>('showStatusBar')) {
        statusBarItem.hide();
        return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'markdown') {
        statusBarItem.hide();
        return;
    }

    const stories = parseStories(editor.document);
    const epic = detectEpic(editor.document);

    if (stories.length > 0) {
        statusBarItem.text = `$(list-unordered) ${stories.length} stories`;
        if (epic) {
            statusBarItem.text += ` (${epic})`;
        }
        statusBarItem.tooltip = 'Click to jump to a story';
        statusBarItem.show();
    } else {
        statusBarItem.hide();
    }
}

/**
 * Run spectra CLI command
 */
function runSpectra(args: string[]): Promise<SpectraResult> {
    return new Promise((resolve) => {
        const executable = getExecutable();
        const cmd = [executable, ...args].join(' ');

        outputChannel.appendLine(`> ${cmd}`);

        cp.exec(cmd, { maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
            outputChannel.appendLine(stdout);
            if (stderr) {
                outputChannel.appendLine(stderr);
            }

            resolve({
                code: error ? error.code || 1 : 0,
                stdout: stdout || '',
                stderr: stderr || ''
            });
        });
    });
}

/**
 * Get spectra executable path
 */
function getExecutable(): string {
    const config = vscode.workspace.getConfiguration('spectra');
    return config.get<string>('executable') || 'spectra';
}

/**
 * Show result in a panel
 */
function showResultPanel(title: string, content: string): void {
    const panel = vscode.window.createWebviewPanel(
        'spectraResult',
        title,
        vscode.ViewColumn.Beside,
        {}
    );

    panel.webview.html = `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                    color: var(--vscode-foreground);
                    background: var(--vscode-editor-background);
                }
                pre {
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    font-family: var(--vscode-editor-font-family);
                    font-size: var(--vscode-editor-font-size);
                    line-height: 1.5;
                }
                .success { color: var(--vscode-terminal-ansiGreen); }
                .error { color: var(--vscode-terminal-ansiRed); }
                .warning { color: var(--vscode-terminal-ansiYellow); }
            </style>
        </head>
        <body>
            <pre>${escapeHtml(content)}</pre>
        </body>
        </html>
    `;
}

/**
 * Escape HTML
 */
function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Build tracker URL for an issue ID
 */
function buildTrackerUrl(baseUrl: string, issueId: string): string {
    const url = baseUrl.replace(/\/$/, '');

    // Detect tracker type and build appropriate URL
    if (url.includes('atlassian.net') || url.includes('jira')) {
        return `${url}/browse/${issueId}`;
    }
    if (url.includes('github.com')) {
        const issueNum = issueId.replace(/[A-Z]+-/, '');
        return `${url}/issues/${issueNum}`;
    }
    if (url.includes('gitlab')) {
        const issueNum = issueId.replace(/[A-Z]+-/, '');
        return `${url}/-/issues/${issueNum}`;
    }
    if (url.includes('linear.app')) {
        return `${url}/issue/${issueId}`;
    }
    if (url.includes('shortcut.com') || url.includes('clubhouse.io')) {
        const storyNum = issueId.replace(/[A-Z]+-/, '');
        return `${url}/story/${storyNum}`;
    }
    if (url.includes('youtrack')) {
        return `${url}/issue/${issueId}`;
    }
    if (url.includes('azure') || url.includes('dev.azure.com')) {
        const workItemId = issueId.replace(/[A-Z]+-/, '');
        return `${url}/_workitems/edit/${workItemId}`;
    }
    if (url.includes('trello.com')) {
        return `${url}/c/${issueId}`;
    }
    if (url.includes('asana.com')) {
        const taskId = issueId.replace(/[A-Z]+-/, '');
        return `${url}/0/0/${taskId}`;
    }
    if (url.includes('monday.com')) {
        const pulseId = issueId.replace(/[A-Z]+-/, '');
        return `${url}/boards/pulse/${pulseId}`;
    }
    if (url.includes('clickup.com')) {
        const taskId = issueId.replace(/[A-Z]+-/, '');
        return `${url}/t/${taskId}`;
    }
    if (url.includes('notion.so')) {
        return `${url}/${issueId}`;
    }
    if (url.includes('plane.so') || url.includes('plane')) {
        return `${url}/issues/${issueId}`;
    }
    if (url.includes('pivotaltracker.com')) {
        const storyId = issueId.replace(/[A-Z]+-/, '');
        return `${url}/story/show/${storyId}`;
    }
    if (url.includes('basecamp.com')) {
        return `${url}/todos/${issueId}`;
    }

    // Default: assume Jira-like browse URL
    return `${url}/browse/${issueId}`;
}

// Export for testing
export { parseStories, detectEpic, getStoryAtLine, buildTrackerUrl };
