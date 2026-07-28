if (typeof ajax_helpers === 'undefined') {
    var ajax_helpers = function () {
        var drag_drop_files = [];
        var window_location = window.location;
        var ajax_busy = false;
        var set_intervals = {}

        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        function is_visible(el) {
            return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
        }

        // querySelectorAll that understands jQuery's :visible / :hidden pseudo
        // selectors (used by e.g. toast_commands), which native CSS does not.
        function query_all(selector) {
            var visibility = null;
            var match = selector.match(/:(visible|hidden)\s*$/);
            if (match) {
                visibility = match[1];
                selector = selector.slice(0, match.index);
            }
            var nodes = Array.prototype.slice.call(document.querySelectorAll(selector));
            if (visibility === 'visible') {
                return nodes.filter(is_visible);
            }
            if (visibility === 'hidden') {
                return nodes.filter(function (el) { return !is_visible(el); });
            }
            return nodes;
        }

        function on_ready(fn) {
            if (document.readyState !== 'loading') {
                fn();
            } else {
                document.addEventListener('DOMContentLoaded', fn);
            }
        }

        // Re-create <script> elements so the browser executes them. innerHTML does
        // not run scripts, but jQuery's .html()/.append()/.replaceWith() did, and
        // command responses (toasts, modals, page-load scripts) rely on it.
        function activate_scripts(node) {
            var scripts = [];
            if (node.tagName === 'SCRIPT') {
                scripts.push(node);
            }
            if (node.querySelectorAll) {
                node.querySelectorAll('script').forEach(function (s) {
                    scripts.push(s);
                });
            }
            scripts.forEach(function (old) {
                var s = document.createElement('script');
                for (var i = 0; i < old.attributes.length; i++) {
                    s.setAttribute(old.attributes[i].name, old.attributes[i].value);
                }
                s.text = old.textContent;
                old.parentNode.replaceChild(s, old);
            });
        }

        function set_html(target, html) {
            target.innerHTML = html;
            activate_scripts(target);
        }

        function ajax_error() {
            document.documentElement.classList.remove('wait');
            ajax_helpers.ajax_busy = false;
        }

        function send_form(form_id, extra_data, timeout, options) {
            if (timeout === undefined) {
                var timeout = 0
            }
            var data;
            if (form_id != null) {
                var form = document.getElementById(form_id);
                data = new FormData(form);
            } else {
                data = new FormData();
            }
            if (extra_data !== 'undefined') {
                for (var property in extra_data) {
                    data.append(property, extra_data[property]);
                }
            }
            ajax_helpers.post_data(ajax_helpers.window_location, data, timeout, options);
        }

        function contains_file(xhr) {
            var content_disposition = xhr.getResponseHeader('Content-Disposition');
            return typeof (content_disposition) == 'string' && content_disposition.indexOf('attachment') > -1;
        }

        function add_CSRF(xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }

        function download_blob(filename, blob) {
            if (navigator.msSaveOrOpenBlob) {
                navigator.msSaveOrOpenBlob(blob, filename);
            } else {
                var download_url = window.URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.style.display = 'none';
                a.href = download_url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                setTimeout(function(){ window.URL.revokeObjectURL(download_url); }, 3000);
            }
        }

        function download_file(xhr, response) {
            var filename, blob;
            var content_disposition = xhr.getResponseHeader('Content-Disposition');
            var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            var matches = filenameRegex.exec(content_disposition);
            if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
            if (typeof (response) === 'object') {
                blob = response;
            } else {
                blob = new Blob([response], {type: "octet/stream"});
            }
            download_blob(filename, blob);
            setTimeout(function(){ alert('your file has downloaded') }, 100);
        }

        // Reads a fetch Response body in the same way jQuery auto-detected it:
        // attachment -> blob, application/json -> parsed object, otherwise text.
        function dispatch_fetch(response, success, response_type) {
            var headers = response.headers;
            var fake_xhr = {
                getResponseHeader: function (name) {
                    return headers.get(name);
                }
            };
            var content_disposition = headers.get('Content-Disposition');
            var is_file = typeof content_disposition === 'string' && content_disposition.indexOf('attachment') > -1;
            var content_type = headers.get('Content-Type') || '';
            var body_promise;
            if (is_file || response_type === 'blob') {
                body_promise = response.blob();
            } else if (response_type === 'arraybuffer') {
                body_promise = response.arrayBuffer();
            } else if (content_type.indexOf('application/json') > -1) {
                body_promise = response.json();
            } else {
                body_promise = response.text();
            }
            body_promise.then(function (body) {
                success(body, 'success', fake_xhr);
            });
        }

        function fetch_request(config) {
            var method = config.method || 'get';
            var headers = {};
            if (config.contentType) {
                headers['Content-Type'] = config.contentType;
            }
            if (method.toLowerCase() !== 'get') {
                headers['X-CSRFToken'] = getCookie('csrftoken');
            }
            var init = {
                method: method,
                headers: headers,
                credentials: 'same-origin',
            };
            if (config.body !== undefined) {
                init.body = config.body;
            }
            var timer;
            if (config.timeout) {
                var controller = new AbortController();
                init.signal = controller.signal;
                timer = window.setTimeout(function () {
                    controller.abort();
                }, config.timeout);
            }
            fetch(config.url, init).then(function (response) {
                if (timer) clearTimeout(timer);
                if (!response.ok) {
                    ajax_error();
                    return;
                }
                dispatch_fetch(response, config.success || from_django, config.response_type);
            }).catch(function () {
                if (timer) clearTimeout(timer);
                ajax_error();
            });
        }

        // Uploads use XMLHttpRequest because fetch cannot report upload progress
        // and cannot run synchronously, both of which post_data supports.
        function post_data(url, data, timeout, options) {
            if (timeout === undefined) {
                var timeout = 0
            }
            var is_sync = options !== undefined && options.sync === true;
            var xhr = new XMLHttpRequest();
            xhr.open('post', url, !is_sync);
            add_CSRF(xhr);
            if (timeout) {
                xhr.timeout = timeout;
            }
            if (options !== undefined && options.progress !== undefined) {
                xhr.upload.addEventListener('progress', function (e) {
                    if (e.lengthComputable) {
                        var percent = Math.round((e.loaded / e.total) * 100);
                        query_all(options.progress.selector).forEach(function (el) {
                            el.style.width = percent + '%';
                            el.textContent = percent + '%';
                        });
                    }
                });
            }
            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 300) {
                    dispatch_xhr(xhr, from_django);
                } else {
                    ajax_error();
                }
            };
            xhr.onerror = ajax_error;
            xhr.ontimeout = ajax_error;
            xhr.send(data);
        }

        function dispatch_xhr(xhr, success) {
            var content_type = xhr.getResponseHeader('Content-Type') || '';
            var body;
            if (contains_file(xhr)) {
                body = xhr.response;
            } else if (content_type.indexOf('application/json') > -1) {
                body = JSON.parse(xhr.responseText);
            } else {
                body = xhr.responseText;
            }
            success(body, 'success', xhr);
        }

        function post_json(ajax_data, timeout) {
            if (timeout === undefined) {
                var timeout = 0
            }
            var url, data, success;
            var response_type = 'text';
            if (typeof (ajax_data) === 'object') {
                if (ajax_data.url !== undefined) {
                    url = ajax_data.url
                }
                data = ajax_data.data;
                if (ajax_data.success !== undefined) {
                    success = ajax_data.success
                }
                if (ajax_data.response_type !== undefined) {
                    response_type = ajax_data.response_type;
                }
            } else {
                data = ajax_data
            }

            if (success === undefined) {
                success = from_django
            }

            if (url === undefined) {
                url = ajax_helpers.window_location;
            }

            fetch_request({
                url: url,
                method: 'post',
                body: JSON.stringify(data),
                contentType: 'application/json',
                success: success,
                response_type: response_type,
                timeout: timeout,
            });
        }

        function from_django(form_response, status, xhr) {
            if (contains_file(xhr)) {
                download_file(xhr, form_response)
            } else if (typeof (form_response) == 'object') {
                process_commands(form_response)
            }
        }

        function get_content(url, store = true) {
            remove_tooltip();
            if (store) {
                history.pushState(null, "", url);
                window_location = url
            }
            fetch_request({
                url: url,
                method: 'get',
                success: from_django,
            });
        }

        window.addEventListener('popstate', function (e) {
            get_content(window.location.href, false)
        });

        function process_commands(commands) {
            if (ajax_helpers.ajax_busy) {
                window.setTimeout(function () {
                    process_commands(commands)
                }, 100)
            } else {
                while (commands.length > 0) {
                    var command = commands.shift();
                    command_functions[command.function](command);
                    if (ajax_helpers.ajax_busy) {
                        window.setTimeout(function () {
                            process_commands(commands)
                        }, 100);
                        break;
                    }
                }
            }
        }

        var active_tooltip = null;
        var tooltip_hide_timer = null;

        function remove_tooltip() {
            if (tooltip_hide_timer) {
                clearTimeout(tooltip_hide_timer);
                tooltip_hide_timer = null;
            }
            if (active_tooltip) {
                active_tooltip.remove();
                active_tooltip = null;
            }
        }

        function position_tooltip(tip, target, placement) {
            var rect = target.getBoundingClientRect();
            var sx = window.pageXOffset, sy = window.pageYOffset;
            var tw = tip.offsetWidth, th = tip.offsetHeight;
            var top, left;
            if (placement === 'top') {
                top = rect.top + sy - th;
                left = rect.left + sx + rect.width / 2 - tw / 2;
            } else if (placement === 'left') {
                top = rect.top + sy + rect.height / 2 - th / 2;
                left = rect.left + sx - tw;
            } else if (placement === 'right') {
                top = rect.top + sy + rect.height / 2 - th / 2;
                left = rect.right + sx;
            } else {
                top = rect.bottom + sy;
                left = rect.left + sx + rect.width / 2 - tw / 2;
            }
            tip.style.top = Math.round(top) + 'px';
            tip.style.left = Math.round(left) + 'px';
        }

        function tooltip(selector, function_name, placement, template) {
            placement = placement ? placement : "bottom";
            template = template ? template : '<div class="ah-tooltip" role="tooltip"><div class="ah-arrow"></div><div class="ah-tooltip-inner"></div></div>';
            document.querySelectorAll(selector).forEach(function (el) {
                el.addEventListener('mouseenter', function () {
                    var element_data = Object.assign({}, el.dataset);
                    element_data['tooltip'] = function_name;
                    ajax_helpers.post_json({
                        data: element_data,
                        success: function (data) {
                            remove_tooltip();
                            var wrapper = document.createElement('div');
                            wrapper.innerHTML = template.trim();
                            var tip = wrapper.firstChild;
                            tip.classList.add('ah-tooltip-' + placement, 'ah-show');
                            tip.style.position = 'absolute';
                            tip.style.top = '0';
                            tip.style.left = '0';
                            tip.querySelector('.ah-tooltip-inner').innerHTML = data;
                            document.body.appendChild(tip);
                            position_tooltip(tip, el, placement);
                            active_tooltip = tip;
                            tip.addEventListener('mouseenter', function () {
                                if (tooltip_hide_timer) {
                                    clearTimeout(tooltip_hide_timer);
                                    tooltip_hide_timer = null;
                                }
                            });
                            tip.addEventListener('mouseleave', remove_tooltip);
                        }
                    });
                });
                el.addEventListener('mouseleave', function () {
                    tooltip_hide_timer = window.setTimeout(remove_tooltip, 100);
                });
            });
        }

        function show_toast(id) {
            var el = document.getElementById(id);
            if (!el) {
                return;
            }
            var delay = parseInt(el.getAttribute('data-delay'), 10) || 500;
            var auto_hide = el.getAttribute('data-autohide') !== 'false';
            el.querySelectorAll('[data-dismiss="toast"]').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    hide_toast(el);
                });
            });
            el.classList.remove('ah-hide');
            el.classList.add('ah-show');
            if (auto_hide) {
                window.setTimeout(function () {
                    hide_toast(el);
                }, delay);
            }
        }

        function hide_toast(el) {
            el.classList.remove('ah-show');
            el.classList.add('ah-hide');
        }

        function set_ajax_busy(status, pointer_wait) {
            if (typeof pointer_wait === 'undefined') {
                var pointer_wait = false
            }
            if (status === true) {
                ajax_helpers.ajax_busy = true;
                if (pointer_wait) {
                    document.documentElement.classList.add('wait')
                }
            } else {
                ajax_helpers.ajax_busy = false;
                if (pointer_wait) {
                    document.documentElement.classList.remove('wait')
                }
            }
        }

        var command_functions = {
            null: function (){
            },

            element_count: function(command){
                command.data.count = query_all(command.selector).length;
                ajax_helpers.post_json({url:command.url, data: command.data});
            },

            get_attr: function(command){
                var el = query_all(command.selector)[0];
                command.data.val = el ? el.getAttribute(command.attr) : undefined;
                ajax_helpers.post_json({url:command.url, data: command.data});
            },

            timeout: function (command){
                window.setTimeout(function () {
                    ajax_helpers.process_commands(command.commands)
                }, command.time)
            },

            timer: function (command) {
                var timer = window.setInterval(function () {
                    if (command.always || document.visibilityState === "visible") {
                        ajax_helpers.process_commands([...command.commands]);
                    }
                }, command.interval);
                if (command.store !== undefined){
                    if (set_intervals[command.store] === undefined){
                        set_intervals[command.store] = [timer]
                    } else{
                        set_intervals[command.store].push(timer)
                    }
                }
            },

            clear_timers: function(command){
                if (set_intervals[command.store] !== undefined) {
                    for (var i = 0; i < set_intervals[command.store].length; i++) {
                        clearTimeout(set_intervals[command.store][i]);
                    }
                    set_intervals[command.store] = [];
                }
            },

            ajax_post: function (command) {
                ajax_helpers.post_json({url:command.url, data: command.data})
            },

            send_form: function(command){
                ajax_helpers.send_form(command.form_id, command)
            },

            onload: function (command) {
                on_ready(function () {
                    ajax_helpers.process_commands(command.commands);
                });
            },

            delay: function (command) {
                ajax_helpers.ajax_busy = true;
                window.setTimeout(function () {
                    ajax_helpers.ajax_busy = false
                }, command.time)
            },

            save_file: function (command) {
                var byte_chars = atob(command.data);
                var byte_numbers = [];
                for (var i = 0; i < byte_chars.length; i++) {
                    byte_numbers.push(byte_chars.charCodeAt(i))
                }
                var byte_array = new Uint8Array(byte_numbers);
                var blob = new Blob([byte_array], {type: "octet/stream"});
                download_blob(command.filename, blob)
            },

            on: function(command){
                query_all(command.selector).forEach(function (el) {
                    command.event.split(' ').forEach(function (event_name) {
                        el.addEventListener(event_name, function (e) {
                            if (command.keys) {
                                if (command.keys.includes(e.key)) {
                                    if (command.prevent_default) {
                                        e.preventDefault();
                                    }
                                    ajax_helpers.process_commands([...command.commands])
                                }
                            } else {
                                if (command.prevent_default) {
                                    e.preventDefault();
                                }
                                ajax_helpers.process_commands([...command.commands])
                            }
                        });
                    });
                });
            },

            stop_propagation: function (command) {
                query_all(command.selector).forEach(function (el) {
                    command.event.split(' ').forEach(function (event_name) {
                        el.addEventListener(event_name, function (e) {
                            e.stopPropagation();
                        });
                    });
                });
            },

            set_prop: function (command) {
                query_all(command.selector).forEach(function (el) {
                    el[command.prop] = command.val;
                });
            },

            set_attr: function (command) {
                query_all(command.selector).forEach(function (el) {
                    el.setAttribute(command.attr, command.val);
                });
            },

            set_value: function (command) {
                query_all(command.selector).forEach(function (el) {
                    el.value = command.val;
                });
            },

            set_css: function (command) {
                query_all(command.selector).forEach(function (el) {
                    el.style.setProperty(command.prop, command.val);
                });
            },

            append_to: function(command) {
                query_all(command.selector).forEach(function (target) {
                    var tmp = document.createElement('div');
                    tmp.innerHTML = command.html;
                    var added = [];
                    while (tmp.firstChild) {
                        added.push(target.appendChild(tmp.firstChild));
                    }
                    added.forEach(function (node) {
                        if (node.nodeType === 1) {
                            activate_scripts(node);
                        }
                    });
                });
            },

            remove: function (command){
                query_all(command.selector).forEach(function (el) {
                    el.remove();
                });
            },

            html: function (command) {
                remove_tooltip();
                query_all(command.selector).forEach(function (el) {
                    var target = command.parent === true ? el.parentElement : el;
                    set_html(target, command.html);
                });
            },

            reload: function () {
                ajax_helpers.ajax_busy = true;
                location.reload();
            },

            redirect: function (command) {
                if (command.new_tab) {
                    window.open(command.url, '_blank');
                } else {
                    window.location.href = command.url;
                }
            },

            message: function (command) {
                alert(command.text);
            },

            replace_with: function (command) {
                query_all(command.selector).forEach(function (el) {
                    var target = command.parent === true ? el.parentElement : el;
                    var tmp = document.createElement('div');
                    tmp.innerHTML = command.html;
                    var nodes = Array.prototype.slice.call(tmp.childNodes);
                    nodes.forEach(function (node) {
                        target.parentNode.insertBefore(node, target);
                    });
                    target.remove();
                    nodes.forEach(function (node) {
                        if (node.nodeType === 1) {
                            activate_scripts(node);
                        }
                    });
                });
            },

            console_log: function (command) {
                console.log(command.text);
            },

            focus: function (command) {
                var el = query_all(command.selector)[0];
                if (el) {
                    el.focus();
                }
            },

            clipboard: function(command){
                navigator.clipboard.writeText(command.text);
            },

            if_selector: function (command) {
                var elements = query_all(command.selector);
                var matched;
                if (command.is_visible) {
                    matched = false;
                    elements.forEach(function (el) {
                        if (is_visible(el)) {
                            matched = true;
                        }
                    });
                } else {
                    matched = elements.length > 0;
                }
                if (matched) {
                    ajax_helpers.process_commands([...command.commands])
                } else if (command.else_commands !== undefined) {
                    ajax_helpers.process_commands([...command.else_commands])
                }
            },

            if_not_selector: function (command) {
                var elements = query_all(command.selector);
                var matched;
                if (command.is_visible) {
                    matched = elements.length === 0;
                    elements.forEach(function (el) {
                        if (!is_visible(el)) {
                            matched = true;
                        }
                    });
                } else {
                    matched = elements.length === 0;
                }
                if (matched) {
                    ajax_helpers.process_commands([...command.commands])
                } else if (command.else_commands !== undefined) {
                    ajax_helpers.process_commands([...command.else_commands])
                }
            },

            upload_file: function (command) {
                var file, file_data;
                var index = command.index !== undefined ? command.index : 0;
                var form_data = {
                    upload: 'files',
                    index: index,
                };
                if (command.upload_params !== undefined) {
                    form_data.upload_params = JSON.stringify(command.upload_params);
                }
                if (command.drag_drop !== undefined) {
                    file = ajax_helpers.drag_drop_files[command.drag_drop][index];
                    form_data.file_info = JSON.stringify(ajax_helpers.file_info(ajax_helpers.drag_drop_files[command.drag_drop]));
                    form_data.drag_drop = command.drag_drop;
                } else {
                    file = query_all(command.selector)[0].files[index];
                    form_data.file_info = JSON.stringify(ajax_helpers.file_info(command.selector));
                    form_data.selector = command.selector;
                }
                if (command.start !== undefined || command.end !== undefined) {
                    form_data.start = command.start !== undefined ? command.start : 0;
                    form_data.end = command.end !== undefined ? command.end : file.size;
                    file_data = file.slice(form_data.start, form_data.end);
                } else {
                    file_data = file;
                }
                form_data.ajax_modal_file = file_data;
                ajax_helpers.send_form(null, form_data, 0, command.options)
            },

            start_websocket: function(command) {
                var sockets = ajax_helpers._websockets || (ajax_helpers._websockets = {});
                var url = command.ws_url;

                // One socket per page per ws_url. If we already hold one that's
                // connecting or open, reuse it — repeat calls (page re-render, an
                // ajax html-swap re-running the tail block, a per-row refresh) must
                // NOT stack additional connections. Previously every call opened a
                // fresh WebSocket and every close/error spun up its own immortal
                // reconnect loop, so sockets accumulated without bound.
                var existing = sockets[url];
                if (existing && (existing.readyState === WebSocket.CONNECTING || existing.readyState === WebSocket.OPEN)) {
                    return existing;
                }

                var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
                var helperSocket = new WebSocket(ws_scheme + "://" + window.location.host + url);
                sockets[url] = helperSocket;

                helperSocket.onopen = function (e) {
                    console.log("Successfully connected to the WebSocket.");
                }

                helperSocket.onclose = function (e) {
                    // Only the currently-registered socket owns the reconnect loop,
                    // so a superseded/duplicate socket closing can never spawn a
                    // second loop.
                    if (sockets[url] !== helperSocket) {
                        return;
                    }
                    delete sockets[url];
                    console.log("WebSocket connection closed unexpectedly. Trying to reconnect in 2s...");
                    setTimeout(function () {
                        console.log("Reconnecting...");
                        command_functions['start_websocket'](command);
                    }, 2000);
                };

                helperSocket.onmessage = function (e) {
                    const commands = JSON.parse(e.data)
                    ajax_helpers.process_commands(commands.commands);
                }

                helperSocket.onerror = function (err) {
                    console.log("WebSocket encountered an error: " + err.message);
                    console.log("Closing the socket.");
                    helperSocket.close();
                }
                return helperSocket;
            }
        };

        function file_info(selector) {
            var files;
            if (typeof (selector) === "string") {
                files = query_all(selector)[0].files
            } else {
                files = selector
            }
            var fi = [];
            for (var f = 0; f < files.length; f++) {
                fi.push({name: files[f].name, size: files[f].size})
            }
            return fi
        }

        function upload_file(selector, upload_params) {
            ajax_helpers.post_json({
                data: {
                    start_upload: 'files',
                    files: file_info(selector),
                    selector: selector,
                    upload_params: upload_params
                }
            })
        }

        var drag_drop = function (container_id, upload_params, upload_function) {
            var dropArea = query_all(container_id)[0];
            if (!dropArea) {
                return;
            }
            if (upload_function === undefined) {
                upload_function = handle_files;
            }
            ['dragenter', 'dragover'].forEach(function (event_name) {
                dropArea.addEventListener(event_name, function (e) {
                    e.preventDefault();
                    dropArea.classList.add('drag_highlight');
                });
            });
            ['dragleave', 'drop'].forEach(function (event_name) {
                dropArea.addEventListener(event_name, function (e) {
                    e.preventDefault();
                    dropArea.classList.remove('drag_highlight');
                });
            });
            dropArea.addEventListener('drop', function (e) {
                var dt = e.dataTransfer;
                upload_function(dt.files, dropArea);
            });

            function handle_files(files, element) {
                ajax_helpers.drag_drop_files.push(files);
                var data = {
                    start_upload: 'files',
                    files: file_info(files),
                    drag_drop: ajax_helpers.drag_drop_files.length - 1
                };
                var element_id = element.getAttribute('id');
                if (upload_params !== undefined && upload_params !== null) {
                    data.upload_params = upload_params
                }
                if (element_id !== undefined && element_id !== null) {
                    if (data.upload_params === undefined) {
                        data.upload_params = {element_id: element_id}
                    } else {
                        data.upload_params.element_id = element_id
                    }
                }
                ajax_helpers.post_json({
                    data: data
                });
            }
        };

        return {
            getCookie,
            get_content,
            window_location,
            post_json,
            send_form,
            post_data,
            command_functions,
            process_commands,
            tooltip,
            remove_tooltip,
            show_toast,
            ajax_busy,
            set_ajax_busy,
            upload_file,
            file_info,
            drag_drop,
            drag_drop_files,
        }
    }()
}
