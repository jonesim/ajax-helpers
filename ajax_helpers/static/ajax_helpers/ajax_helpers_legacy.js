"use strict";

function _toConsumableArray(arr) { return _arrayWithoutHoles(arr) || _iterableToArray(arr) || _unsupportedIterableToArray(arr) || _nonIterableSpread(); }

function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _iterableToArray(iter) { if (typeof Symbol !== "undefined" && iter[Symbol.iterator] != null || iter["@@iterator"] != null) return Array.from(iter); }

function _arrayWithoutHoles(arr) { if (Array.isArray(arr)) return _arrayLikeToArray(arr); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }

function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }

if (typeof ajax_helpers === 'undefined') {
  var ajax_helpers = function () {
    var drag_drop_files = [];
    var window_location = window.location;
    var ajax_busy = false;

    function getCookie(name) {
      var cookieValue = null;

      if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');

        for (var i = 0; i < cookies.length; i++) {
          var cookie = jQuery.trim(cookies[i]);

          if (cookie.substring(0, name.length + 1) === name + '=') {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }

      return cookieValue;
    }

    function send_form(form_id, extra_data, timeout, options) {
      if (timeout === undefined) {
        var timeout = 0;
      }

      var data;

      if (form_id != null) {
        var form = $('#' + form_id);
        data = new FormData(form[0]);
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

    function contains_file(jqXHR) {
      var content_disposition = jqXHR.getResponseHeader('Content-Disposition');
      return typeof content_disposition == 'string' && content_disposition.indexOf('attachment') > -1;
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
        window.URL.revokeObjectURL(download_url);
      }
    }

    function download_file(jqXHR, response) {
      var filename, blob;
      var content_disposition = jqXHR.getResponseHeader('Content-Disposition');
      var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
      var matches = filenameRegex.exec(content_disposition);
      if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');

      if (_typeof(response) === 'object') {
        blob = response;
      } else {
        blob = new Blob([response], {
          type: "octet/stream"
        });
      }

      download_blob(filename, blob);
      alert('your file has downloaded');
    }

    function post_data(url, data, timeout, options) {
      if (timeout === undefined) {
        var timeout = 0;
      }

      var ajax_config = {
        url: url,
        method: 'post',
        data: data,
        beforeSend: add_CSRF,
        cache: false,
        contentType: false,
        processData: false,
        success: from_django,
        timeout: timeout
      };

      if (options !== undefined && options.progress !== undefined) {
        ajax_config.xhr = function () {
          var xhr = new XMLHttpRequest();
          xhr.upload.addEventListener('progress', function (e) {
            if (e.lengthComputable) {
              var percent = Math.round(e.loaded / e.total * 100);
              $(options.progress.selector).css('width', percent + '%');
              $(options.progress.selector).text(percent + '%');
            }
          });
          return xhr;
        };
      }

      $.ajax(ajax_config);
    }

    function post_json(ajax_data, timeout) {
      if (timeout === undefined) {
        var timeout = 0;
      }

      var url, data, success;
      var response_type = 'text';

      if (_typeof(ajax_data) === 'object') {
        if (ajax_data.url !== undefined) {
          url = ajax_data.url;
        }

        data = ajax_data.data;

        if (ajax_data.success !== undefined) {
          success = ajax_data.success;
        }

        if (ajax_data.response_type !== undefined) {
          response_type = ajax_data.response_type;
        }
      } else {
        data = ajax_data;
      }

      if (success === undefined) {
        success = from_django;
      }

      if (url === undefined) {
        url = ajax_helpers.window_location;
      }

      $.ajax({
        url: url,
        method: 'post',
        data: JSON.stringify(data),
        contentType: 'application/json',
        beforeSend: add_CSRF,
        cache: false,
        success: success,
        timeout: timeout,
        xhrFields: {
          responseType: response_type
        }
      });
    }

    function from_django(form_response, status, jqXHR) {
      if (contains_file(jqXHR)) {
        download_file(jqXHR, form_response);
      } else if (_typeof(form_response) == 'object') {
        process_commands(form_response);
      }
    }

    function get_content(url) {
      var store = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : true;

      if (store) {
        history.pushState(null, "", url);
        window_location = url;
      }

      $.ajax({
        url: url,
        success: from_django
      });
    }

    $(window).on("popstate", function (e) {
      get_content(e.target.window.location.href, false);
    });

    function process_commands(commands) {
      if (ajax_helpers.ajax_busy) {
        window.setTimeout(function () {
          process_commands(commands);
        }, 100);
      } else {
        while (commands.length > 0) {
          var command = commands.shift();
          command_functions[command.function](command);

          if (ajax_helpers.ajax_busy) {
            window.setTimeout(function () {
              process_commands(commands);
            }, 100);
            break;
          }
        }
      }
    }

    var tooltip = {
      init: function init(selector, url) {
        var css_class = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 'ajax-tooltip';
        var tooltip_start = false;
        $(selector).hover(function () {
          var _this = this;

          if (!$(".tooltip:hover").length) {
            tooltip_start = false;
            $(this).tooltip("dispose");
          } else {
            $('.tooltip').mouseleave(function () {
              tooltip_start = false;
              $(_this).tooltip("dispose");
            });
          }
        });
        $(selector).mouseover(function () {
          if (tooltip_start) {
            return;
          }

          tooltip_start = true;
          var tooltip_container = $(this);
          $.ajax({
            url: url,
            data: this.dataset,
            success: function success(data) {
              tooltip_container.tooltip({
                placement: "bottom",
                delay: 0,
                trigger: 'manual',
                html: true,
                title: data,
                template: '<div class="tooltip" role="tooltip"><div class="arrow"></div><div class="tooltip-inner ' + css_class + '"></div></div>'
              });

              if (tooltip_start) {
                tooltip_container.tooltip('show');
                tooltip_start = false;
              } else {
                tooltip_container.tooltip('dispose');
              }
            },
            error: function error() {
              tooltip_start = false;
            }
          });
        });
      }
    };

    function set_ajax_busy(status, pointer_wait) {
      if (typeof pointer_wait === 'undefined') {
        var pointer_wait = false;
      }

      if (status === true) {
        ajax_helpers.ajax_busy = true;

        if (pointer_wait) {
          $("html").addClass("wait");
        }
      } else {
        ajax_helpers.ajax_busy = false;

        if (pointer_wait) {
          $("html").removeClass("wait");
        }
      }
    }

    var command_functions = {
      null: function _null() {},
      element_count: function element_count(command) {
        command.data.count = $(command.selector).length;
        ajax_helpers.post_json({
          url: command.url,
          data: command.data
        });
      },
      get_attr: function get_attr(command) {
        command.data.val = $(command.selector).attr(command.attr);
        ajax_helpers.post_json({
          url: command.url,
          data: command.data
        });
      },
      timeout: function timeout(command) {
        window.setTimeout(function () {
          ajax_helpers.process_commands(command.commands);
        }, command.time);
      },
      timer: function timer(command) {
        window.setInterval(function () {
          if (command.always || document.visibilityState === "visible") {
            ajax_helpers.process_commands(_toConsumableArray(command.commands));
          }
        }, command.interval);
      },
      ajax_post: function ajax_post(command) {
        ajax_helpers.post_json({
          url: command.url,
          data: command.data
        });
      },
      send_form: function send_form(command) {
        ajax_helpers.send_form(command.form_id, command);
      },
      onload: function onload(command) {
        $(document).ready(function () {
          ajax_helpers.process_commands(command.commands);
        });
      },
      delay: function delay(command) {
        ajax_helpers.ajax_busy = true;
        window.setTimeout(function () {
          ajax_helpers.ajax_busy = false;
        }, command.time);
      },
      save_file: function save_file(command) {
        var byte_chars = atob(command.data);
        var byte_numbers = [];

        for (var i = 0; i < byte_chars.length; i++) {
          byte_numbers.push(byte_chars.charCodeAt(i));
        }

        var byte_array = new Uint8Array(byte_numbers);
        var blob = new Blob([byte_array], {
          type: "octet/stream"
        });
        download_blob(command.filename, blob);
      },
      on: function on(command) {
        $(command.selector).on(command.event, function () {
          ajax_helpers.process_commands(_toConsumableArray(command.commands));
        });
      },
      set_prop: function set_prop(command) {
        $(command.selector).prop(command.prop, command.val);
      },
      set_attr: function set_attr(command) {
        $(command.selector).attr(command.attr, command.val);
      },
      set_value: function set_value(command) {
        $(command.selector).val(command.val);
      },
      set_css: function set_css(command) {
        $(command.selector).css(command.prop, command.val);
      },
      append_to: function append_to(command) {
        $(command.html).appendTo(command.selector);
      },
      html: function html(command) {
        var element = $(command.selector);

        if (command.parent === true) {
          element = element.parent();
        }

        element.html(command.html);
      },
      reload: function reload() {
        ajax_helpers.ajax_busy = true;
        location.reload();
      },
      redirect: function redirect(command) {
        window.location.href = command.url;
      },
      message: function message(command) {
        alert(command.text);
      },
      upload_file: function upload_file(command) {
        var file, file_data;
        var index = command.index !== undefined ? command.index : 0;
        var form_data = {
          upload: 'files',
          index: index
        };

        if (command.upload_params !== undefined) {
          form_data.upload_params = JSON.stringify(command.upload_params);
        }

        if (command.drag_drop !== undefined) {
          file = ajax_helpers.drag_drop_files[command.drag_drop][index];
          form_data.file_info = JSON.stringify(ajax_helpers.file_info(ajax_helpers.drag_drop_files[command.drag_drop]));
          form_data.drag_drop = command.drag_drop;
        } else {
          file = $(command.selector)[0].files[index];
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
        ajax_helpers.send_form(null, form_data, null, command.options);
      }
    };

    function file_info(selector) {
      var files;

      if (typeof selector === "string") {
        files = $(selector)[0].files;
      } else {
        files = selector;
      }

      var fi = [];

      for (var f = 0; f < files.length; f++) {
        fi.push({
          name: files[f].name,
          size: files[f].size
        });
      }

      return fi;
    }

    function upload_file(selector, upload_params) {
      ajax_helpers.post_json({
        data: {
          start_upload: 'files',
          files: file_info(selector),
          selector: selector,
          upload_params: upload_params
        }
      });
    }

    var drag_drop = function drag_drop(container_id, upload_params, upload_function) {
      var dropArea = $(container_id);

      if (upload_function === undefined) {
        upload_function = handle_files;
      }

      dropArea.on('dragenter dragover', function (e) {
        e.preventDefault();
        $(this).addClass('drag_highlight');
      });
      dropArea.on('dragleave drop', function (e) {
        e.preventDefault();
        $(this).removeClass('drag_highlight');
      });
      dropArea.on('drop', function (e) {
        var dt = e.originalEvent.dataTransfer;
        upload_function(dt.files, this);
      });

      function handle_files(files, element) {
        ajax_helpers.drag_drop_files.push(files);
        var data = {
          start_upload: 'files',
          files: file_info(files),
          drag_drop: ajax_helpers.drag_drop_files.length - 1
        };
        var element_id = $(element).attr('id');

        if (upload_params !== undefined && upload_params !== null) {
          data.upload_params = upload_params;
        }

        if (element_id !== undefined) {
          if (data.upload_params === undefined) {
            data.upload_params = {
              element_id: element_id
            };
          } else {
            data.upload_params.element_id = element_id;
          }
        }

        ajax_helpers.post_json({
          data: data
        });
      }
    };

    $(document).ajaxError(function () {
      $("html").removeClass("wait");
      ajax_helpers.ajax_busy = false;
    });
    return {
      getCookie: getCookie,
      get_content: get_content,
      window_location: window_location,
      post_json: post_json,
      send_form: send_form,
      post_data: post_data,
      command_functions: command_functions,
      process_commands: process_commands,
      tooltip: tooltip,
      ajax_busy: ajax_busy,
      set_ajax_busy: set_ajax_busy,
      upload_file: upload_file,
      file_info: file_info,
      drag_drop: drag_drop,
      drag_drop_files: drag_drop_files
    };
  }();
}