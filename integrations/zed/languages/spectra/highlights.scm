; Spectra-specific highlighting for markdown files

; Epic headers
(atx_heading
  (atx_h1_marker)
  heading_content: (inline) @keyword.directive
  (#match? @keyword.directive "^Epic:"))

; Story headers
(atx_heading
  (atx_h2_marker)
  heading_content: (inline) @function
  (#match? @function "^Story:"))

; Subtask headers
(atx_heading
  (atx_h2_marker)
  heading_content: (inline) @function.method
  (#match? @function.method "^Subtask:"))

; Tracker IDs in brackets
(inline
  (text) @constant
  (#match? @constant "\\[[A-Z]+-[0-9]+\\]"))

; Status field
(paragraph
  (inline
    (strong_emphasis) @property
    (#match? @property "^\\*\\*Status\\*\\*")))

; Status values
(paragraph
  (inline) @string.special
  (#match? @string.special "(Todo|In Progress|In Review|Done|Blocked|Cancelled)$"))

; Priority field
(paragraph
  (inline
    (strong_emphasis) @property
    (#match? @property "^\\*\\*Priority\\*\\*")))

; Priority values
(paragraph
  (inline) @type
  (#match? @type "(Critical|High|Medium|Low)$"))

; Points field
(paragraph
  (inline
    (strong_emphasis) @property
    (#match? @property "^\\*\\*Points\\*\\*")))

; Points values
(paragraph
  (inline) @number
  (#match? @number "[0-9]+$"))

; Assignee field
(paragraph
  (inline
    (strong_emphasis) @property
    (#match? @property "^\\*\\*Assignee\\*\\*")))

; Labels field
(paragraph
  (inline
    (strong_emphasis) @property
    (#match? @property "^\\*\\*Labels\\*\\*")))

; Sprint field
(paragraph
  (inline
    (strong_emphasis) @property
    (#match? @property "^\\*\\*Sprint\\*\\*")))

; Acceptance Criteria header
(atx_heading
  heading_content: (inline) @keyword
  (#match? @keyword "^Acceptance Criteria"))

; Checkbox items
(list_item
  (task_list_marker_unchecked) @comment)

(list_item
  (task_list_marker_checked) @string.special)

; Issue references
(inline
  (text) @link
  (#match? @link "[A-Z][A-Z0-9]+-[0-9]+"))

; GitHub-style issue references
(inline
  (text) @link
  (#match? @link "#[0-9]+"))
