package dev.spectra.plugin.settings

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage

@State(
    name = "SpectraSettings",
    storages = [Storage("spectra.xml")]
)
class SpectraSettings : PersistentStateComponent<SpectraSettings.State> {

    data class State(
        var trackerType: String = "jira",
        var trackerUrl: String = "",
        var projectKey: String = "",
        var validateOnSave: Boolean = true,
        var showSyncStatus: Boolean = true,
        var spectraPath: String = "spectra"
    )

    private var state = State()

    override fun getState(): State = state

    override fun loadState(state: State) {
        this.state = state
    }

    companion object {
        fun getInstance(): SpectraSettings {
            return ApplicationManager.getApplication().getService(SpectraSettings::class.java)
        }
    }

    var trackerType: String
        get() = state.trackerType
        set(value) { state.trackerType = value }

    var trackerUrl: String
        get() = state.trackerUrl
        set(value) { state.trackerUrl = value }

    var projectKey: String
        get() = state.projectKey
        set(value) { state.projectKey = value }

    var validateOnSave: Boolean
        get() = state.validateOnSave
        set(value) { state.validateOnSave = value }

    var showSyncStatus: Boolean
        get() = state.showSyncStatus
        set(value) { state.showSyncStatus = value }

    var spectraPath: String
        get() = state.spectraPath
        set(value) { state.spectraPath = value }
}
