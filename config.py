def init():
    global PORT, CH, HZ, DURATION, WSURI, rawList, currentIndex, scale
    PORT = 8888
    CH = 64
    HZ = 250
    DURATION = 10
    WSURI = "ws://localhost:" + str(PORT) + "/"
    rawList = [[0 + n * 10] * HZ * DURATION for n in range(CH)]
    currentIndex = 0
    scale = 0.5