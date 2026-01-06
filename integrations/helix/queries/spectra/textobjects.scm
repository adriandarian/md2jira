; Text objects for Spectra documents
; Place in ~/.config/helix/runtime/queries/spectra/textobjects.scm

; Function/method = Story/Subtask
(atx_heading
  heading_content: (inline) @function.inside
  (#match? @function.inside "^(Story|Subtask):")) @function.around

; Class = Epic
(atx_heading
  heading_content: (inline) @class.inside
  (#match? @class.inside "^Epic:")) @class.around

; Parameter = Metadata fields
(paragraph
  (inline
    (strong_emphasis) @parameter.inside)) @parameter.around

; Comment = Block quotes
(block_quote) @comment.around
(block_quote (paragraph) @comment.inside)

; Entry = List items (for acceptance criteria)
(list_item) @entry.around
(list_item (paragraph) @entry.inside)
