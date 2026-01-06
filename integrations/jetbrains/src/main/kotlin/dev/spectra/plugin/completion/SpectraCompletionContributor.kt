package dev.spectra.plugin.completion

import com.intellij.codeInsight.completion.*
import com.intellij.codeInsight.lookup.LookupElementBuilder
import com.intellij.patterns.PlatformPatterns
import com.intellij.psi.PsiElement
import com.intellij.util.ProcessingContext
import com.intellij.icons.AllIcons

class SpectraCompletionContributor : CompletionContributor() {

    init {
        // Register completion provider for markdown
        extend(
            CompletionType.BASIC,
            PlatformPatterns.psiElement(),
            SpectraCompletionProvider()
        )
    }
}

class SpectraCompletionProvider : CompletionProvider<CompletionParameters>() {

    private val statusValues = listOf("Todo", "In Progress", "In Review", "Done", "Blocked", "Cancelled")
    private val priorityValues = listOf("Critical", "High", "Medium", "Low")
    private val pointsValues = listOf("1", "2", "3", "5", "8", "13", "21")
    private val headerTypes = listOf("Epic:", "Story:", "Subtask:")
    private val metadataFields = listOf("Status", "Priority", "Points", "Assignee", "Labels", "Sprint")

    override fun addCompletions(
        parameters: CompletionParameters,
        context: ProcessingContext,
        result: CompletionResultSet
    ) {
        val position = parameters.position
        val lineText = getLineText(position)
        val prefix = lineText.substringBefore(position.text).trim()

        when {
            // Status completions
            prefix.endsWith("**Status**:") || prefix.endsWith("**Status**: ") -> {
                statusValues.forEach { status ->
                    result.addElement(
                        LookupElementBuilder.create(status)
                            .withIcon(getStatusIcon(status))
                            .withTypeText("Status")
                    )
                }
            }

            // Priority completions
            prefix.endsWith("**Priority**:") || prefix.endsWith("**Priority**: ") -> {
                priorityValues.forEach { priority ->
                    result.addElement(
                        LookupElementBuilder.create(priority)
                            .withIcon(getPriorityIcon(priority))
                            .withTypeText("Priority")
                    )
                }
            }

            // Points completions
            prefix.endsWith("**Points**:") || prefix.endsWith("**Points**: ") -> {
                pointsValues.forEach { points ->
                    result.addElement(
                        LookupElementBuilder.create(points)
                            .withTypeText("Fibonacci")
                    )
                }
            }

            // Header type completions
            prefix.matches(Regex("^##?\\s*$")) -> {
                headerTypes.forEach { type ->
                    result.addElement(
                        LookupElementBuilder.create(type)
                            .withIcon(AllIcons.Nodes.Tag)
                            .withTypeText("Spectra ${type.removeSuffix(":")}")
                    )
                }
            }

            // Metadata field completions at line start
            prefix.isEmpty() || prefix == "*" -> {
                metadataFields.forEach { field ->
                    result.addElement(
                        LookupElementBuilder.create("**$field**: ")
                            .withPresentableText("**$field**:")
                            .withIcon(AllIcons.Nodes.Property)
                            .withTypeText("Metadata")
                    )
                }
            }
        }
    }

    private fun getLineText(position: PsiElement): String {
        val document = position.containingFile?.viewProvider?.document ?: return ""
        val lineNumber = document.getLineNumber(position.textOffset)
        val lineStart = document.getLineStartOffset(lineNumber)
        val lineEnd = document.getLineEndOffset(lineNumber)
        return document.getText(com.intellij.openapi.util.TextRange(lineStart, lineEnd))
    }

    private fun getStatusIcon(status: String) = when (status) {
        "Done" -> AllIcons.Actions.Checked
        "In Progress" -> AllIcons.Actions.Execute
        "In Review" -> AllIcons.Actions.Preview
        "Blocked" -> AllIcons.Actions.Suspend
        "Cancelled" -> AllIcons.Actions.Cancel
        else -> AllIcons.Actions.AddToDictionary
    }

    private fun getPriorityIcon(priority: String) = when (priority) {
        "Critical" -> AllIcons.Ide.FatalError
        "High" -> AllIcons.Actions.IntentionBulb
        "Medium" -> AllIcons.Actions.IntentionBulbGrey
        else -> AllIcons.General.Information
    }
}
