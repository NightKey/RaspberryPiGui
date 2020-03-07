window.onload = function(){
    let connection = new this.WebSocket("ws://127.0.0.1:6969");
    let todo;

    console.log("Connecting to server...")

    connection.onopen = function() {
        console.log("Connection established");
    }

    connection.onclose = function() {
        console.log("Connection closed!");
        show_error('Megszakadt a kapcsolat a szerverrel!');
    }

    connection.onmessage = function(event){
        todo = event.data;
        console.log(todo);
        switch (todo) {
            case 'room':
                show_message('Az ajtó nyitva, a fények égnek 2 percig.<br>Maradjanak égve?');
                break;
        }
    }

    let brightness = document.getElementById('brightness');
    let brightness_text = document.getElementById("brightness_number");
    let bvalue = brightness.value;

    if (bvalue < 10) {
        bvalue = "0" + bvalue;
    }

    brightness_text.innerHTML = bvalue;
    brightness.addEventListener("input", function() {
        
        let bvalue = brightness.value;
        console.log("EventListener called with value of "+bvalue)
        if (bvalue < 10) {
            bvalue = "0" + bvalue;
        }

        brightness_text.innerHTML = bvalue;
        let data = 'brightness,'+bvalue;
        connection.send(data);
    }, false);

    let room = document.getElementById("room");

    room.addEventListener('change', function() {
        let room_on = room.checked;
        console.log("EventListener called for '"+lights.id+"' with value '"+room_on+"'");
        let data = 'room,'+room_on;
        connection.send(data);
    });

    let bath_tub = document.getElementById("bath_tub");

    bath_tub.addEventListener('change', function() {
        let bath_tub_on = bath_tub.checked;
        console.log("EventListener called for '"+bath_tub.id+"' with value '"+bath_tub_on+"'");
        let data = 'bath_tub,'+bath_tub_on;
        connection.send(data);
    });

    let cabinet = document.getElementById("cabinet");

    cabinet.addEventListener('change', function() {
        let cabinet_on = cabinet.checked;
        console.log("EventListener called for '"+cabinet.id+"' with value '"+cabinet_on+"'");
        let data = 'cabinet,'+cabinet_on;
        connection.send(data);
    });

    let color = this.document.getElementById('selected_color');

    color.addEventListener('change', function() {
        let selected_color = color.background-color;
        console.log("EventListener called for '"+color.id+"' with value '"+selected_color+"'");
    });

    let modal = document.getElementById('alerts');
    let error = document.getElementById('error');
    let message = document.getElementById('message');
    let error_msg = document.getElementById('error_message');
    let message_msg = document.getElementById('message_message');
    let dismiss = document.getElementById('Dismiss');
    let ok = document.getElementById('Ok');
    let cancle = document.getElementById('Cancle');

    work = function(ansver) {
        console.log('Todo: '+todo+'\tAnsver: '+ansver);
        switch (todo) {
            case 'room':
                room.checked = ansver;
                event = document.createEvent('Event');
                event.initEvent('change', true, true);
                room.dispatchEvent(event);
                break;
            case 'kill':
                connection.send('kill');
                break;
        }
    }

    show_error = function(msg) {
        error_msg.innerHTML = msg;
        error.style.display = 'block';
        modal.style.display = 'block';
    }

    show_message = function(msg) {
        message_msg.innerHTML = msg;
        message.style.display = 'block';
        modal.style.display = 'block';
    }

    dismiss.addEventListener('click', function() {
        error_msg.innerHTML = '';
        error.style.display = 'none';
        modal.style.display = 'none';
    });
    
    ok.addEventListener('click', function() {
        message_msg.innerHTML = '';
        message.style.display = 'none';
        modal.style.display = 'none';
        work(true);
    });

    cancle.addEventListener('click', function() {
        message_msg.innerHTML = '';
        message.style.display = 'none';
        modal.style.display = 'none';
        work(false);
    });

}