package dev.spectra.plugin.settings

import com.intellij.openapi.options.Configurable
import com.intellij.openapi.ui.ComboBox
import com.intellij.ui.components.JBCheckBox
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.FormBuilder
import javax.swing.JComponent
import javax.swing.JPanel

class SpectraSettingsConfigurable : Configurable {

    private var panel: JPanel? = null
    private var trackerTypeCombo: ComboBox<String>? = null
    private var trackerUrlField: JBTextField? = null
    private var projectKeyField: JBTextField? = null
    private var validateOnSaveCheckbox: JBCheckBox? = null
    private var showSyncStatusCheckbox: JBCheckBox? = null
    private var spectraPathField: JBTextField? = null

    private val trackerTypes = arrayOf(
        "jira", "github", "gitlab", "linear", "azure",
        "trello", "asana", "clickup", "monday", "shortcut",
        "youtrack", "plane", "pivotal", "basecamp", "notion"
    )

    override fun getDisplayName(): String = "Spectra"

    override fun createComponent(): JComponent {
        val settings = SpectraSettings.getInstance()

        trackerTypeCombo = ComboBox(trackerTypes).apply {
            selectedItem = settings.trackerType
        }

        trackerUrlField = JBTextField(settings.trackerUrl, 40)
        projectKeyField = JBTextField(settings.projectKey, 20)
        validateOnSaveCheckbox = JBCheckBox("Validate on save", settings.validateOnSave)
        showSyncStatusCheckbox = JBCheckBox("Show sync status in status bar", settings.showSyncStatus)
        spectraPathField = JBTextField(settings.spectraPath, 30)

        panel = FormBuilder.createFormBuilder()
            .addLabeledComponent(JBLabel("Tracker Type:"), trackerTypeCombo!!, 1, false)
            .addLabeledComponent(JBLabel("Tracker URL:"), trackerUrlField!!, 1, false)
            .addLabeledComponent(JBLabel("Project Key:"), projectKeyField!!, 1, false)
            .addSeparator()
            .addComponent(validateOnSaveCheckbox!!)
            .addComponent(showSyncStatusCheckbox!!)
            .addSeparator()
            .addLabeledComponent(JBLabel("Spectra CLI Path:"), spectraPathField!!, 1, false)
            .addComponentFillVertically(JPanel(), 0)
            .panel

        return panel!!
    }

    override fun isModified(): Boolean {
        val settings = SpectraSettings.getInstance()
        return trackerTypeCombo?.selectedItem != settings.trackerType ||
               trackerUrlField?.text != settings.trackerUrl ||
               projectKeyField?.text != settings.projectKey ||
               validateOnSaveCheckbox?.isSelected != settings.validateOnSave ||
               showSyncStatusCheckbox?.isSelected != settings.showSyncStatus ||
               spectraPathField?.text != settings.spectraPath
    }

    override fun apply() {
        val settings = SpectraSettings.getInstance()
        settings.trackerType = trackerTypeCombo?.selectedItem as? String ?: "jira"
        settings.trackerUrl = trackerUrlField?.text ?: ""
        settings.projectKey = projectKeyField?.text ?: ""
        settings.validateOnSave = validateOnSaveCheckbox?.isSelected ?: true
        settings.showSyncStatus = showSyncStatusCheckbox?.isSelected ?: true
        settings.spectraPath = spectraPathField?.text ?: "spectra"
    }

    override fun reset() {
        val settings = SpectraSettings.getInstance()
        trackerTypeCombo?.selectedItem = settings.trackerType
        trackerUrlField?.text = settings.trackerUrl
        projectKeyField?.text = settings.projectKey
        validateOnSaveCheckbox?.isSelected = settings.validateOnSave
        showSyncStatusCheckbox?.isSelected = settings.showSyncStatus
        spectraPathField?.text = settings.spectraPath
    }

    override fun disposeUIResources() {
        panel = null
        trackerTypeCombo = null
        trackerUrlField = null
        projectKeyField = null
        validateOnSaveCheckbox = null
        showSyncStatusCheckbox = null
        spectraPathField = null
    }
}
