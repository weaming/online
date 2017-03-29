var CHECK_INTERVAL = 30;
var DEFAULT_URL =  "wss://online.bitsflow.org/websocket";
//var DEFAULT_URL =  "ws://localhost:9999/websocket";

function startWebsocket(event){
    var print = window.print = console.log.bind(console);
    var wsURL = window.onlineWebsocketURL || DEFAULT_URL;

    var ws = new WebSocket(wsURL);
    if (window.onlineWebsocket){
        var funcs = ['onopen', 'onmessage', 'onerror', 'onclose'];
        for (var i=0,l=funcs.length;i<l;i++){
            var method = funcs[i];
            if (window.onlineWebsocket[method]){
                ws[method] = window.onlineWebsocket[method];
            }
        }
    }
    window.onlineWebsocket = ws;

    if (!ws.onopen){
        ws.onopen = function() {
            ws.send(location.hostname);
        };
    }

    if (!ws.onmessage){
        ws.onmessage = function(e) {
            print(e.data);

            try{ var data = JSON.parse(e.data); } catch(e){return;}

            var ele = document.getElementsByClassName('onlineCount');
            if (!ele.length){
                // return; // disable auto adding <p>

                // add <p> at the bottom of <body>
                ele = [document.createElement('p')];
                ele[0].classList.add('onlineCount');
                document.body.appendChild(ele[0]);
            }
            for(var i=0, length=ele.length; i<length; i++){
                ele[i].innerHTML = '在线人数：' + data.client;
            }
        };
    }

    if (!ws.onerror){
        ws.onerror = function(){
            print('error: ' + this.url);
        }
    }

    if (!ws.onclose){
        ws.onclose = function(){
            print('closed: ' + this.url);
        }
    }
}

// first start
document.addEventListener("DOMContentLoaded", startWebsocket);

setInterval(function check(){
    //CONNECTING	0	The connection is not yet open.
    //OPEN      1	The connection is open and ready to communicate.
    //CLOSING	2	The connection is in the process of closing.
    //CLOSED	3	The connection is closed or couldn't be opened.
    if (!window.onlineWebsocket || window.onlineWebsocket.readyState === undefined || window.onlineWebsocket.status > 1){
        print('retrying...');
        startWebsocket()
    }else{
        window.onlineWebsocket.send('healthy: ' + new Date().toLocaleString());
    }
}, CHECK_INTERVAL*1000)
