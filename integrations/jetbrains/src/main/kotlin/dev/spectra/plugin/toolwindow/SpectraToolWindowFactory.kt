package dev.spectra.plugin.toolwindow

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory

class SpectraToolWindowFactory : ToolWindowFactory {

    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val contentFactory = ContentFactory.getInstance()

        // Stories tab
        val storiesPanel = SpectraStoriesPanel(project)
        val storiesContent = contentFactory.createContent(storiesPanel, "Stories", false)
        toolWindow.contentManager.addContent(storiesContent)

        // Sync Status tab
        val syncPanel = SpectraSyncPanel(project)
        val syncContent = contentFactory.createContent(syncPanel, "Sync Status", false)
        toolWindow.contentManager.addContent(syncContent)

        // Recent Changes tab
        val changesPanel = SpectraChangesPanel(project)
        val changesContent = contentFactory.createContent(changesPanel, "Recent Changes", false)
        toolWindow.contentManager.addContent(changesContent)
    }

    override fun shouldBeAvailable(project: Project): Boolean = true
}
