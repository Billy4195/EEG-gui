# MockupServer for Websocket
- Configurable options
    - PORT (port to listen)
        - default: 8888
    - CH (number of channels)
        - default: 64
    - HZ (update frequncy)
        - default: 250

### JSON format
```
{
    name: "raw",
    type: "raw",
    data: {
        eeg: Array(CH),
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
}
```
### Usage
```
npm install
PORT=8888 CH=64 HZ=250 node mockupServer.js //you can execute without options
```
