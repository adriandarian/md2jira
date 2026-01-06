package dev.spectra.plugin.toolwindow

import com.intellij.openapi.project.Project
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.treeStructure.Tree
import com.intellij.util.ui.JBUI
import java.awt.BorderLayout
import javax.swing.JPanel
import javax.swing.tree.DefaultMutableTreeNode
import javax.swing.tree.DefaultTreeModel

class SpectraStoriesPanel(private val project: Project) : JPanel(BorderLayout()) {

    private val treeModel: DefaultTreeModel
    private val tree: Tree

    init {
        val root = DefaultMutableTreeNode("Stories")
        treeModel = DefaultTreeModel(root)
        tree = Tree(treeModel)

        // Add placeholder content
        val epicNode = DefaultMutableTreeNode("# Epic: User Authentication")
        val story1 = DefaultMutableTreeNode("## Story: Login form [PROJ-123]")
        val story2 = DefaultMutableTreeNode("## Story: Password reset [PROJ-124]")
        epicNode.add(story1)
        epicNode.add(story2)
        root.add(epicNode)

        tree.expandRow(0)

        add(JBScrollPane(tree), BorderLayout.CENTER)

        // Toolbar
        val toolbar = JPanel()
        toolbar.add(JBLabel("Refresh to load stories from current file"))
        add(toolbar, BorderLayout.NORTH)

        border = JBUI.Borders.empty(5)
    }

    fun refresh() {
        // TODO: Parse current file and update tree
    }
}

class SpectraSyncPanel(private val project: Project) : JPanel(BorderLayout()) {

    init {
        val content = JPanel().apply {
            layout = java.awt.GridBagLayout()
            val gbc = java.awt.GridBagConstraints().apply {
                gridx = 0
                gridy = 0
                anchor = java.awt.GridBagConstraints.WEST
                insets = JBUI.insets(5)
            }

            add(JBLabel("Sync Status: "), gbc)
            gbc.gridx = 1
            add(JBLabel("Not synced"), gbc)

            gbc.gridx = 0
            gbc.gridy = 1
            add(JBLabel("Last Sync: "), gbc)
            gbc.gridx = 1
            add(JBLabel("Never"), gbc)

            gbc.gridx = 0
            gbc.gridy = 2
            add(JBLabel("Tracker: "), gbc)
            gbc.gridx = 1
            add(JBLabel("Not configured"), gbc)
        }

        add(content, BorderLayout.NORTH)
        border = JBUI.Borders.empty(10)
    }
}

class SpectraChangesPanel(private val project: Project) : JPanel(BorderLayout()) {

    init {
        val content = JBLabel("No recent changes")
        content.horizontalAlignment = JBLabel.CENTER
        add(content, BorderLayout.CENTER)
        border = JBUI.Borders.empty(10)
    }
}
