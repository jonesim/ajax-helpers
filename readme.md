[![PyPI version](https://badge.fury.io/py/django-ajax-helpers.svg)](https://badge.fury.io/py/django-ajax-helpers)

# Django Ajax Helpers

A Django library for building interactive AJAX-driven pages. Send commands from Django views to the browser and handle button clicks, tooltips, file uploads, and more — all without writing custom JavaScript.

## Installation

```bash
pip install django-ajax-helpers
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'ajax_helpers',
]
```

## Quick Start

### 1. Include the JavaScript

In your base template:

```html
{% load ajax_helpers %}
{% lib_include 'ajax_helpers' %}
```

This loads jQuery, Popper.js and the ajax_helpers JavaScript.

Alternatively, if you already have jQuery loaded:

```html
{% load ajax_helpers %}
{% init_ajax %}
```

### 2. Add the Mixin to Your View

```python
from ajax_helpers.mixins import AjaxHelpers

class MyView(AjaxHelpers, TemplateView):
    template_name = 'my_template.html'
```

### 3. Handle a Button Click

```python
class MyView(AjaxHelpers, TemplateView):
    template_name = 'my_template.html'

    def button_save(self, **kwargs):
        # Do something...
        return self.command_response('reload')
```

```html
{% load ajax_helpers %}
{% ajax_button "Save" "save" "primary" %}
```

Clicking the button sends an AJAX POST to the view which calls `button_save()`, and the returned `reload` command refreshes the page.

## How It Works

Ajax Helpers uses a **command pattern** — Django views return JSON arrays of command objects, which the JavaScript client executes in sequence.

```
Browser                              Django View
  │                                      │
  │  POST {button: "save"}               │
  ├─────────────────────────────────────►│
  │                                      │  button_save() called
  │  [{function: "reload"}]              │
  │◄─────────────────────────────────────┤
  │                                      │
  │  Executes: location.reload()         │
  └──────────────────────────────────────┘
```

---

## Python API

### `AjaxHelpers` Mixin

The core mixin for AJAX-enabled views. Mix it into any Django class-based view.

```python
from ajax_helpers.mixins import AjaxHelpers

class MyView(AjaxHelpers, TemplateView):
    ...
```

#### Command Methods

| Method | Description |
|--------|-------------|
| `add_command(function_name, **kwargs)` | Append a command to the response queue |
| `command_response(function_name=None, **kwargs)` | Add optional final command and return the `JsonResponse` |
| `add_page_command(function_name, **kwargs)` | Add a command that runs on page load |
| `get_page_commands()` | Override to return a list of page load commands |

**Building responses:**

```python
# Single command
return self.command_response('reload')

# Single command with parameters
return self.command_response('redirect', url='/dashboard/')

# Multiple commands
self.add_command('message', text='Saved!')
self.add_command('delay', time=1000)
return self.command_response('reload')

# Return accumulated commands without adding another
self.add_command('html', selector='#status', html='<b>Done</b>')
return self.command_response()
```

**Page load commands** (executed when the page first renders):

```python
def get_page_commands(self):
    return [
        ajax_command('on', selector='#my-input', event='keyup',
                     keys=['Enter'], commands=[
                         ajax_command('ajax_post', data={'button': 'search'})
                     ])
    ]
```

#### Request Routing

AJAX POST requests are automatically routed to handler methods based on the request data.

**Button handlers** — when the POST data contains `{button: "name"}`:

```python
def button_save(self, **kwargs):
    return self.command_response('reload')

def button_delete(self, pk, **kwargs):
    # pk comes from the POST data
    return self.command_response('message', text=f'Deleted {pk}')
```

**Tooltip handlers** — when the POST data contains `{tooltip: "name"}`:

```python
def tooltip_info(self, **kwargs):
    html = render_to_string('my_tooltip.html', kwargs)
    return HttpResponse(html)
```

**Timer handlers** — when the POST data contains `{timer: "name"}`:

```python
def timer_refresh(self, **kwargs):
    return self.command_response('html', selector='#count', html=str(get_count()))
```

**Ajax method handlers** — when the POST data contains `{ajax_method: "name"}`:

```python
from ajax_helpers.mixins import ajax_method

@ajax_method
def calculate(self, value1, value2):
    result = int(value1) + int(value2)
    return self.command_response('html', selector='#result', html=str(result))
```

Methods must be decorated with `@ajax_method` to be callable via this route.

**Custom command types** — extend `ajax_commands` to add your own routing:

```python
class MyView(AjaxHelpers, TemplateView):
    ajax_commands = ['button', 'tooltip', 'timer', 'ajax', 'action']

    def action_archive(self, **kwargs):
        # Called when POST contains {action: "archive"}
        ...
```

### `ajax_command()` Utility

Build command dicts for use with `add_command()` or in nested command lists.

```python
from ajax_helpers.utils import ajax_command

cmd = ajax_command('html', selector='#content', html='<p>Hello</p>')
# Returns: {'function': 'html', 'selector': '#content', 'html': '<p>Hello</p>'}
```

### `toast_commands()` Utility

Generate commands to show a Bootstrap toast notification.

```python
from ajax_helpers.utils import toast_commands

self.add_command(toast_commands(
    text='Record saved successfully',
    header='Success',
    position='top-right',      # top-left, top-right, bottom-left, bottom-right
    auto_hide=True,
    delay=4000,
    font_awesome='fas fa-check',
))
return self.command_response()
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `text` | *required* | Toast body text |
| `header` | `None` | Toast header text |
| `header_small` | `None` | Small text in header |
| `position` | `'bottom-right'` | Corner position |
| `auto_hide` | `True` | Auto-dismiss the toast |
| `delay` | `4000` | Milliseconds before auto-hide |
| `font_awesome` | `None` | Icon class for header |
| `template_name` | `'ajax_helpers/toast.html'` | Override toast template |
| `header_classes` | `''` | Extra CSS classes for header |
| `body_classes` | `''` | Extra CSS classes for body |

### `is_ajax()` Utility

Check if a request is an AJAX request.

```python
from ajax_helpers.utils import is_ajax

if is_ajax(request):
    ...
```

---

## JavaScript Commands Reference

Commands are sent from Python and executed in the browser. Use them with `command_response()` or `add_command()`.

### Page Navigation

#### `reload`
Reload the current page.

```python
return self.command_response('reload')
```

#### `redirect`
Navigate to a URL, optionally in a new tab.

```python
# Same tab
return self.command_response('redirect', url='/dashboard/')

# New tab
return self.command_response('redirect', url='/report/', new_tab=True)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | The URL to navigate to |
| `new_tab` | bool | If truthy, opens in a new browser tab |

### DOM Manipulation

#### `html`
Set the inner HTML of an element.

```python
self.add_command('html', selector='#content', html='<p>Updated</p>')
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `selector` | string | jQuery selector |
| `html` | string | HTML content to set |
| `parent` | bool | If `True`, targets the parent element |

#### `replace_with`
Replace element(s) with new HTML.

```python
self.add_command('replace_with', selector='#old-row', html='<tr>...</tr>')
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `selector` | string | jQuery selector |
| `html` | string | Replacement HTML |
| `parent` | bool | If `True`, replaces the parent element |

#### `append_to`
Append HTML as a child of the target element.

```python
self.add_command('append_to', selector='#list', html='<li>New item</li>')
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `selector` | string | jQuery selector for the container |
| `html` | string | HTML to append |

#### `remove`
Remove element(s) from the DOM.

```python
self.add_command('remove', selector='#obsolete')
```

### Element Properties

#### `set_value`
Set the value of an input element.

```python
self.add_command('set_value', selector='#my-input', val='Hello')
```

#### `set_attr`
Set an HTML attribute.

```python
self.add_command('set_attr', selector='#link', attr='href', val='/new-url/')
```

#### `set_prop`
Set a DOM property.

```python
self.add_command('set_prop', selector='#checkbox', prop='checked', val=True)
```

#### `set_css`
Set a CSS property.

```python
self.add_command('set_css', selector='#box', prop='background-color', val='red')
```

#### `focus`
Set focus on an element.

```python
self.add_command('focus', selector='#name-input')
```

### User Feedback

#### `message`
Show a browser alert dialog.

```python
return self.command_response('message', text='Something went wrong')
```

#### `console_log`
Log a message to the browser console.

```python
self.add_command('console_log', text='Debug: value is 42')
```

#### `clipboard`
Copy text to the clipboard.

```python
return self.command_response('clipboard', text='Copied content')
```

### Timing

#### `delay`
Pause command processing for a given time. Sets `ajax_busy` to prevent overlapping requests.

```python
self.add_command('delay', time=500)
self.add_command('reload')
return self.command_response()
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `time` | int | Milliseconds to delay |

#### `timeout`
Execute nested commands after a delay.

```python
return self.command_response('timeout', time=2000, commands=[
    ajax_command('message', text='2 seconds later!')
])
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `time` | int | Milliseconds to wait |
| `commands` | list | Commands to execute after the delay |

#### `timer`
Execute nested commands repeatedly at an interval.

```python
self.add_page_command('timer', interval=5000, commands=[
    ajax_command('ajax_post', url='/api/status/', data={'timer': 'refresh'})
], store='status_timer')
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `interval` | int | Milliseconds between executions |
| `commands` | list | Commands to execute each interval |
| `always` | bool | Run even when the tab is not visible |
| `store` | string | Name for the timer (for later clearing) |

#### `clear_timers`
Stop all timers stored under a given name.

```python
self.add_command('clear_timers', store='status_timer')
```

### Conditional Execution

#### `if_selector`
Execute commands if a selector matches elements (optionally checking visibility).

```python
self.add_command('if_selector', selector='#panel', commands=[
    ajax_command('html', selector='#panel', html='Updated')
], else_commands=[
    ajax_command('console_log', text='Panel not found')
])
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `selector` | string | jQuery selector to test |
| `commands` | list | Commands if selector matches |
| `else_commands` | list | Commands if selector does not match |
| `is_visible` | bool | Also require the element to be visible |

#### `if_not_selector`
Execute commands if a selector does **not** match (inverse of `if_selector`).

```python
self.add_command('if_not_selector', selector='#toast-container', commands=[
    ajax_command('append_to', selector='body', html='<div id="toast-container"></div>')
])
```

### Event Binding

#### `on`
Bind an event handler that executes commands.

```python
self.add_page_command('on', selector='#search', event='keyup',
    keys=['Enter'], prevent_default=True, commands=[
        ajax_command('ajax_post', data={'button': 'search'})
    ]
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `selector` | string | jQuery selector |
| `event` | string | DOM event name (e.g. `'click'`, `'keyup'`) |
| `commands` | list | Commands to execute on event |
| `keys` | list | Only trigger for these key values (for keyboard events) |
| `prevent_default` | bool | Call `e.preventDefault()` |

#### `stop_propagation`
Prevent event propagation on an element.

```python
self.add_page_command('stop_propagation', selector='.inner-btn', event='click')
```

### AJAX Requests

#### `ajax_post`
Send a JSON POST request to a URL.

```python
self.add_command('ajax_post', url='/api/action/', data={'key': 'value'})
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | Target URL |
| `data` | dict | JSON data to send |

#### `send_form`
Submit a form via AJAX.

```python
self.add_command('send_form', form_id='my-form')
```

### File Operations

#### `save_file`
Trigger a file download from base64-encoded data.

```python
import base64
data = base64.b64encode(file_bytes).decode()
return self.command_response('save_file', data=data, filename='report.pdf')
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | string | Base64-encoded file content |
| `filename` | string | Download filename |

#### `upload_file`
Used internally by the file upload system. See [File Uploads](#file-uploads).

### Data Retrieval

#### `element_count`
Count matching elements and POST the count back to a URL.

```python
self.add_command('element_count', selector='.item', data={'type': 'items'}, url='/api/count/')
```

#### `get_attr`
Get an element's attribute value and POST it back to a URL.

```python
self.add_command('get_attr', selector='#target', attr='data-id', data={}, url='/api/receive/')
```

### WebSocket

#### `start_websocket`
Open a WebSocket connection. See [WebSockets](#websockets).

```python
self.add_page_command('start_websocket', ws_url='/helpers/gn-my_channel/')
```

### No-op

#### `null`
Do nothing. Useful as a placeholder response.

```python
return self.command_response('null')
```

---

## Template Tags

Load with `{% load ajax_helpers %}`.

### `{% lib_include %}`
Include CSS and JavaScript libraries.

```html
{% lib_include 'ajax_helpers' %}
```

Options: `cdn=True/False`, `module=True/False`, `version='x.y.z'`.

### `{% init_ajax %}`
Include just the ajax_helpers.js script (when you already have jQuery loaded).

```html
{% init_ajax %}
```

### `{% ajax_button %}`
Render a button that sends a button command via AJAX.

```html
{% ajax_button "Save" "save" "primary" %}
{% ajax_button "Delete" "delete" css_class="btn btn-sm btn-danger" %}
```

Arguments: `text`, `name`, `bootstrap_style` (default `'primary'`), `css_class` (overrides bootstrap_style). Extra kwargs are passed as POST data.

### `{% ajax_method_button %}`
Render a button that calls an `@ajax_method`.

```html
{% ajax_method_button "Calculate" "calculate" "success" value1="10" value2="20" %}
```

### `{% button_javascript %}`
Output just the JavaScript for a button click (for use in custom `onclick` handlers).

```html
<button class="btn btn-primary" onclick='{% button_javascript "save" pk=object.pk %}'>Save</button>
```

### `{% post_json_js %}`
Output JavaScript for posting JSON data. Supports named URLs and blob responses.

```html
<button onclick='{% post_json_js url_name="my_api" blob=True action="export" %}'>Export</button>
```

### `{% send_form %}`
Output JavaScript to submit a form via AJAX.

```html
<button onclick='{% send_form "my_form" extra_param="value" %}'>Submit</button>
```

### `{% send_form_button %}`
Render a button that submits a form.

```html
{% send_form_button "Submit" "my_form" "success" %}
```

### `{% upload_file %}`
Render a file upload widget with optional drag-and-drop and progress bar.

```html
{% upload_file "Choose File" "primary" drag_drop="default" progress=True %}
{% upload_file text="Upload" width="200px" height="100px" %}
```

| Argument | Default | Description |
|----------|---------|-------------|
| `text` | `'Upload File'` | Button text |
| `bootstrap_style` | `'primary'` | Bootstrap button style |
| `css_class` | `None` | Override CSS class |
| `drag_drop` | `None` | Enable drag-and-drop (set to `'default'`) |
| `width` | `None` | Drag-drop zone width |
| `height` | `None` | Drag-drop zone height |
| `progress` | `False` | Show progress bar |

### `{% tooltip_init %}`
Initialise AJAX-loaded tooltips on elements.

```html
{% tooltip_init '.has-tooltip' 'info' 'bottom' %}
```

Arguments: `selector`, `function_name`, `placement` (optional), `template` (optional).

### `{% ajax_timer %}`
Set up a periodic timer that POSTs to the view.

```html
{% ajax_timer "refresh" 5000 %}
```

Arguments: `name`, `interval_ms`.

---

## File Uploads

Use `AjaxFileUploadMixin` for uploading files with progress tracking.

### View Setup

```python
from ajax_helpers.mixins import AjaxHelpers, AjaxFileUploadMixin

class MyUploadView(AjaxFileUploadMixin, AjaxHelpers, TemplateView):
    template_name = 'upload.html'

    def upload_files(self, name, size, file, **kwargs):
        # Called for each uploaded file
        # name: original filename
        # size: file size in bytes
        # file: Django UploadedFile
        save_uploaded_file(file, name)

    def upload_completed(self):
        self.add_command('message', text='All files uploaded')
        return self.command_response('reload')
```

### Template

```html
{% load ajax_helpers %}
{% upload_file "Upload Files" "primary" progress=True %}
```

### Drag and Drop

```html
{% upload_file "Drop files here" drag_drop="default" width="300px" height="200px" progress=True %}
```

### Configuration

| Attribute | Default | Description |
|-----------|---------|-------------|
| `upload_key` | `'ajax_modal_file'` | Form field name for uploaded file |
| `single_progress_bar` | `True` | Use one progress bar for all files |

---

## Celery Task Integration

Use `AjaxTaskMixin` to start Celery tasks and poll for results.

```python
from ajax_helpers.mixins import AjaxHelpers, AjaxTaskMixin
from myapp.tasks import generate_report

class ReportView(AjaxTaskMixin, AjaxHelpers, TemplateView):
    template_name = 'report.html'
    tasks = {'report': generate_report}
    refresh_ms = 1000  # poll every second (default: 600ms)

    def button_generate(self, **kwargs):
        return self.start_task('report', task_kwargs={'user_id': self.request.user.id})

    def task_state_success(self, task_result, task_name, **kwargs):
        self.add_command('message', text='Report ready!')
        return self.command_response('reload')

    def task_state_failure(self, task_result, task_name, **kwargs):
        return self.command_response('message', text='Report generation failed')

    def task_progress(self, info):
        # Called on each poll while task is running
        # info is task_result.info (dict)
        if 'percent' in info:
            self.add_command('set_css', selector='#progress', prop='width', val=f'{info["percent"]}%')
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `tasks` | `{}` | Dict mapping task names to Celery task classes |
| `refresh_ms` | `600` | Polling interval in milliseconds |

Override methods:
- `task_state_success(task_result, task_name, **kwargs)` — task completed
- `task_state_failure(task_result, task_name, **kwargs)` — task failed
- `task_state_revoked(task_result, task_name, **kwargs)` — task was revoked
- `task_progress(info)` — called on each poll while pending/running

---

## WebSockets

Push commands to the browser in real time using Django Channels.

### Consumer

```python
from ajax_helpers.websockets.consumers import ConsumerHelper

class NotificationConsumer(ConsumerHelper):

    def connect_commands(self):
        # Sent to client on connection
        self.add_command('message', text='Connected')

    def receive(self, text_data=None, bytes_data=None):
        # Handle messages from the client
        pass
```

### Routing

```python
# routing.py
from django.urls import path
from ajax_helpers.websockets.routing import websocket_urlpatterns

# Or define your own:
websocket_urlpatterns = [
    path('ws/notifications/<str:slug>/', NotificationConsumer.as_asgi()),
]
```

### View Mixin

Send WebSocket commands from a Django view:

```python
from ajax_helpers.websockets.mixin import WebsocketHelpers

class MyView(WebsocketHelpers, AjaxHelpers, TemplateView):
    template_name = 'my_template.html'

    def get_page_commands(self):
        self.add_channel('notifications')
        return super().get_page_commands()

    def button_notify(self, **kwargs):
        self.send_ws_commands('notifications', 'html',
                              selector='#status', html='<b>Updated!</b>')
        return self.command_response('null')
```

### Celery Task

Send WebSocket commands from a background task:

```python
from ajax_helpers.websockets.tasks import TaskHelper

class NotifyTask(TaskHelper):
    def run(self, channel_name, message):
        self.send_ws_commands(channel_name, 'message', text=message)
```

---

## JavaScript API

The `ajax_helpers` object is available globally for direct use in templates and scripts.

### `ajax_helpers.post_json(data)`

Send a JSON POST request to the current page (or a specified URL).

```javascript
// Simple button post
ajax_helpers.post_json({data: {button: 'save', pk: 42}})

// Post to a specific URL
ajax_helpers.post_json({url: '/api/action/', data: {action: 'run'}})

// With blob response (for file downloads)
ajax_helpers.post_json({data: {button: 'export'}, response_type: 'blob'})

// Custom success handler
ajax_helpers.post_json({data: {button: 'check'}, success: function(data) { console.log(data) }})
```

### `ajax_helpers.send_form(form_id, extra_data)`

Submit a form as `FormData` via AJAX POST.

```javascript
ajax_helpers.send_form('my-form', {extra_field: 'value'})
```

### `ajax_helpers.post_data(url, data, timeout, options)`

POST `FormData` to a URL with optional progress tracking.

```javascript
ajax_helpers.post_data('/upload/', formData, 0, {
    progress: {selector: '#progress-bar'}
})
```

### `ajax_helpers.get_content(url)`

Load a page via AJAX and push to browser history (SPA-style navigation).

```javascript
ajax_helpers.get_content('/dashboard/')
```

### `ajax_helpers.process_commands(commands)`

Execute an array of command objects. Commands are queued if `ajax_busy` is true.

```javascript
ajax_helpers.process_commands([
    {function: 'html', selector: '#msg', html: 'Hello'},
    {function: 'focus', selector: '#input'}
])
```

### `ajax_helpers.tooltip(selector, function_name, placement, template)`

Initialise lazy-loaded tooltips that fetch content from the server on hover.

```javascript
ajax_helpers.tooltip('.info-icon', 'details', 'bottom')
```

### `ajax_helpers.set_ajax_busy(status, pointer_wait)`

Control the busy flag and optional wait cursor.

```javascript
ajax_helpers.set_ajax_busy(true, true)   // busy + wait cursor
ajax_helpers.set_ajax_busy(false, true)  // not busy, remove wait cursor
```

### `ajax_helpers.upload_file(selector, upload_params)`

Initiate a file upload from a file input.

```javascript
ajax_helpers.upload_file('#file-input', {category: 'documents'})
```

### `ajax_helpers.file_info(selector)`

Get file metadata from a file input.

```javascript
var files = ajax_helpers.file_info('#file-input')
// [{name: 'doc.pdf', size: 12345}, ...]
```

### `ajax_helpers.drag_drop(container_id, upload_params)`

Enable drag-and-drop file uploads on a container element.

```javascript
ajax_helpers.drag_drop('#drop-zone', {category: 'images'})
```

### `ajax_helpers.command_functions`

The command function registry. Add custom commands:

```javascript
ajax_helpers.command_functions.my_command = function(command) {
    console.log('Custom command:', command.data);
};
```

Then from Python:

```python
self.add_command('my_command', data='hello')
```

---

## CSS Classes

| Class | Description |
|-------|-------------|
| `html.wait` | Wait cursor on the entire page (set via `set_ajax_busy`) |
| `.drag_highlight` | Light blue background applied during drag-over |
| `.upload-dropzone` | Styled drag-and-drop zone |
| `.toast-danger`, `.toast-primary`, etc. | Bootstrap toast colour variants |

---

## License

MIT
