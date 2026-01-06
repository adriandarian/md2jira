;;; spectra-eglot.el --- Eglot configuration for Spectra -*- lexical-binding: t; -*-

;; Copyright (C) 2024 Spectra Contributors

;; Author: Spectra Contributors
;; Keywords: languages, tools, markdown
;; URL: https://github.com/spectra/spectra
;; Version: 0.1.0
;; Package-Requires: ((emacs "29.1") (markdown-mode "2.5"))

;;; Commentary:

;; This package provides eglot integration for the Spectra language server,
;; enabling IDE features for Spectra markdown user story files.
;; Eglot is built into Emacs 29+.

;;; Code:

(require 'eglot)
(require 'markdown-mode)

(defgroup spectra-eglot nil
  "Spectra eglot configuration."
  :group 'spectra
  :prefix "spectra-eglot-")

(defcustom spectra-eglot-server-path "spectra-lsp"
  "Path to the Spectra language server executable."
  :type 'string
  :group 'spectra-eglot)

(defcustom spectra-eglot-server-args '("--stdio")
  "Arguments to pass to the Spectra language server."
  :type '(repeat string)
  :group 'spectra-eglot)

;; Define the language server
(defclass spectra-eglot-server (eglot-lsp-server) ()
  :documentation "Spectra LSP server class.")

;; Custom initialization options
(cl-defmethod eglot-initialization-options ((server spectra-eglot-server))
  "Return initialization options for Spectra LSP SERVER."
  `(:spectra
    (:tracker
     (:type ,(or (bound-and-true-p spectra-tracker-type) "jira")
      :url ,(or (bound-and-true-p spectra-tracker-url) "")
      :projectKey ,(or (bound-and-true-p spectra-project-key) ""))
     :validation
     (:validateOnSave t
      :validateOnType t)
     :diagnostics
     (:showWarnings t
      :showHints t)
     :hover
     (:cacheTimeout 60))))

;; Register the server with eglot
(add-to-list 'eglot-server-programs
             `((markdown-mode spectra-mode)
               . (spectra-eglot-server
                  . (lambda ()
                      (cons spectra-eglot-server-path
                            spectra-eglot-server-args)))))

;; Alternative simple registration (if custom class not needed)
;; (add-to-list 'eglot-server-programs
;;              '((markdown-mode spectra-mode) . ("spectra-lsp" "--stdio")))

;; Enable eglot for markdown files
(add-hook 'markdown-mode-hook #'eglot-ensure)

;; Workspace configuration
(setq-default eglot-workspace-configuration
              '(:spectra
                (:tracker
                 (:type "jira"
                  :url ""
                  :projectKey "")
                 :validation
                 (:validateOnSave t
                  :validateOnType t))))

(provide 'spectra-eglot)
;;; spectra-eglot.el ends here
