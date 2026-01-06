package dev.spectra.plugin.actions

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import dev.spectra.plugin.settings.SpectraSettings
import java.io.BufferedReader
import java.io.InputStreamReader

class ValidateAction : AnAction() {

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return

        if (!virtualFile.extension.equals("md", ignoreCase = true)) {
            showNotification(project, "Please select a markdown file", NotificationType.WARNING)
            return
        }

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "Validating Spectra File") {
            override fun run(indicator: ProgressIndicator) {
                indicator.isIndeterminate = true
                indicator.text = "Running validation..."

                try {
                    val settings = SpectraSettings.getInstance()
                    val process = ProcessBuilder(
                        settings.spectraPath,
                        "--validate",
                        "--markdown",
                        virtualFile.path
                    )
                        .redirectErrorStream(true)
                        .start()

                    val output = BufferedReader(InputStreamReader(process.inputStream)).readText()
                    val exitCode = process.waitFor()

                    if (exitCode == 0) {
                        showNotification(project, "Validation passed ✓", NotificationType.INFORMATION)
                    } else {
                        showNotification(project, "Validation failed:\n$output", NotificationType.ERROR)
                    }
                } catch (ex: Exception) {
                    showNotification(project, "Error: ${ex.message}", NotificationType.ERROR)
                }
            }
        })
    }

    override fun update(e: AnActionEvent) {
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        e.presentation.isEnabledAndVisible = virtualFile?.extension?.equals("md", ignoreCase = true) == true
    }

    private fun showNotification(project: com.intellij.openapi.project.Project, content: String, type: NotificationType) {
        NotificationGroupManager.getInstance()
            .getNotificationGroup("Spectra Notifications")
            .createNotification(content, type)
            .notify(project)
    }
}
