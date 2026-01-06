;;; spectra-mode.el --- Major mode for Spectra markdown files -*- lexical-binding: t; -*-

;; Copyright (C) 2024 Spectra Contributors

;; Author: Spectra Contributors
;; Keywords: languages, tools, markdown
;; URL: https://github.com/spectra/spectra
;; Version: 0.1.0
;; Package-Requires: ((emacs "27.1") (markdown-mode "2.5"))

;;; Commentary:

;; A major mode for editing Spectra markdown user story files.
;; Derived from markdown-mode with additional highlighting and commands.

;;; Code:

(require 'markdown-mode)

(defgroup spectra-mode nil
  "Major mode for Spectra markdown files."
  :group 'spectra
  :prefix "spectra-mode-")

;; Font-lock keywords for Spectra-specific syntax
(defvar spectra-font-lock-keywords
  `(
    ;; Epic headers
    ("^#\\s-*Epic:\\s-*\\(.+\\)$"
     (0 'markdown-header-face-1)
     (1 'font-lock-keyword-face t))

    ;; Story headers
    ("^##\\s-*Story:\\s-*\\(.+?\\)\\(\\s-*\\[\\([^]]+\\)\\]\\)?$"
     (0 'markdown-header-face-2)
     (1 'font-lock-function-name-face t)
     (3 'font-lock-constant-face t t))

    ;; Subtask headers
    ("^##\\s-*Subtask:\\s-*\\(.+?\\)\\(\\s-*\\[\\([^]]+\\)\\]\\)?$"
     (0 'markdown-header-face-2)
     (1 'font-lock-type-face t)
     (3 'font-lock-constant-face t t))

    ;; Metadata fields
    ("^\\*\\*\\(Status\\|Priority\\|Points\\|Assignee\\|Labels\\|Sprint\\)\\*\\*:"
     (1 'font-lock-builtin-face))

    ;; Status values
    ("\\<\\(Todo\\|In Progress\\|In Review\\|Done\\|Blocked\\|Cancelled\\)\\>"
     (1 'font-lock-string-face))

    ;; Priority values
    ("\\<\\(Critical\\|High\\|Medium\\|Low\\)\\>"
     (1 'font-lock-warning-face))

    ;; Tracker IDs
    ("\\<[A-Z][A-Z0-9]+-[0-9]+\\>"
     (0 'font-lock-constant-face))

    ;; GitHub-style issue references
    ("#[0-9]+"
     (0 'font-lock-constant-face))

    ;; Acceptance Criteria header
    ("^###\\s-*Acceptance Criteria"
     (0 'font-lock-keyword-face)))
  "Font-lock keywords for Spectra mode.")

;; Imenu support for navigation
(defvar spectra-imenu-generic-expression
  '(("Epics" "^#\\s-*Epic:\\s-*\\(.+\\)$" 1)
    ("Stories" "^##\\s-*Story:\\s-*\\(.+?\\)\\(?:\\s-*\\[.+\\]\\)?$" 1)
    ("Subtasks" "^##\\s-*Subtask:\\s-*\\(.+?\\)\\(?:\\s-*\\[.+\\]\\)?$" 1))
  "Imenu expressions for Spectra mode.")

;; Outline support
(defvar spectra-outline-regexp "^##?\\s-*\\(Epic\\|Story\\|Subtask\\):"
  "Regexp for Spectra outline headings.")

;;;###autoload
(define-derived-mode spectra-mode markdown-mode "Spectra"
  "Major mode for editing Spectra markdown user story files.

Derived from `markdown-mode' with additional highlighting and
navigation for Spectra-specific elements like Epics, Stories,
and Subtasks.

\\{spectra-mode-map}"
  :group 'spectra-mode

  ;; Add Spectra-specific font-lock
  (font-lock-add-keywords nil spectra-font-lock-keywords t)

  ;; Setup imenu
  (setq-local imenu-generic-expression spectra-imenu-generic-expression)

  ;; Setup outline
  (setq-local outline-regexp spectra-outline-regexp)

  ;; Enable features
  (outline-minor-mode 1))

;; Key bindings
(define-key spectra-mode-map (kbd "C-c s v") #'spectra-validate)
(define-key spectra-mode-map (kbd "C-c s s") #'spectra-sync)
(define-key spectra-mode-map (kbd "C-c s p") #'spectra-plan)
(define-key spectra-mode-map (kbd "C-c s d") #'spectra-diff)
(define-key spectra-mode-map (kbd "C-c s i") #'spectra-import)
(define-key spectra-mode-map (kbd "C-c s o") #'spectra-open-in-tracker)
(define-key spectra-mode-map (kbd "C-c s n") #'spectra-new-story)

;; Auto-mode for Spectra files
;;;###autoload
(add-to-list 'auto-mode-alist '("\\.spectra\\.md\\'" . spectra-mode))
;;;###autoload
(add-to-list 'auto-mode-alist '("user-stories\\.md\\'" . spectra-mode))
;;;###autoload
(add-to-list 'auto-mode-alist '("backlog\\.md\\'" . spectra-mode))

(provide 'spectra-mode)
;;; spectra-mode.el ends here
