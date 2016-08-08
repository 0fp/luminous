#!/usr/bin/python3
#coding: utf8

#import lirc as lirc
import threading
import time
import socketserver
import queue
import json
import math

from multiprocessing import Process, Queue, Pipe

import RPi.GPIO as GPIO

# =====================================================================
class LED:
    power = False
    intensity = 0.5
    norm = 1

    _pin = 0
    _pwmFrequency = 60 #Hz

    def __init__(self, pin):
        GPIO.setup(pin, GPIO.OUT)
        self._pwm = GPIO.PWM(pin, self._pwmFrequency)
        self._pin = pin
        self._pwm.start(0)

    def __del__(self):
        self.set(0)
        self._pwm.stop()
        GPIO.cleanup(self._pin)

    def set(self, intensity=1):
        if not self.power:
            print('!off')
            return

        intensity = min(1., max(0., intensity))
        dc = (math.exp(2*intensity) - 1) / (math.exp(2) - 1) * 100 * self.norm
        # print('pwm {} {:.4f} {:.4f}'.format(self._pin, dc, intensity))
        self._pwm.ChangeDutyCycle(dc)
        self.intensity = intensity

    def on(self):
        self.power = True

    def off(self):
        self.power = False

    def toggle(self):
        self.off() if self.power else self.on()

# =====================================================================
class Sequence:
    steps = []
    transitionDuration = 4
    stepDuration = 5
    running = False

    def append(self, step):
        self.steps.append(step)

    def run(self):
        def _():
            self._start = time.time()
            step = 0
            print('run sequence')
            while self.running and len(self.steps) > 1:
                print("step", step)
                for c, I in self.steps[step]:
                    if not c.on: continue
                    d = self.transitionDuration
                    c.transition(Linear(c.intensity, I, d), d)
                    c.start()

                time.sleep(self.stepDuration)
                step = (step+1) % len(self.steps)

            self.running = False

        self.running = True
        self._thread = threading.Thread(target=_)
        self._thread.start()

    def stop(self):
        print('stop sequence')
        self.running = False
        if self._thread:
            self._thread.join()

# =====================================================================
class Transition:
    _updateFrequency = 10

    def __init__(self, led, intensity_start, intensity_end,
            duration=0,
            loop=False,
            blocking=False):
        self.led = led
        self.i_start = intensity_start
        self.i_end = intensity_end
        self.duration = duration
        self.loop = loop
        self.blocking = blocking

    def run(self):
        if self.duration == 0:
            self.led.set(self.i_end)
            return

        def _():
            self._start = time.time()
            dt = 0
            while dt <= self.duration:
                rdt = dt/self.duration
                I = self.i_start + (self.i_end - self.i_start) * rdt

                print(self._thread, I)
                self.led.set(I)

                time.sleep(1/self._updateFrequency)
                dt = (time.time() - self._start)

        if self.blocking:
            _()
            return

        self._thread = threading.Thread(target=_)
        self._thread.start()

# =====================================================================
class ThreadedTCPStreamServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True,
                 queue=None):
        self.queue = queue
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass,
                           bind_and_activate=bind_and_activate)

class ThreadedTCPStreamHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.queue = server.queue
        socketserver.StreamRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip().decode()
        self.queue.put(self.data)

# =====================================================================
class Channel:

    _updateFrequency = 30
    intensity = 0.1
    _mStart = None
    mFunction = None
    on = False
    _mAmplitude = 0.2
    mFrequency = 0.5
    _thread = None

    def __init__(self, led):
        self.led=led
        led.on()
        self._running = False

    def __del__(self):
        self.stop()

    def toggle(self):
        print('toggle')
        print('Ib=', self.intensity)
        I = self.intensity
        #currentI = self.led.intensity

        if not self.on:
            self.transition(Linear(0, I, 1), 1)
        else:
            self.transition(Linear(I, 0, 1), 1)
        self.start()

        self.on = not self.on
        print('on' if self.on else 'off', I)

        def reset():
            self._thread.join()
            self.intensity = I
            print('reset {}'.format(I))
        threading.Thread(target=reset).start()

        print('Ia=', self.intensity)

    def modulation(self, function, blocking=False):
        print('modulation')
        self.mFunction = function
        self._mStart = time.time()

    def transition(self, function, duration):
        print('transition')
        self.tFunction = function
        self.tDuration = duration
        self._tStart = time.time()

    def start(self):

        if self._running: return

        def update():
            running = True
            while running:
                now = time.time()
                I = self.intensity
                mod = 0

                # transition
                if self._tStart:
                    dt = now - self._tStart
                    if dt > self.tDuration:
                        I = min(1, max(0, self.tFunction(self.tDuration)))
                        self._tStart = None
                    else:
                        I = self.tFunction(dt)
                    self.intensity = I

                # modulation
                if self._mStart and I > 0:
                    dt = now - self._mStart
                    mod = self._mAmplitude * self.mFunction(self.mFrequency * dt)

                # hold
                if not (self._tStart or (self._mStart and I > 0)):
                    self._running = False

                #print("{:.4f} {:.4f} {}".format(I, mod, self._mStart))
                self.led.set(I + mod)

                running = self._running
                time.sleep(1/self._updateFrequency)

        self._running = True
        print('run')
        self._thread = threading.Thread(target=update)
        self._thread.start()

    def stop(self):
        print('stop channel')
        self._running = False
        if self._thread:
            self._thread.join()

# =====================================================================

def Linear(x0, x1, duration):
    print('from {} to {}'.format(x0, x1))
    def _(dt):
        if dt <= duration:
            return x0 + (x1 - x0) * (dt/duration)
        return x1
    return _

def Sine(x0, x1, period, offset=0):
    def _(dt):
        m = (1 + math.sin(2 * math.pi / period * dt + offset)) / 2
        return x0 + (x1 - x0) * m
    return _

# =====================================================================

q = queue.Queue()

HOST, PORT = "localhost", 50007

# Create the server, binding to localhost on port 9999
server = ThreadedTCPStreamServer((HOST, PORT), ThreadedTCPStreamHandler, queue=q)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

GPIO.setmode(GPIO.BCM)

red = Channel(LED(19))
green = Channel(LED(13))
blue = Channel(LED(26))

green.led.norm = 0.2

channels = {
        'red': red,
        'green': green,
        'blue': blue
        }

sequence = Sequence()

try:
    while True:

        cmd = q.get()
        q.task_done()
        q.join()
        print('got', cmd)
        try:
            cmd = json.loads(cmd)
        except ValueError:
            continue
        try:
            cmd = {k:v for k,v in cmd.items() if v != ''}
        except AttributeError:
            continue

        if 'power' in cmd and cmd['power'] == 'toggle':
            for c in [red, green, blue]:
                c.toggle()
            _ = False
            while not _:
                time.sleep(0.1)
                _ = True
                for c in [red, green, blue]:
                    _ = _ and c._tStart is None

        if not blue.on:
            continue

        _ = ((c, cmd[k]) for k,c in channels.items() if k in cmd)
        for c, I in _:

            if I == "toggle":
                if c.intensity == 0:
                    c.transition(Linear(0, 1, 1), 1)
                elif c.intensity == 1:
                    c.transition(Linear(1, 0, 1), 1)
                else:
                    c.transition(Linear(c.intensity, 1, 1), 1)
                continue

            if str(I)[0] in ['+', '-']:
                I = c.intensity + float(I)
                c.transition(Linear(c.intensity, I, 1), 1)

            # mod
            if I == 'sine':
            # if codeIR == 'JUMP3':
                if c._mStart:
                    continue
                c.modulation(Sine(-1, 1, 1))


        if cmd.get('play') == 'toggle':
            if red.mFunction is not None:
                if red._mStart:
                    mStart = None
                else:
                    mStart = time.time()
                for c in channels.values():
                    c._mStart = mStart

        if cmd.get('sequence') == 'start':
            if sequence.running:
                print('n')
                sequence.stop()
            else:
                print('i')
                step = [(c, c.intensity) for c in channels.values()]
                sequence.append(step)
                sequence.run()


        #c.Intensity(I)

        for c in [red, green, blue]:
            c.start()

        print([c.intensity for c in [red, green, blue]])

except KeyboardInterrupt:
    pass

sequence.stop()

for c in [red, green, blue]:
    c.stop()

server.shutdown()
#del controller

print('exit')
