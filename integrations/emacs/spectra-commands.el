;;; spectra-commands.el --- Interactive commands for Spectra -*- lexical-binding: t; -*-

;; Copyright (C) 2024 Spectra Contributors

;; Author: Spectra Contributors
;; Keywords: languages, tools, markdown
;; URL: https://github.com/spectra/spectra
;; Version: 0.1.0
;; Package-Requires: ((emacs "27.1"))

;;; Commentary:

;; Interactive commands for working with Spectra markdown files.
;; These commands invoke the Spectra CLI tool.

;;; Code:

(require 'compile)

(defcustom spectra-cli-path "spectra"
  "Path to the Spectra CLI executable."
  :type 'string
  :group 'spectra)

(defun spectra--run-command (args &optional buffer-name)
  "Run Spectra CLI with ARGS and display output in BUFFER-NAME."
  (let ((default-directory (or (locate-dominating-file default-directory "spectra.yaml")
                               (locate-dominating-file default-directory "spectra.toml")
                               default-directory))
        (buf-name (or buffer-name "*Spectra*")))
    (compile (concat spectra-cli-path " " args) t)
    (with-current-buffer "*compilation*"
      (rename-buffer buf-name t))))

(defun spectra--current-file ()
  "Return the current buffer's file name."
  (or buffer-file-name
      (error "Buffer is not visiting a file")))

;;;###autoload
(defun spectra-validate ()
  "Validate the current Spectra markdown file."
  (interactive)
  (save-buffer)
  (spectra--run-command
   (format "--validate --markdown %s" (shell-quote-argument (spectra--current-file)))
   "*Spectra Validate*"))

;;;###autoload
(defun spectra-sync ()
  "Sync the current file to the issue tracker."
  (interactive)
  (save-buffer)
  (when (yes-or-no-p "Sync this file to the tracker? ")
    (spectra--run-command
     (format "--sync --markdown %s" (shell-quote-argument (spectra--current-file)))
     "*Spectra Sync*")))

;;;###autoload
(defun spectra-plan ()
  "Show what changes would be made without syncing (like terraform plan)."
  (interactive)
  (save-buffer)
  (spectra--run-command
   (format "plan --markdown %s" (shell-quote-argument (spectra--current-file)))
   "*Spectra Plan*"))

;;;###autoload
(defun spectra-diff ()
  "Show diff between local file and tracker state."
  (interactive)
  (save-buffer)
  (spectra--run-command
   (format "diff --markdown %s" (shell-quote-argument (spectra--current-file)))
   "*Spectra Diff*"))

;;;###autoload
(defun spectra-import ()
  "Import stories from tracker to create a new markdown file."
  (interactive)
  (let ((output-file (read-file-name "Save imported stories to: " nil nil nil "stories.md")))
    (spectra--run-command
     (format "import --output %s" (shell-quote-argument output-file))
     "*Spectra Import*")))

;;;###autoload
(defun spectra-export (format)
  "Export the current file to FORMAT (html, pdf, docx, json)."
  (interactive
   (list (completing-read "Export format: " '("html" "pdf" "docx" "json" "csv"))))
  (save-buffer)
  (let* ((input-file (spectra--current-file))
         (base-name (file-name-sans-extension input-file))
         (output-file (concat base-name "." format)))
    (spectra--run-command
     (format "export --markdown %s --format %s --output %s"
             (shell-quote-argument input-file)
             format
             (shell-quote-argument output-file))
     "*Spectra Export*")))

;;;###autoload
(defun spectra-open-in-tracker ()
  "Open the story at point in the issue tracker."
  (interactive)
  (save-excursion
    (beginning-of-line)
    (if (re-search-forward "\\[\\([A-Z][A-Z0-9]*-[0-9]+\\)\\]" (line-end-position) t)
        (let ((issue-id (match-string 1)))
          (spectra--run-command
           (format "open %s" issue-id)
           "*Spectra Open*"))
      (if (re-search-forward "#\\([0-9]+\\)" (line-end-position) t)
          (let ((issue-num (match-string 1)))
            (spectra--run-command
             (format "open #%s" issue-num)
             "*Spectra Open*"))
        (message "No issue ID found at point")))))

;;;###autoload
(defun spectra-new-story ()
  "Insert a new story template at point."
  (interactive)
  (let ((title (read-string "Story title: ")))
    (insert (format "\n## Story: %s
**Status**: Todo
**Priority**: Medium
**Points**:

### Description

TODO: Add description

### Acceptance Criteria
- [ ]

" title))))

;;;###autoload
(defun spectra-new-epic ()
  "Insert a new epic template at point."
  (interactive)
  (let ((title (read-string "Epic title: ")))
    (insert (format "\n# Epic: %s

TODO: Add epic description

" title))))

;;;###autoload
(defun spectra-new-subtask ()
  "Insert a new subtask template at point."
  (interactive)
  (let ((title (read-string "Subtask title: ")))
    (insert (format "\n## Subtask: %s
**Status**: Todo

" title))))

;;;###autoload
(defun spectra-stats ()
  "Show statistics for the current file."
  (interactive)
  (save-buffer)
  (spectra--run-command
   (format "stats --markdown %s" (shell-quote-argument (spectra--current-file)))
   "*Spectra Stats*"))

;;;###autoload
(defun spectra-doctor ()
  "Run diagnostics on the Spectra setup."
  (interactive)
  (spectra--run-command "doctor" "*Spectra Doctor*"))

;; Hydra menu (optional, requires hydra package)
(with-eval-after-load 'hydra
  (defhydra spectra-hydra (:color blue :hint nil)
    "
Spectra Commands
────────────────
_v_: Validate    _s_: Sync       _p_: Plan
_d_: Diff        _i_: Import     _o_: Open in Tracker
_e_: Export      _r_: Report     _t_: Stats
_n_: New Story   _E_: New Epic   _T_: New Subtask
_D_: Doctor      _q_: Quit
"
    ("v" spectra-validate)
    ("s" spectra-sync)
    ("p" spectra-plan)
    ("d" spectra-diff)
    ("i" spectra-import)
    ("o" spectra-open-in-tracker)
    ("e" spectra-export)
    ("r" (spectra--run-command "report" "*Spectra Report*"))
    ("t" spectra-stats)
    ("n" spectra-new-story)
    ("E" spectra-new-epic)
    ("T" spectra-new-subtask)
    ("D" spectra-doctor)
    ("q" nil))

  (with-eval-after-load 'spectra-mode
    (define-key spectra-mode-map (kbd "C-c s h") #'spectra-hydra/body)))

(provide 'spectra-commands)
;;; spectra-commands.el ends here
