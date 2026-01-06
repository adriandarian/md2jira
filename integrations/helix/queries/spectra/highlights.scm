; Spectra-specific highlighting for Helix
; Place in ~/.config/helix/runtime/queries/spectra/highlights.scm

; Inherit from markdown
(document) @text

; Epic headers (# Epic: Title)
(atx_heading
  (atx_h1_marker) @punctuation.special
  heading_content: (inline) @keyword.directive
  (#match? @keyword.directive "^Epic:"))

; Story headers (## Story: Title)
(atx_heading
  (atx_h2_marker) @punctuation.special
  heading_content: (inline) @function
  (#match? @function "^Story:"))

; Subtask headers (## Subtask: Title)
(atx_heading
  (atx_h2_marker) @punctuation.special
  heading_content: (inline) @function.method
  (#match? @function.method "^Subtask:"))

; Tracker IDs in brackets like [PROJ-123]
((inline) @constant
  (#match? @constant "\\[[A-Z][A-Z0-9]*-[0-9]+\\]"))

; GitHub-style issue refs like #123
((inline) @constant
  (#match? @constant "#[0-9]+"))

; Metadata fields (**Status**, **Priority**, etc.)
(strong_emphasis) @property

; Status values
((paragraph) @string.special
  (#match? @string.special "(Todo|In Progress|In Review|Done|Blocked|Cancelled)"))

; Priority values
((paragraph) @type
  (#match? @type "(Critical|High|Medium|Low)"))

; Acceptance Criteria header
(atx_heading
  heading_content: (inline) @label
  (#match? @label "Acceptance Criteria"))

; Checkbox task items
(task_list_marker_unchecked) @comment
(task_list_marker_checked) @string.special

; Code blocks
(fenced_code_block) @markup.raw.block
(code_span) @markup.raw.inline

; Links
(link_text) @markup.link.text
(link_destination) @markup.link.url

; Emphasis
(emphasis) @markup.italic
(strong_emphasis) @markup.bold

; Block quotes
(block_quote) @markup.quote
