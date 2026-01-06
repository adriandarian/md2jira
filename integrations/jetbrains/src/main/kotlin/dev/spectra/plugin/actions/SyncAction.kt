package dev.spectra.plugin.actions

import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.openapi.project.Project
import dev.spectra.plugin.settings.SpectraSettings
import java.io.BufferedReader
import java.io.InputStreamReader

class SyncAction : AnAction() {

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return

        if (!virtualFile.extension.equals("md", ignoreCase = true)) {
            showNotification(project, "Please select a markdown file", NotificationType.WARNING)
            return
        }

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "Syncing to Tracker") {
            override fun run(indicator: ProgressIndicator) {
                indicator.isIndeterminate = false
                indicator.fraction = 0.0
                indicator.text = "Preparing sync..."

                try {
                    val settings = SpectraSettings.getInstance()

                    indicator.fraction = 0.2
                    indicator.text = "Connecting to ${settings.trackerType}..."

                    val process = ProcessBuilder(
                        settings.spectraPath,
                        "--sync",
                        "--markdown",
                        virtualFile.path,
                        "--tracker",
                        settings.trackerType
                    )
                        .redirectErrorStream(true)
                        .start()

                    indicator.fraction = 0.5
                    indicator.text = "Syncing stories..."

                    val output = BufferedReader(InputStreamReader(process.inputStream)).readText()
                    val exitCode = process.waitFor()

                    indicator.fraction = 1.0

                    if (exitCode == 0) {
                        showNotification(project, "Sync completed successfully ✓", NotificationType.INFORMATION)
                    } else {
                        showNotification(project, "Sync failed:\n$output", NotificationType.ERROR)
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

    private fun showNotification(project: Project, content: String, type: NotificationType) {
        NotificationGroupManager.getInstance()
            .getNotificationGroup("Spectra Notifications")
            .createNotification(content, type)
            .notify(project)
    }
}
