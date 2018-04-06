const WebSocketServer = require('uws').Server;
const readline = require("readline");

class rawDataChart {
    constructor() {
        this.port = process.env.PORT || 8888;
        this.clock = (1000 / process.env.HZ) || (1000 / 250);
        this.channelNum = Number(process.env.CH) || 64;
        this.coefficient = 0;
        this.sendEvent = false;
        this.tick = 0;
        this.msgCount = 0;
        
        this.mockLoop();
        this.rl = this.stdinListener();
        this.wss = this.setupServer();
    }

    generateJSON() {
        let currentEvent = null;
        if(this.sendEvent) {
            currentEvent = {
                name: "testEvent@" + this.tick.toString(),
                duration: 10
            }
            this.sendEvent = false;
        }
    
        return {
            name: "raw",
            type: "raw",
            tick: this.tick,
            data: {
                eeg: Array(this.channelNum).fill(Math.sin(this.coefficient)),
                event: currentEvent
            }
        };
    };

    mockLoop() {
        setInterval(() => {
            this.coefficient += 0.04;
            this.tick += 4;
        }, 4);

        setInterval(() => {
            this.sendEvent = true; //send a test event every 5 second
        }, 5000);
    }

    stdinListener() {
        var rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            terminal: false
        });
        
        rl.on("line", (line) => {
            const tmp = Number(line);
            if(tmp === 125 || tmp === 250) {
                this.clock = 1000 / tmp;
                console.log("set frequency to:", tmp);
            }
            else {
                console.log("bad cmd format");
            }
        });

        return rl;
    }

    setupServer() {
        let self = this;
        let wss = new WebSocketServer({ port: self.port }, () => {
            console.log(`Server is up on ${self.port}`);
        });

        wss.on("connection", (ws) => {
            ws.on("message", (message) => {
                msgObj = JSON.parse(message);
                if(msgObj.hasOwnProperty("frequency")) {
                    const tmp = Number(msgObj["frequency"]);
                    if(tmp === 125 || tmp === 250) {
                        self.clock = 1000 / tmp;
                    }
                }
                else {
                    console.log("bad msg format");
                }
            });
        
            const sendMsg = () => {
                setTimeout(sendMsg, self.clock);
                self.msgCount++;
                ws.send(JSON.stringify(self.generateJSON()));
            }
            setTimeout(sendMsg, self.clock);
        
            setInterval(() => {
                console.log("msgCount: ", self.msgCount);
                self.msgCount = 0;
            }, 1000)
        });

        return wss;
    }
};

let myRawDataChart = new rawDataChart();
