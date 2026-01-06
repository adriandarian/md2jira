use zed_extension_api::{self as zed, LanguageServerId, Result};

struct SpectraExtension;

impl zed::Extension for SpectraExtension {
    fn new() -> Self {
        SpectraExtension
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        // Try to find spectra-lsp in PATH or use pip-installed version
        let path = worktree
            .which("spectra-lsp")
            .unwrap_or_else(|| "spectra-lsp".to_string());

        Ok(zed::Command {
            command: path,
            args: vec!["--stdio".to_string()],
            env: Default::default(),
        })
    }

    fn language_server_initialization_options(
        &mut self,
        _language_server_id: &LanguageServerId,
        _worktree: &zed::Worktree,
    ) -> Result<Option<zed::serde_json::Value>> {
        Ok(Some(zed::serde_json::json!({
            "spectra": {
                "validation": {
                    "validateOnSave": true,
                    "validateOnType": true
                },
                "diagnostics": {
                    "showWarnings": true,
                    "showHints": true
                }
            }
        })))
    }
}

zed::register_extension!(SpectraExtension);
