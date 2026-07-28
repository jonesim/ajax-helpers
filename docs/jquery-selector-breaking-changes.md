# Breaking changes: jQuery selectors → native `querySelectorAll`

**Applies to:** django-ajax-helpers **0.0.23+** (the jQuery-removal release).
**Audience:** developers (and AI assistants) auditing a project that uses
django-ajax-helpers for selectors that will silently stop working after upgrading.

## What changed

Before 0.0.23 the client (`ajax_helpers.js`) resolved every selector through
jQuery, i.e. the **Sizzle** engine. Sizzle accepts a superset of CSS, including
custom pseudo-selectors (`:visible`, `:first`, `:contains(...)`, `:input`, …).

From 0.0.23 the client is vanilla JS. Every selector is resolved by the browser's
native `document.querySelectorAll`, via one helper — `query_all()` in
`ajax_helpers.js`:

```js
function query_all(selector) {
    var match = selector.match(/:(visible|hidden)\s*$/);   // ONLY a trailing :visible/:hidden
    if (match) { /* strip it, filter the native result by visibility */ }
    return document.querySelectorAll(selector);            // everything else: native CSS only
}
```

Consequences:

- **Native CSS selectors work unchanged** (`#id`, `.class`, `[attr=val]`,
  `:checked`, `:disabled`, `:not(.x)`, `:nth-child(n)`, `:first-child`, …).
- **`:visible` / `:hidden` still work — but only as the *final* token of the whole
  selector string.** `#toasts .toast:visible` is fine; `.toast:visible .body`,
  `.a:visible, .b`, or `.toast:hidden:first` are **not** (the pseudo isn't at the
  end, so it is handed to `querySelectorAll` and throws `SyntaxError`).
- **All other jQuery/Sizzle pseudo-selectors throw a `SyntaxError`** in
  `querySelectorAll`. The command aborts and the DOM update / event binding / count
  silently does not happen.

`is_visible()` treats an element as visible when it has layout boxes
(`offsetWidth || offsetHeight || getClientRects().length`), matching jQuery's
`:visible`. (Note: like jQuery, `visibility:hidden` / `opacity:0` elements still
count as *visible* because they occupy space.)

## Where selectors enter the library (audit these call sites)

**Server side (Python)** — the `selector` argument to any command:

```python
self.add_command('html', selector='#panel:visible', html=...)   # <-- audit these
self.command_response('remove', selector='.row:eq(0)')
ajax_command('set_value', selector=..., ...)
self.add_page_command('if_selector', selector=..., ...)
```

Commands that take a `selector`: `html`, `replace_with`, `append_to`, `remove`,
`set_value`, `set_attr`, `set_prop`, `set_css`, `focus`, `on`, `stop_propagation`,
`element_count`, `get_attr`, `if_selector`, `if_not_selector`, `send_form`,
`upload_file`.

**Client side (JS / templates)** — direct calls and template tags:

```js
ajax_helpers.upload_file('#file:input');   // selector string
```
```django
{% tooltip_init '.help:visible' 'my_fn' %}   {# NOTE: tooltip uses querySelectorAll directly — :visible/:hidden are NOT supported here at all #}
```

## jQuery-only selectors to search for, and their replacements

| jQuery / Sizzle (now broken)          | Native replacement |
|---------------------------------------|--------------------|
| `:first`                              | `:first-child` / `:first-of-type` (**not** identical) or take `[0]` in JS |
| `:last`                               | `:last-child` / `:last-of-type` or last element in JS |
| `:eq(n)` / `:gt(n)` / `:lt(n)`        | `:nth-child(n+1)` (careful: child vs match index differ) or slice in JS |
| `:even` / `:odd`                      | `:nth-child(odd)` / `:nth-child(even)` (child index, not match index) |
| `:contains('text')`                   | no CSS equivalent — filter in JS by `textContent` |
| `:input`                              | `input, select, textarea, button` |
| `:text` `:password` `:checkbox` `:radio` `:file` `:image` `:submit` `:reset` `:button` | `input[type=text]`, `input[type=checkbox]`, … |
| `:selected`                           | `option:checked` |
| `:header`                             | `h1, h2, h3, h4, h5, h6` |
| `:parent`                             | filter in JS (`el.children.length`) |
| `:visible` / `:hidden` **mid-selector or in a list** | move it to the **end**, or filter in JS |
| `:animated` `:focusable` `:tabbable`  | no equivalent — rewrite in JS |
| `[name!="x"]`                         | `:not([name="x"])` |

Still valid — **do not** flag these: `:checked`, `:disabled`, `:enabled`,
`:not(...)`, `:nth-child()`, `:first-child`, `:last-child`, `:only-child`,
`:focus`, `:required`, `:empty`, attribute selectors.

## Non-selector behavioural changes (related, worth checking)

- **Event delegation removed.** The `on` command binds listeners directly to the
  elements that match *at bind time*. jQuery-style live delegation (bind on a parent,
  match descendants added later) is not replicated — dynamically-added elements won't
  fire. Re-issue the `on` command after inserting new HTML.
- **Selectors must be strings.** Anywhere the old code accepted a jQuery object or a
  raw DOM node, pass a CSS selector string instead.
- **CSS-invalid ids/names must be escaped.** `querySelectorAll('#a.b')` reads `.b` as
  a class. Ids/names with `.`, `:`, spaces, or a leading digit — which jQuery
  tolerated — need `CSS.escape()` or an `[id="…"]` attribute selector.

## Search patterns for auditing a project (ripgrep)

Run from the project root. First pass — any jQuery-only pseudo anywhere:

```bash
rg -n --pcre2 \
  ":visible|:hidden|:first\b|:last\b|:eq\(|:gt\(|:lt\(|:even\b|:odd\b|:contains\(|:input\b|:selected\b|:checkbox\b|:radio\b|:header\b|:parent\b|:animated\b|\[[^\]]*!=" \
  -g '!**/jquery*' -g '!**/*.min.js'
```

Tighter pass — jQuery pseudos specifically inside an ajax-helpers `selector=` (Python)
or `selector:` (JSON/JS) value:

```bash
rg -n --pcre2 \
  "selector\s*[=:]\s*['\"][^'\"]*:(visible|hidden|first|last|eq|gt|lt|even|odd|contains|input|selected|checkbox|radio|header|parent|animated)" \
  -g '!**/*.min.js'
```

Review each hit against the table above. `:visible` / `:hidden` hits are only a
problem when the pseudo is **not** the last token of the selector (or when used in a
`tooltip_init` selector). Everything else in the pattern is a genuine break.
