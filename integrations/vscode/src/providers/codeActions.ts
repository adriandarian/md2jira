/**
 * Code Actions provider for spectra
 *
 * Provides quick actions to create stories in trackers from cursor position.
 */

import * as vscode from 'vscode';

export class SpectraCodeActionProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix,
        vscode.CodeActionKind.Refactor,
    ];

    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        _context: vscode.CodeActionContext,
        _token: vscode.CancellationToken
    ): vscode.CodeAction[] | undefined {
        const actions: vscode.CodeAction[] = [];
        const line = document.lineAt(range.start.line);
        const lineText = line.text;

        // Check if we're on a story header line (with or without ID)
        const storyWithIdPattern = /^###\s+[📋✅🔄⏸️]*\s*([A-Z]+-\d+):\s*(.+)/;
        const storyWithoutIdPattern = /^###\s+(.+?)(?:\s*$)/;
        const subtaskPattern = /^####\s+(.+?)(?:\s*$)/;
        const epicPattern = /^#\s+[🚀]*\s*([A-Z][A-Z0-9]+-\d+)?:?\s*(.+)/;

        // Story with ID - offer sync and open actions
        const storyWithIdMatch = lineText.match(storyWithIdPattern);
        if (storyWithIdMatch) {
            const storyId = storyWithIdMatch[1];

            // Open in tracker
            const openAction = new vscode.CodeAction(
                `Open ${storyId} in Tracker`,
                vscode.CodeActionKind.QuickFix
            );
            openAction.command = {
                command: 'spectra.openInJira',
                title: 'Open in Tracker',
            };
            actions.push(openAction);

            // Copy ID
            const copyAction = new vscode.CodeAction(
                `Copy ${storyId}`,
                vscode.CodeActionKind.QuickFix
            );
            copyAction.command = {
                command: 'spectra.copyStoryId',
                title: 'Copy Story ID',
            };
            actions.push(copyAction);

            // Sync this story
            const syncAction = new vscode.CodeAction(
                `Sync ${storyId} to Tracker`,
                vscode.CodeActionKind.Refactor
            );
            syncAction.command = {
                command: 'spectra.syncSingleStory',
                title: 'Sync Story',
                arguments: [storyId],
            };
            actions.push(syncAction);

            // Update status
            const updateStatusAction = new vscode.CodeAction(
                `Update Status of ${storyId}`,
                vscode.CodeActionKind.Refactor
            );
            updateStatusAction.command = {
                command: 'spectra.updateStoryStatus',
                title: 'Update Status',
                arguments: [storyId, range.start.line],
            };
            actions.push(updateStatusAction);

            return actions;
        }

        // Story without ID - offer to create in tracker
        const storyWithoutIdMatch = lineText.match(storyWithoutIdPattern);
        if (storyWithoutIdMatch && !lineText.match(storyWithIdPattern)) {
            const title = storyWithoutIdMatch[1].trim();

            if (title && !title.match(/^[A-Z]+-\d+/)) {
                const createAction = new vscode.CodeAction(
                    `Create "${title.substring(0, 30)}${title.length > 30 ? '...' : ''}" in Tracker`,
                    vscode.CodeActionKind.QuickFix
                );
                createAction.command = {
                    command: 'spectra.createStoryInTracker',
                    title: 'Create Story in Tracker',
                    arguments: [title, range.start.line, 'story'],
                };
                createAction.isPreferred = true;
                actions.push(createAction);

                // Generate ID locally
                const generateIdAction = new vscode.CodeAction(
                    'Generate Story ID',
                    vscode.CodeActionKind.Refactor
                );
                generateIdAction.command = {
                    command: 'spectra.generateStoryId',
                    title: 'Generate Story ID',
                    arguments: [range.start.line],
                };
                actions.push(generateIdAction);
            }
        }

        // Subtask - offer to create
        const subtaskMatch = lineText.match(subtaskPattern);
        if (subtaskMatch) {
            const title = subtaskMatch[1].trim();

            if (title && !title.match(/^[A-Z]+-\d+/)) {
                const createAction = new vscode.CodeAction(
                    `Create Subtask "${title.substring(0, 30)}${title.length > 30 ? '...' : ''}" in Tracker`,
                    vscode.CodeActionKind.QuickFix
                );
                createAction.command = {
                    command: 'spectra.createStoryInTracker',
                    title: 'Create Subtask in Tracker',
                    arguments: [title, range.start.line, 'subtask'],
                };
                actions.push(createAction);
            }
        }

        // Epic header - offer sync and validation
        const epicMatch = lineText.match(epicPattern);
        if (epicMatch) {
            const epicId = epicMatch[1];
            const epicTitle = epicMatch[2];

            if (epicId) {
                // Sync epic
                const syncAction = new vscode.CodeAction(
                    `Sync Epic ${epicId}`,
                    vscode.CodeActionKind.Refactor
                );
                syncAction.command = {
                    command: 'spectra.sync',
                    title: 'Sync Epic',
                };
                actions.push(syncAction);

                // Validate
                const validateAction = new vscode.CodeAction(
                    'Validate Document',
                    vscode.CodeActionKind.QuickFix
                );
                validateAction.command = {
                    command: 'spectra.validate',
                    title: 'Validate',
                };
                actions.push(validateAction);

                // Open epic in tracker
                const openEpicAction = new vscode.CodeAction(
                    `Open Epic ${epicId} in Tracker`,
                    vscode.CodeActionKind.QuickFix
                );
                openEpicAction.command = {
                    command: 'spectra.openEpicInTracker',
                    title: 'Open Epic in Tracker',
                    arguments: [epicId],
                };
                actions.push(openEpicAction);
            } else if (epicTitle) {
                // Create epic in tracker
                const createEpicAction = new vscode.CodeAction(
                    `Create Epic "${epicTitle.substring(0, 30)}${epicTitle.length > 30 ? '...' : ''}" in Tracker`,
                    vscode.CodeActionKind.QuickFix
                );
                createEpicAction.command = {
                    command: 'spectra.createStoryInTracker',
                    title: 'Create Epic in Tracker',
                    arguments: [epicTitle.trim(), range.start.line, 'epic'],
                };
                actions.push(createEpicAction);
            }
        }

        // Check for acceptance criteria - offer to generate
        if (lineText.match(/^\*\*Acceptance Criteria:\*\*\s*$/i)) {
            const generateACAction = new vscode.CodeAction(
                'Generate Acceptance Criteria with AI',
                vscode.CodeActionKind.Refactor
            );
            generateACAction.command = {
                command: 'spectra.generateAcceptanceCriteria',
                title: 'Generate Acceptance Criteria',
                arguments: [range.start.line],
            };
            actions.push(generateACAction);
        }

        // Check for story points placeholder
        if (lineText.match(/Story Points:\s*\?|Story Points:\s*TBD/i)) {
            const estimateAction = new vscode.CodeAction(
                'Estimate Story Points with AI',
                vscode.CodeActionKind.Refactor
            );
            estimateAction.command = {
                command: 'spectra.estimateStoryPoints',
                title: 'Estimate Story Points',
                arguments: [range.start.line],
            };
            actions.push(estimateAction);
        }

        return actions.length > 0 ? actions : undefined;
    }
}
