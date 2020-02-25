/*
__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"
*/
const uws = require("uWebSockets.js");

class Server {
    constructor() {
        this.port = process.env.PORT || 8888;
        this.tick = 0;
        this.coe = 0;
        this.decEvent = false;
        this.serverParams = this.initParams(1000, (Number(process.env.CH) || 64));
        //serverParams: { spsOrigin(Number), chNum(Number), chLabel(array) }
        this.clientState = this.initClientState(4, 4);
        this.mockLoop();
        this.server = this.initServer();
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
                stream: false,
                chunkSize: chunkSize
            },
            decimation: {
                stream: false,
                decimateNum: decimateNum
            },
            impedance: {
                stream: false
            },
            FFT: {
                stream: false
            },
            powerBand: {
                stream: false
            }
        };
    }
    initServer() {
        const server = uws.App().listen(this.port,() => {
            console.log(`Server is up on ${this.port}`);
        });
        return server;
    }
    wsHandler() {
        this.server.ws('/*', {
            /* For brevity we skip the other events */
            message: (ws, msg, isBinary) => {
                this.processMsg(ws, JSON.parse(msg));
            },
            close: (ws) => {
                console.log("Client Disconnect");
                this.clientState.raw.stream = false;
                this.clientState.decimation.stream = false;
                this.clientState.impedance.stream = false;
                this.clientState.FFT.stream = false;
                this.clientState.powerBand.stream = false;
            },
            open: (ws, req) => {
                const sendDecimate = () => {
                    if (this.clientState.decimation.stream) {
                        ws.send(JSON.stringify(this.genPacket("DEC")));
                    }
                    setTimeout(sendDecimate, this.clientState.decimation.decimateNum);
                }
                setTimeout(sendDecimate, this.clientState.decimation.decimateNum);
    
                const sendRaw = () => {
                    if (this.clientState.raw.stream) {
                        ws.send(JSON.stringify(this.genPacket("RAW")));
                    }
                    setTimeout(sendRaw, this.clientState.raw.chunkSize);
                }
                setTimeout(sendRaw, this.clientState.raw.chunkSize);
    
                const sendImpedance = () => {
                    if (this.clientState.impedance.stream) {
                        ws.send(JSON.stringify(this.genPacket("IMP")));
                    }
                    setTimeout(sendImpedance, 2000);
                }
                setTimeout(sendImpedance, 2000);
    
                const sendFFT = () => {
                    if (this.clientState.FFT.stream) {
                        ws.send(JSON.stringify(this.genPacket("FFT")));
                    }
                    setTimeout(sendFFT, 500);
                }
                setTimeout(sendFFT, 500);
    
                const sendPowerBand = () => {
                    if (this.clientState.powerBand.stream) {
                        ws.send(JSON.stringify(this.genPacket("PowerBand")));
                    }
                    setTimeout(sendPowerBand, 500);
                }
                setTimeout(sendPowerBand, 500);
            },
        });
    }
    processMsg(ws, msg) {
        //change clientState
        const PT = msg["type"]["target_name"];
        const COMMAND = msg["type"]["type"];

        if (PT === "raw") {
            if (COMMAND === "setting") {
                this.clientState.raw.stream = (msg["contents"]["enable"] == 'true' || msg["contents"]["enable"] == true);
                this.clientState.raw.chunkSize = Number(msg["contents"]["chunk_size"]);
                this.sendRes("raw", "ack", ws);

            } else if (COMMAND === "request") {
                this.sendRes("raw", "response", ws);
            }
        } else if (PT === "decimation") {
            if (COMMAND === "setting") {
                this.clientState.decimation.stream = (msg["contents"]["enable"] == 'true' || msg["contents"]["enable"] == true);
                this.clientState.decimation.decimateNum = Number(msg["contents"]["decimate_num"]);
                this.sendRes("decimation", "ack", ws);

            } else if (COMMAND === "request") {
                this.sendRes("decimation", "response", ws);
            }
        } else if (PT === "impedance") {
            if (COMMAND === "setting") {
                this.clientState.impedance.stream = (msg["contents"]["enable"] == 'true' || msg["contents"]["enable"] == true);
                this.sendRes("impedance", "ack", ws);

            } else if (COMMAND === "request") {
                this.sendRes("impedance", "response", ws);
            }
        } else if (PT === "device") {
            this.sendRes("device", "response", ws);
        } else if (PT === "FFT") {
            if (COMMAND === "setting") {
                this.clientState.FFT.stream = (msg["contents"]["enable"] == 'true' || msg["contents"]["enable"] == true);
                this.sendRes("FFT", "ack", ws);

            } else if (COMMAND === "request") {
                this.sendRes("FFT", "response", ws);
            }  
        } else if (PT === "PowerBand") {
            if (COMMAND === "setting") {
                this.clientState.powerBand.stream = (msg["contents"]["enable"] == 'true' || msg["contents"]["enable"] == true);
                this.sendRes("PowerBand", "ack", ws);

            } else if (COMMAND === "request") {
                this.sendRes("PowerBand", "response", ws);
            }  
        }
    }
    sendRes(PT, resType, ws) {
        if (PT === "raw" && resType === "ack") {
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: PT,
                    source_name: PT
                },
                name: null,
                contents: {
                    result: true
                }
            }));
        } else if (PT === "raw" && resType === "response") {
            ws.send(JSON.stringify({
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
            }));
        } else if (PT === "decimation" && resType === "ack") {
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: "algorithm",
                    source_name: PT
                },
                name: null,
                contents: {
                    result: true
                }
            }));
        } else if (PT === "decimation" && resType === "response") {
            ws.send(JSON.stringify({
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
                    chunk_size: this.clientState.raw.chunkSize,
                    ch_label: this.serverParams.chLabel
                }
            }));
        } else if (PT === "impedance" && resType === "ack") {
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: "device",
                    source_name: PT
                },
                name: null,
                contents: {
                    result: true
                }
            }));
        } else if (PT === "impedance" && resType === "response") {
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: "device",
                    source_name: PT
                },
                name: null,
                contents: {
                    enable: true,
                    sps_origin: this.serverParams.spsOrigin,
                    ch_num: 8,
                    ch_label: ["Fp1", "Fp2", "Fz", "C1", "C2", "Pz", "POz", "Oz"]
                }
            }));
        } else if (PT === "device" && resType === "response") {
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: "device",
                    source_name: PT
                },
                name: null,
                contents: {
                    sampling_rate: 1000,
                    resolution: 24,
                    ch_num: 8,
                    ch_label: ["Fp1", "Fp2", "Fz", "C1", "C2", "Pz", "POz", "Oz"],
                    battery: 87,
                    error: ""
                }
            }));            
        } else if (PT === "FFT" && resType === "ack") {
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: "algorithm",
                    source_name: PT
                },
                name: null,
                contents: {
                    result: true
                }
            }));
        } else if (PT === "FFT" && resType === "response") {
            let index = -0.5;
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: "algorithm",
                    source_name: PT
                },
                name: null,
                contents: {
                    enable: true,
                    window_size: 2,
                    window_interval: 0.5,
                    freq_range: [0,30],
                    ch_label: ["Fp1", "Fp2", "Fz", "C1", "C2", "Pz", "POz", "Oz"],
                    freq_label:  Array.from({length: 61}, () => { return (index += 0.5) }),
                    data_size: [8,61]
                }
            }));
        } else if (PT === "PowerBand" && resType === "ack") {
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: "algorithm",
                    source_name: PT
                },
                name: null,
                contents: {
                    result: true
                }                
            }));
        } else if (PT === "PowerBand" && resType === "response") {
            ws.send(JSON.stringify({
                type: {
                    type: resType,
                    source_type: "algorithm",
                    source_name: PT
                },
                name: null,
                contents: {
                    enable: true,
                    window_size: 2,
                    window_interval: 0.5,
                    smooth: 4,
                    ch_num: 8,
                    ch_label: ["Fp1", "Fp2", "Fz", "C1", "C2", "Pz", "POz", "Oz"]
                }
            }));
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
                    sync_tick: [this.tick, this.tick + 1, this.tick + 2, this.tick + 3],
                    eeg: Array(4).fill(Array(8).fill(1)),
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
        } else if (PT === "IMP") {
            return {
                type: {
                    type: "data",
                    source_tpye: "device",
                    source_name: "impedance"
                },
                name: null,
                contents: {
                    sync_tick: this.tick,
                    impedance: Array.from({length: 8}, () => Math.random() * 2000)
                }
            }
        } else if (PT === "FFT") {
            return {
                type: {
                    type: "data",
                    source_tpye: "algorithm",
                    source_name: "FFT"
                },
                name: null,
                contents: {
                    sync_tick: this.tick,
                    data: Array.from({length: 8}, () => {
                        return Array.from({length: 61}, () => Math.random() * 600);
                    })
                }              
            }
        } else if (PT === "PowerBand") {
            return {
                type: {
                    type: "data",
                    source_tpye: "algorithm",
                    source_name: "PowerBand"
                },
                name: null,
                contents: {
                    sync_tick: this.tick,
                    power: Array.from({length: 8}, () => {
                        return Array.from({length: 8}, () => Math.random() * 8);
                    }),
                    z_score_all: Array.from({length: 8}, () => {
                        return Array.from({length: 8}, () => Math.random() * 8);
                    }),
                    z_score_each: Array.from({length: 8}, () => {
                        return Array.from({length: 8}, () => Math.random() * 8);
                    }),
                }                   
            }
        } else {
            console.log("PT error:", PT);
        }
    }
};

let myServer = new Server();
