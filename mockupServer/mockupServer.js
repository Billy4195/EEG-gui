const WebSocketServer = require("uws").Server;
const readline = require("readline");

class Server {
    constructor() {
        this.port = process.env.PORT || 8888;
        this.channelNum = Number(process.env.CH) || 64;
        this.msgCount = {
            RAW: 0,
            DEC: 0,
            FFT: 0
        };
        this.tick = 0;
        this.coefficient = 0;
        this.dec_factor = 4;
        this.fftFakeData = Array(this.channelNum).fill(Array(5000).fill(0));
        this.rawEvent = false;
        this.decEvent = false;

        this.mockLoop();
        this.stdinListener();
        this.wss = this.initServer();
        this.setHandler();
        this.printMsgCount();
    }

    mockLoop() {
        const mainLoop = () => {
            setTimeout(mainLoop, 1);
            this.tick += 1;
            this.coefficient += 0.01;
        }
         
        const eventLoop = () => {
            setTimeout(eventLoop, 5000);
            this.rawEvent = true;
            this.decEvent = true;
        }

        setTimeout(mainLoop, 1);
        setTimeout(eventLoop, 5000);
    }

    stdinListener() {
        let rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            terminal: false
        });
        
        rl.on("line", (line) => {
            const tmp = Number(line);
            if(tmp === 4 || tmp === 8) {
                this.dec_factor = tmp;
            }
            else {
                console.log("bad cmd format");
            }
        });
    }

    initServer() {
        let wss = new WebSocketServer({ port: this.port }, () => {
            console.log(`Server is up on ${this.port}`);
        });

        return wss;
    }

    setHandler() {
        this.wss.on("connection", (ws) => {
            this.onMsg(ws);

            //this.sendRAW(ws);
            this.sendDEC(ws);
            //this.sendFFT(ws);
        });
    }

    onMsg(ws) {
        ws.on("message", (message) => {
            msgObj = JSON.parse(message);
            if(msgObj.hasOwnProperty("dec_factor")) {
                const tmp = Number(msgObj["dec_factor"]);
                if(tmp === 8 || tmp === 4) {
                    this.dec_factor = tmp;
                }
            }
            else {
                console.log("bad msg format");
            }
        });
    }

    sendRAW(ws) {
        const sendOneRAW = () => {
            setTimeout(sendOneRAW, 1);
            this.msgCount.RAW += 1;
            ws.send(JSON.stringify(this.genPacket("RAW")));
        }
        setTimeout(sendOneRAW, 1);
    }

    sendDEC(ws) {
        const sendOneDEC = () => {
            setTimeout(sendOneDEC, this.dec_factor);
            this.msgCount.DEC += 1;
            ws.send(JSON.stringify(this.genPacket("DEC")));
        }
        setTimeout(sendOneDEC, this.dec_factor);
    }

    sendFFT(ws) {
        const sendOneFFT = () => {
            setTimeout(sendOneFFT, 5000);
            this.msgCount.FFT += 1;
            ws.send(JSON.stringify(this.genPacket("FFT")));
        }
        setTimeout(sendOneFFT, 5000);
    }

    genPacket(type) {
        if(type === "RAW") {
            let currentEvent = null;
            if(this.rawEvent) {
                currentEvent = {
                    name: "testEvent@" + this.tick.toString(),
                    duration: 10
                }
                this.rawEvent = false;
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
        }
        else if(type === "DEC") {
            let currentEvent = null;
            if(this.decEvent) {
                currentEvent = {
                    name: "testEvent@" + this.tick.toString(),
                    duration: 10
                }
                this.decEvent = false;
            }
            return {
                name: "dec",
                type: "raw",
                tick: this.tick,
                data: {
                    eeg: Array(this.channelNum).fill(Math.sin(this.coefficient)),
                    event: currentEvent
                }
            };
        }
        else if(type === "FFT") {
            return {
                name: "fft",
                type: "fft",
                startTick: this.tick - 4999,
                endTick: this.tick,
                data: this.fftFakeData
            }
        }
        else {
            console.log("Type err: ", type);
        }
    }

    printMsgCount() {
        setInterval(() => {
            console.log("msgCount: ", this.msgCount);
            this.msgCount.RAW = 0;
            this.msgCount.DEC = 0;
            this.msgCount.FFT = 0;
        }, 1000);
    }
};

let myServer = new Server();