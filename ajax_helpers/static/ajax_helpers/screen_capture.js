if (typeof screen_capture === 'undefined') {
    var screen_capture = function () {

        let audioTrack, videoTrack, stream, chunks, recorder, timerInterval, timer;
        let audioSource = true;

        async function startCapture() {
            navigator.mediaDevices.getDisplayMedia({video: true})
                .then(async displayStream => {
                    [videoTrack] = displayStream.getVideoTracks();
                    const audioStream = await navigator.mediaDevices.getUserMedia({audio: audioSource}).catch(e => {
                        throw e;
                    });
                    [audioTrack] = audioStream.getAudioTracks();
                    start_recording();
                })
                .catch(console.error);
        }

        function audio_devices(modal_url) {
            let audioInputs = [];
            navigator.mediaDevices.enumerateDevices().then(function (deviceInfos) {
                for (let i = 0; i !== deviceInfos.length; ++i) {
                    const deviceInfo = deviceInfos[i];
                    if (deviceInfo.kind === "audioinput") {
                        audioInputs.push([deviceInfo.deviceId, deviceInfo.label || "microphone " + (audioInputs.length + 1)]);
                    }
                }
                django_modal.show_modal(modal_url.replace('%1%', btoa(JSON.stringify(audioInputs).replace(/\+/g, '-').replace(/\//g, '_'))));
            });
        }

        function start_recording() {
            chunks = [];
            stream = new MediaStream([videoTrack, audioTrack]);
            recorder = new MediaRecorder(stream);
            recorder.ondataavailable = e => {chunks.push(e.data)};
            recorder.start();
            timer = 0;
            start_timer();
            ajax_helpers.post_json({data:{button: "recording_started"}})
        }

        function start_timer(){
            timerInterval = window.setInterval(function(){
                timer += 1;
                $('#record-timer').html(((timer/60)>>0).toString() + ':' + (timer % 60).toString().padStart(2,'0'))
            }, 1000)
        }


        ajax_helpers.command_functions['set_audio_source'] = function (command) {
            audioSource = {deviceId: command.audio_source}
        };


        ajax_helpers.command_functions['pause_resume'] = function () {
            if (recorder.state === 'paused'){
                recorder.resume();
                start_timer();
                ajax_helpers.post_json({data:{button: "recording_started"}})
            } else if (recorder.state ==='recording'){
                recorder.pause();
                clearInterval(timerInterval)
            }
        };

        ajax_helpers.command_functions['start_capture'] = function () {
            if (videoTrack === undefined) {
                startCapture();
            } else {
                start_recording();
            }
        };

        ajax_helpers.command_functions['upload_capture'] = function (command) {
            recorder.onstop = e => {
                clearInterval(timerInterval);
                stream.getTracks().forEach(track => track.stop());
                videoTrack = undefined;
                const completeBlob = new Blob(chunks, {type: chunks[0].type});
                var fd = new FormData();
                fd.append('data', completeBlob);
                fd.append('ajax', 'upload_video');
                for (let property in command){
                    fd.append(property, command[property])
                }
                for (let property in extra_data) {
                    fd.append(property, extra_data[property])
                }

                ajax_helpers.post_data(ajax_helpers.window_location, fd);
            };
            if (recorder.state === 'paused' || recorder.state === 'recording'){
                recorder.stop()
            }
        };

        ajax_helpers.command_functions['stop_capture'] = function () {
            recorder.stop();
            clearInterval(timerInterval);
            stream.getTracks().forEach(track => track.stop());
            videoTrack = undefined;
        };

        return {
            audio_devices,
        };
    }();
}