const wsServer = require("uws").Server;

class Server {
    constructor() {
        this.port = process.env.PORT || 8888;
        this.tick = 0;
        this.coe = 0;
        this.decEvent = false;
        this.serverParams = this.initParams(1000, (Number(process.env.CH) || 64));
        //serverParams: { spsOrigin(Number), chNum(Number), chLabel(array) }
        this.clientState = this.initClientState(4, 4);
        //clientState: { raw: { phase, chunkSize}, decimation: {phase, decimateNum} }
        this.mockLoop();
        this.wss = this.initServer();
        this.wsHandler();
    }
    mockLoop() {
        const mainLoop = () => {
            setTimeout(mainLoop, 4);
            this.tick += 4;
            this.coe += 0.04;
        }
        setTimeout(mainLoop, 4);

        const eventLoop = () => {
            setTimeout(eventLoop, 5000);
            this.decEvent = true;
        }
        setTimeout(eventLoop, 5000);
        //mock-up event in decimation every 5 seconds
    }
    initParams(spsOrigin, chNum) {
        let params = {
            spsOrigin: spsOrigin,
            chNum: chNum,
            chLabel: []       
        };
        for (let i = 0; i < chNum; i++) {
            params.chLabel.push("mockCH" + i.toString());
        }
        return params;
    }
    initClientState(chunkSize, decimateNum) {
        return {
            raw: {
                phase: "WAIT_SET",
                chunkSize: chunkSize
            },
            decimation: {
                phase: "WAIT_SET",
                decimateNum: decimateNum
            }
        };
    }
    initServer() {
        let wss = new wsServer({ port: this.port }, () => {
            console.log(`Server is up on ${this.port}`);
        });
        return wss;
    }
    wsHandler() {
        this.wss.on("connection", (ws) => {
            console.log("Client Connected");

            ws.on("message", (msg) => {
                this.processMsg(ws, msg);
            });
            ws.on("close", () => {
                console.log("Client Disconnect");
                this.clientState.raw.phase = "WAIT_SET";
                this.clientState.decimation.phase = "WAIT_SET";
            });        
            //////////////////////////////////////////////
            this.clientState.raw.phase = "STREAM";
            this.clientState.decimation.phase = "STREAM";
            //This part is temporary
            //////////////////////////////////////////////
            const sendDecimate = () => {
                if (this.clientState.decimation.phase === "STREAM") {
                    setTimeout(sendDecimate, this.clientState.decimation.decimateNum);
                }
                ws.send(JSON.stringify(this.genPacket("DEC")));
            }
            setTimeout(sendDecimate, this.clientState.decimation.decimateNum);

            const sendRaw = () => {
                if (this.clientState.raw.phase === "STREAM") {
                    setTimeout(sendRaw, this.clientState.raw.chunkSize);
                }
                ws.send(JSON.stringify(this.genPacket("RAW")));
            }
            setTimeout(sendRaw, this.clientState.raw.chunkSize);
        });
    }
    processMsg(ws, msg) {
        //change clientState
        const PT = msg["type"]["target_name"];
        const COMMAND = msg["type"]["type"];

        if (PT === "raw") {
            if (COMMAND === "setting") {
                this.clientState.raw.phase = "WAIT_REQ";
                this.clientState.raw.chunkSize = Number(msg["contents"]["chunk_size"]);
                this.sendRes("raw", "ack", ws);

            } else if (COMMAND === "request") {
                this.clientState.raw.phase = "STREAM";
                this.sendRes("raw", "response", ws);
            }
        } else if (PT === "decimation") {
            if (COMMAND === "setting") {
                this.clientState.decimation.phase = "WAIT_REQ";
                this.clientState.decimation.decimateNum = Number(msg["contents"]["decimate_num"]);
                this.sendRes("decimation", "ack", ws);

            } else if (COMMAND === "request") {
                this.clientState.decimation.phase = "STREAM";
                this.sendRes("decimation", "response", ws);
            }
        } else {
            console.log(msg);
        }
    }
    sendRes(PT, resType, ws) {
        if (PT === "raw" && resType === "ack") {
            ws.send({
                type: {
                    type: resType,
                    source_type: PT,
                    source_name: PT
                },
                name: null,
                contents: {
                    result: true
                }
            });
        } else if (PT === "raw" && resType === "response") {
            ws.send({
                type: {
                    type: resType,
                    source_type: PT,
                    source_name: PT
                },
                name: null,
                contents: {
                    enable: true,
                    sps_origin: this.serverParams.spsOrigin,
                    ch_num: this.serverParams.chNum,
                    chunk_size: this.clientState.raw.chunkSize
                }
            });
        } else if (PT === "decimation" && resType === "ack") {
            ws.send({
                type: {
                    type: resType,
                    source_type: "algorithm",
                    source_name: PT
                },
                name: null,
                contents: {
                    result: true
                }
            });
        } else if (PT === "decimation" && resType === "response") {
            ws.send({
                type: {
                    type: resType,
                    source_type: "algorithm",
                    source_name: PT
                },
                name: null,
                contents: {
                    enable: true,
                    sps_origin: this.serverParams.spsOrigin,
                    ch_num: this.serverParams.chNum,
                    chunk_size: this.clientState.raw.chunkSize
                }
            });
        }
    }
    genPacket(PT) {
        if (PT === "RAW") {
            return {
                type: {
                    type: "data",
                    source_type: "raw",
                    source_name: "raw"
                },
                name: null,
                contents: {
                    sync_tick: [this.tick, this.tick+1, this.tick+2, this.tick+3],
                    eeg: Array(4).fill(Array(64).fill(1)),
                    event: {
                        event_id: [
                            [125, 126],
                            [],
                            [125],
                            []
                        ],
                        event_duration: [
                            [0.5, 1],
                            [],
                            [0.6],
                            []
                        ]
                    },
                    g_sensor: {
                        X: [10, 11, 15, 20],
                        Y: [1, 0, -1, 0],
                        Z: [-2, -1, 0, 1]
                    },
                    gyro: null,
                    battery_power: null,
                    machine_info: null
                }
            }
        } else if (PT === "DEC") {
            let currentEvent = {};
            if (this.decEvent) {
                currentEvent = {
                    event_id: this.tick,
                    event_duration: 10
                }
                this.decEvent = false;
            }
            return {
                type: {
                    type: "data",
                    source_tpye: "algorithm",
                    source_name: "decimation"
                },
                name: null,
                contents: {
                    sync_tick: this.tick,
                    data: Array(this.serverParams.chNum).fill(Math.sin(this.coe)),
                    event: currentEvent
                }
            }
        } else {
            console.log("PT error:", PT);
        }
    }
};

let myServer = new Server();
