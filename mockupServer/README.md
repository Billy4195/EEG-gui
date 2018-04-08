# MockupServer for Websocket
- Configurable options
    - PORT (port to listen)
        - default: 8888
    - CH (number of channels)
        - default: 64
    - HZ (update frequncy)
        - default: 250

### JSON format (tmp)
```
{
    name: "raw",
    type: "raw",
    tick: 1234,
    data: {
        eeg: [0, 1.2, 3.5, .... ,2.1],
        event: {
            name: "eventABC",
            duration: 10
        }
    }
}
```
### Usage
```
npm install
PORT=8888 CH=64 HZ=250 node mockupServer.js //you can execute without options
```
```
You can change decimated factor via terminal by typing `4` or `8`,
Also, you can change it via websocket message, the format is JSON:
{
    dec_factor: 8
}

```
