const http = require("http");
const webSocketServer = require("websocket").server;

const port = process.env.PORT || 8888;
const clock = (1000 / process.env.HZ) || (1000 / 250);
const channelNum = Number(process.env.CH) || 64;

var server = http.createServer();
server.listen(port, () => {
    console.log(`Server is up on ${port}`);
});

var wsServer = new webSocketServer({
    httpServer: server
});

////////////////////////////////////
let factor = 0;
let sendEvent = false;
let mockTick = 0

const generateJSON = () => {
    let currentEvent = null;
    if(sendEvent) {
        currentEvent = {
            name: "testEvent@" + mockTick.toString(),
            duration: 10
        }
        sendEvent = false;
    }

    return {
        name: "raw",
        type: "raw",
        tick: mockTick,
        data: {
            eeg: Array(channelNum).fill(Math.sin(factor)),
            event: currentEvent
        }
    };
};
////////////////////////////////////
setInterval(() => {
    factor += 0.04;
    mockTick += 4;
}, 4);

setInterval(() => {
    sendEvent = true; //send a test event every 5 second
}, 5000)

wsServer.on("request", (request) => {
    var connection = request.accept(null, request.origin); 
    console.log("[Connection] new client connected.");

    setInterval(() => {
        connection.sendUTF(JSON.stringify(generateJSON()));
    }, clock);
    
    connection.on("close", (connection) => {
        console.log("[Connection] a client disconnected.");
    });
});
