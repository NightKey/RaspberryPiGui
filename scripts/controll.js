window.onload = function(){

    weather_creator = function() {
        var js,fjs=document.getElementsByTagName('script')[0];js=document.createElement('script');js.id='weatherwidget-io-js';js.src='https://weatherwidget.io/js/widget.min.js';fjs.parentNode.insertBefore(js,fjs);
    }

    weather_creator();

    /*Variables*/
    let init = false;
    let brightness = document.getElementById('brightness');
    let brightness_text = document.getElementById("brightness_number");
    let bvalue = brightness.value;
    let modal = document.getElementById('alerts');
    let error = document.getElementById('error');
    let message = document.getElementById('message');
    let error_msg = document.getElementById('error_message');
    let message_msg = document.getElementById('message_message');
    let dismiss = document.getElementById('Dismiss');
    let ok = document.getElementById('Ok');
    let cancle = document.getElementById('Cancle');
    let picker = document.getElementById('color');
    let cabinet = document.getElementById("cabinet");
    let bath_tub = document.getElementById("bath_tub");
    let room = document.getElementById("room");
    let message_shown = false;
    let update = document.getElementById('update');
    let refresh = document.getElementById('refresh');
    let pause = document.getElementById('pause');
    let skip = document.getElementById('skip');
    let prev = document.getElementById('prev');
    let is_playing = false;
    let is_music_on = false;
    let volume_nob = document.getElementById('volume');
    let volume_num = document.getElementById('volume_number');
    let send_alert = false;
    let fan = document.getElementById('fan_div');
    let now_playing = document.getElementById('now_playing');

    /*Functions*/
    show_error = function(msg) {
        error_msg.innerHTML = msg;
        error.style.display = 'block';
        modal.style.display = 'block';
    }

    toggle_fan = function() {
        if (fan.style.display == 'block') {
            fan.style.display = 'none';
        }
        else {
            fan.style.display = 'block';
        }
    }

    show_message = function(msg) {
        message_shown = true;
        message_msg.innerHTML = msg;
        message.style.display = 'block';
        modal.style.display = 'block';
    }

    close_message = function() {
        if (message_shown) {
            message_shown = false;
            message.style.display = 'none';
            modal.style.display = 'none';
        }
    }

    room_extend = function() {
        show_message("A fények 30 másodperc múlva kikapcsolnak!");
        swtc(room);
        setTimeout(function() {
            swtc(room);
            close_message();
        }, 30000);
    }

    swtc = function(what) {
        what.checked = !what.checked;
        event = document.createEvent('Event');
        event.initEvent('change', true, true);
        what.dispatchEvent(event);
    }

    work = function(ansver) {
        console.log('Todo: '+todo+'\tAnsver: '+ansver);
        switch (todo) {
            case 'room':
                room.checked = ansver;
                event = document.createEvent('Event');
                event.initEvent('change', true, true);
                room.dispatchEvent(event);
                message_shown=false;
                break;
            case 'kill':
                connection.send('kill');
                break;
        }
    }

    music = function(data) {
        if (data != 'none') {
            is_music_on = true;
            now_playing.innerHTML = data
        }
        else {
            is_music_on = false;
            now_playing.innerHTML = '';
        }
    }

    /* Connection */
    let connection = new this.WebSocket("ws://127.0.0.1:6969");
    let todo;

    console.log("Connecting to server...")

    connection.onopen = function() {
        console.log("Connection established");
        init = true;
    }

    connection.onclose = function() {
        console.log("Connection closed!");
        show_error('Megszakadt a kapcsolat a szerverrel!');
    }

    connection.onmessage = function(event){
        console.log(event.data);
        switch (event.data) {
            case 'room_extend':
                room_extend();
                break;
            case 'room':
                if (!init) {
                    if (!message_shown) {
                        todo = event.data;
                        console.log('room on');
                        show_message('Az ajtó nyitva, a fények égnek 2 percig.<br>Maradjanak égve?');
                    }
                    else {
                        console.log('room off');
                        work(false);
                    }
                }
                else {
                    todo = event.data;
                    swtc(room);
                }
                break;
            case 'bath_tub':
                swtc(bath_tub);
                break;
            case 'cabinet':
                swtc(cabinet);
                break;
            case 'temp':
                show_error('A Pi hőmérséklete túl magas!');
                break;
            case 'alert':
                send_alert = true;
                break;
            case 'finished':
                init = false;
                break;
            case 'fan':
                toggle_fan();
                break;
            case 'close':
                close_message();
                break;
            default:
                if (send_alert) {
                    alert(event.data);
                    send_alert = false;
                } else{
                    switch (event.data.split('|')[0]) {
                        case 'color':
                            let tmp = event.data.split('|')[1].replace('[', '').replace(']', '').split(', ');
                            for (let i = 0; i < 3; i++) {
                                tmp[i] = tmp[i].replace("'", '').replace("'", '');
                            }
                            console.log(tmp)
                            picker.value = "#".concat(tmp[0], tmp[1], tmp[2]);
                            event = document.createEvent('Event');
                            event.initEvent('change', true, true);
                            picker.dispatchEvent(event);
                            break;
                        case 'brightness':
                            brightness.value = parseInt(event.data.split('|')[1]);
                            event = document.createEvent('Event');
                            event.initEvent('input', true, true);
                            brightness.dispatchEvent(event);
                            break;
                        case 'volume':
                            volume_nob.value = parseInt(event.data.split('|')[1]);
                            event = document.createEvent('Event');
                            event.initEvent('input', true, true);
                            volume_nob.dispatchEvent(event);
                            break;
                        case 'music':
                            music(event.data.split('|')[1]);
                            break;
                    }
                }
        }
    }

    if (bvalue < 10) {
        bvalue = "0" + bvalue;
    }

    brightness_text.innerHTML = bvalue;

    /* Event handlers */
    brightness.addEventListener("input", function() {
        
        let bvalue = brightness.value;
        console.log("EventListener called with value of "+bvalue)
        if (bvalue < 10) {
            bvalue = "0" + bvalue;
        }

        brightness_text.innerHTML = bvalue;
        let data = 'brightness,'+bvalue;
        if (!init) {
            connection.send(data);
        }
    }, false);

    room.addEventListener('change', function() {
        let room_on = room.checked;
        console.log("EventListener called for '"+lights.id+"' with value '"+room_on+"'");
        let data = 'room,'+room_on;
        if (!init) {
            connection.send(data);
        }
    }, false);

    bath_tub.addEventListener('change', function() {
        let bath_tub_on = bath_tub.checked;
        console.log("EventListener called for '"+bath_tub.id+"' with value '"+bath_tub_on+"'");
        let data = 'bath_tub,'+bath_tub_on;
        if (!init) {
            connection.send(data);
        }
    }, false);

    cabinet.addEventListener('change', function() {
        let cabinet_on = cabinet.checked;
        console.log("EventListener called for '"+cabinet.id+"' with value '"+cabinet_on+"'");
        let data = 'cabinet,'+cabinet_on;
        if (!init) {
            connection.send(data);
        }
    }, false);

    dismiss.addEventListener('click', function() {
        location.reload();
    }, false);
    
    ok.addEventListener('click', function() {
        message_msg.innerHTML = '';
        message.style.display = 'none';
        modal.style.display = 'none';
        work(true);
    }, false);

    cancle.addEventListener('click', function() {
        message_msg.innerHTML = '';
        message.style.display = 'none';
        modal.style.display = 'none';
        work(false);
    }, false);

    picker.addEventListener('change', function(){
        picker.style.backgroundColor = picker.value;
        console.log('Selected color: '+picker.value);
        if (!init) {
            connection.send('color,'+picker.value);   
        }
    }, false);

    update.addEventListener('click', function(){
        console.log('Update clicked!');
        if (!init) {
            connection.send('update,None');   
        }
    }, false);

    refresh.addEventListener('click', function(){
        if (connection.readyState == WebSocket.OPEN) {
            weather_creator();
        }
        else {
            location.reload();
        }
    }, false);

    skip.addEventListener('click', function(){
        if (is_music_on) {
            console.log('Skip clicked!');
            if (!init) {
                connection.send('skip,None');
            }
        }
    }, false);

    prev.addEventListener('click', function(){
        if (is_music_on) {
            console.log('Prev clicked!');
            if (!init) {
                connection.send('prev,None');
            }
        }
    }, false);

    pause.addEventListener('click', function(){
        console.log('Pause clicked!');
        if(is_music_on) {
            if (!is_playing){
                pause.src='images/play.png';
                is_playing = true;
            }
            else { 
                pause.src='images/pause.png'; 
                is_playing = false;
            }
            if (!init) {
                connection.send('pause,None');
            }
        }
    }, false);

    volume_nob.addEventListener('input', function() {
        console.log('Volume at '+volume_nob.value);
        volume_num.innerHTML = 'Hangerő: '+volume_nob.value+'%';
        if (!init) {
            connection.send('volume,'+volume_nob.value);
        }
    }, false);

}