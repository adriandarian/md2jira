;;; spectra-lsp.el --- LSP configuration for Spectra -*- lexical-binding: t; -*-

;; Copyright (C) 2024 Spectra Contributors

;; Author: Spectra Contributors
;; Keywords: languages, tools, markdown
;; URL: https://github.com/spectra/spectra
;; Version: 0.1.0
;; Package-Requires: ((emacs "27.1") (lsp-mode "8.0.0") (markdown-mode "2.5"))

;;; Commentary:

;; This package provides lsp-mode integration for the Spectra language server,
;; enabling IDE features for Spectra markdown user story files.

;;; Code:

(require 'lsp-mode)
(require 'markdown-mode)

(defgroup spectra nil
  "Spectra markdown user story support."
  :group 'languages
  :prefix "spectra-")

(defcustom spectra-lsp-server-path "spectra-lsp"
  "Path to the Spectra language server executable."
  :type 'string
  :group 'spectra)

(defcustom spectra-tracker-type "jira"
  "Type of issue tracker (jira, github, gitlab, linear, azure, etc.)."
  :type 'string
  :group 'spectra)

(defcustom spectra-tracker-url ""
  "Base URL of your issue tracker."
  :type 'string
  :group 'spectra)

(defcustom spectra-project-key ""
  "Project key or identifier in your tracker."
  :type 'string
  :group 'spectra)

(defcustom spectra-validate-on-save t
  "Whether to validate files on save."
  :type 'boolean
  :group 'spectra)

(defcustom spectra-validate-on-type t
  "Whether to validate files while typing."
  :type 'boolean
  :group 'spectra)

(defcustom spectra-show-warnings t
  "Whether to show warning diagnostics."
  :type 'boolean
  :group 'spectra)

(defcustom spectra-hover-cache-timeout 60
  "Cache timeout for hover information in seconds."
  :type 'integer
  :group 'spectra)

;; Register the Spectra language server with lsp-mode
(lsp-register-client
 (make-lsp-client
  :new-connection (lsp-stdio-connection
                   (lambda ()
                     (list spectra-lsp-server-path "--stdio")))
  :activation-fn (lambda (filename _mode)
                   (or (string-match-p "\\.spectra\\.md\\'" filename)
                       (string-match-p "user-stories\\.md\\'" filename)
                       (string-match-p "backlog\\.md\\'" filename)
                       (string-match-p "requirements\\.md\\'" filename)
                       ;; Also activate for any markdown with Spectra headers
                       (and (string-match-p "\\.md\\'" filename)
                            (spectra--file-has-spectra-headers filename))))
  :priority 1
  :server-id 'spectra-lsp
  :initialization-options
  (lambda ()
    `(:spectra
      (:tracker
       (:type ,spectra-tracker-type
        :url ,spectra-tracker-url
        :projectKey ,spectra-project-key)
       :validation
       (:validateOnSave ,spectra-validate-on-save
        :validateOnType ,spectra-validate-on-type)
       :diagnostics
       (:showWarnings ,spectra-show-warnings
        :showHints t)
       :hover
       (:cacheTimeout ,spectra-hover-cache-timeout))))))

(defun spectra--file-has-spectra-headers (filename)
  "Check if FILENAME contains Spectra headers."
  (when (and filename (file-exists-p filename))
    (with-temp-buffer
      (insert-file-contents filename nil 0 2000)  ; Read first 2KB
      (goto-char (point-min))
      (re-search-forward "^##?\\s-*\\(Epic\\|Story\\|Subtask\\):" nil t))))

;; Add to lsp-language-id-configuration
(add-to-list 'lsp-language-id-configuration '(markdown-mode . "markdown"))
(add-to-list 'lsp-language-id-configuration '(spectra-mode . "markdown"))

;; Enable lsp for markdown files
(add-hook 'markdown-mode-hook #'lsp-deferred)

(provide 'spectra-lsp)
;;; spectra-lsp.el ends here
