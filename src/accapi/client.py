from threading import Thread
import re
import socket
import struct

from .enums import OutboundMessageTypes
from .structs import *

class Event(object):
    def __init__(self, source, **kwargs):
        self.source = source
        for k, v in kwargs.items():
            setattr(self, k, v)

class Observable(object):
    def __init__(self):
        self._callbacks = []

    @property
    def callbacks(self):
        return self._callbacks[:]

    def subscribe(self, callback):
        self._callbacks.append(callback)

class AccClient(object):
    def __init__(
        self,
        displayName: str = "Python ACCAPI",
        updateIntervalMs: int = 100
    ):
        self._server = (None, None)
        self._displayName = displayName
        self._updateIntervalMs = updateIntervalMs
        self._socket = None

        # Callbacks
        self._onConnectionStateChange = Observable()
        self._onTrackDataUpdate = Observable()
        self._onEntryListCarUpdate = Observable()
        self._onRealtimeUpdate = Observable()
        self._onRealtimeCarUpdate = Observable()
        self._onBroadcastingEvent = Observable()

        # Session properties
        self._broadcastingProtocolVersion = 4
        self._connectionId = None
        self._entryList = []

        # Receive methods
        self._receiveMethods = \
        {
            1: self._receive_registration_result,
            2: self._receive_realtime_update,
            3: self._receive_realtime_car_udpate,
            4: self._receive_entry_list,
            5: self._receive_track_data,
            6: self._receive_entry_list_car,
            7: self._receive_broadcasting_event
        }

        # Thread
        self._stopSignal = False
        self._thread = None

    @property
    def onConnectionStateChange(self):
        return self._onConnectionStateChange

    @property
    def onTrackDataUpdate(self):
        return self._onTrackDataUpdate

    @property
    def onEntryListCarUpdate(self):
        return self._onEntryListCarUpdate

    @property
    def onRealtimeUpdate(self):
        return self._onRealtimeUpdate

    @property
    def onRealtimeCarUpdate(self):
        return self._onRealtimeCarUpdate

    @property
    def onBroadcastingEvent(self):
        return self._onBroadcastingEvent

    def _send(self, *fmtValuePairs):
        fmt = "!"
        values = []
        for f, v in fmtValuePairs:
            if f == "s":
                encoded = v.encode("utf8")
                length = len(encoded)
                fmt += "I"
                values.append(length)
                if length > 0:
                    fmt += f"{length}s"
                    values.append(encoded)
            else:
                fmt += f
                values.append(v)
        self._socket.sendto(struct.pack(fmt, *values), self._server)

    def _receive(self, fmt):
        out = []
        for f in fmt:
            if f == "s":
                length, = struct.unpack("!H", self._socket.recv(2))
                if length > 0:
                    out.append(self._socket.recv(length).decode("utf8"))
                else:
                    out.append("")
            else:
                val, = struct.unpack(f"!{f}", self._socket.recv(struct.calcsize(f)))
                out.append(val)
        return out

    def _receive_registration_result(self):
        result = RegistrationResult.receive(self._receive)
        if not result.success:
            self.stop()
            for callback in self._onConnectionStateChange.callbacks:
                callback(Event(self, state = f"rejected ({result.errorMessage})"))
        for callback in self._onConnectionStateChange.callbacks:
            callback(Event(self, state = "established"))
        self._request_entry_list()
        self._request_track_data()

    def _receive_realtime_update(self):
        args = RealtimeUpdate.receive_args(self._receive)
        for callback in self._onRealtimeUpdate.callbacks:
            update = RealtimeUpdate(*args)
            callback(Event(self, update = update))

    def _receive_realtime_car_udpate(self):
        args = RealtimeCarUpdate.receive_args(self._receive)
        update = RealtimeCarUpdate(*args)
        if update.carIndex in self._cars and self._cars[update.carIndex] == update.driverCount:
            for callback in self._onRealtimeCarUpdate.callbacks:
                update = RealtimeCarUpdate(*args)
                callback(Event(self, update = update))
        else:
            self._request_entry_list()

    def _receive_entry_list(self):
        entryList = EntryList.receive(self._receive)
        self._cars = {i: self._cars[i] if i in self._cars else -1 for i in entryList.carIndices}

    def _receive_entry_list_car(self):
        args = EntryListCar.receive_args(self._receive)
        car = EntryListCar(*args)
        self._cars[car.carIndex] = len(car.drivers)
        for callback in self._onEntryListCarUpdate.callbacks:
            car = EntryListCar(*args)
            callback(Event(self, car = car))

    def _receive_track_data(self):
        args = TrackData.receive_args(self._receive)
        for callback in self._onTrackDataUpdate.callbacks:
            data = TrackData(*args)
            callback(Event(self, data = data))

    def _receive_broadcasting_event(self):
        args = BroadcastingEvent.receive_args(self._receive)
        for callback in self._onBroadcastingEvent.callbacks:
            event = BroadcastingEvent(*args)
            callback(Event(self, event = event))

    def _request_connection(
        self,
        displayName: str,
        password: str,
        updateIntervalMs: int,
        commandPassword: str
    ):
        self._send(
            ("B", OutboundMessageTypes.REGISTER_COMMAND_APPLICATION.value),
            ("B", self._broadcastingProtocolVersion),
            ("s", displayName),
            ("s", password),
            ("i", self._updateIntervalMs),
            ("s", commandPassword)
        )

    def _request_disconnection(self):
        self._send(("B", OutboundMessageTypes.UNREGISTER_COMMAND_APPLICATION.value))

    def _request_entry_list(self):
        self._send(
            ("B", OutboundMessageTypes.REQUEST_ENTRY_LIST.value),
            ("i", self._connectionId)
        )

    def _request_track_data(self):
        self._send(
            ("B", OutboundMessageTypes.REQUEST_TRACK_DATA.value),
            ("i", self._connectionId)
        )

    def request_focus_change(
        self,
        carIndex: int = -1,
        cameraSet: str = None,
        camera: str = None
    ):
        # Base message
        args = \
        [
            ("B", OutboundMessageTypes.CHANGE_FOCUS.value),
            ("i", self._connectionId),
        ]

        # Change focused car
        if carIndex >= 0:
            args.extend([
                ("?", True),
                ("H", carIndex)
            ])
        else:
            args.append(("?", False))

        # Change camera
        if cameraSet and camera:
            args.extend([
                ("?", True),
                ("s", cameraSet),
                ("s", camera)
            ])
        else:
            args.append(("?", False))

        # Send
        self._send(*args)

    def request_instant_replay(
        self,
        startTime: float,
        durationMs: float,
        carIndex: int = -1,
        cameraSet: str = "",
        camera: str = ""
    ):
        self._send(
            ("B", OutboundMessageTypes.INSTANT_REPLAY_REQUEST.value),
            ("i", self._connectionId),
            ("f", startTime),
            ("f", durationMs),
            ("i", carIndex),
            ("s", cameraSet),
            ("s", camera)
        )

    def request_hud_page(self, pageName: str):
        self._send(
            ("B", OutboundMessageTypes.CHANGE_HUD_PAGE.value),
            ("i", self._connectionId),
            ("s", pageName)
        )

    def _run(self):
        while not self._stopSignal:
            try:
                messageType = self._receive("B")
            except ConnectionResetError:
                for callback in self._onConnectionStateChange.callbacks:
                    callback(Event(self, state = "lost"))
                break
            self._receiveMethods[messageType]()
        self._socket.close()
        self._socket = None

    @property
    def isAlive(self):
        if self._thread is None:
            return False
        return self._thread.isAlive()

    def start(
        self,
        url: str,
        port: int,
        password: str,
        commandPassword: str = ""
    ):
        if self.isAlive:
            raise ValueError("Must be disconnected")
        self._server = (url, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(1)
        self._connectionId = None
        self._writable = False
        self._request_connection(
            self._displayName,
            password,
            self._updateIntervalMs,
            commandPassword
        )
        self._thread = Thread(target = self._run)
        self._thread.setDaemon(True)
        self._stopSignal = False
        self._thread.start()

    def stop(self):
        if not self.isAlive:
            raise ValueError("Must be connected")
        self._stopSignal = True
        self._thread.join()
        self._thread = None
