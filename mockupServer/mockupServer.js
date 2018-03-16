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
let SN = 0;

const generateJSON = () => {
    return {
        name: "raw",
        type: "raw",
        data: {
            eeg: Array(channelNum).fill(Math.sin(factor)),
            event: null,
            auxiliary: null,
            battery_power: null,
            g_sensor: {
                x: 2,
                y: 2,
                z: 2
            },
            gyro: null,
            machine_info: null,
            serial_number: SN++,
            properties:["g_sensor", "serial_number", "eeg"],
            tag_counts: 3
        }
    };
};
////////////////////////////////////
setInterval(() => {
    factor += 0.1;
}, 10);

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
