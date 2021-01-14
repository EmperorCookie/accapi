from threading import Thread, Condition
import socket
import struct
import time

from .enums import OutboundMessageTypes
from .structs import \
    RegistrationResult, \
    RealtimeUpdate, \
    RealtimeCarUpdate, \
    EntryList, \
    EntryListCar, \
    TrackData, \
    BroadcastingEvent

__all__ = ["AccClient"]

class EndOfStreamError(Exception):
    pass

class ThreadedSocketReader(object):
    """
    Reads from a socket continuously and provides a non-blocking read method.

    Args:
        source (socket.socket): A socket instance.
        chunkSize (int): The data will be read in chunks of the given size.

    Attributes:
        isAlive (bool): The reader will terminate its thread if the source has been closed.
        size (int): How much data has been read so far.
    """
    def __init__(self, source:socket.socket, chunkSize = 1024):
        self._source = source
        self._chunkSize = chunkSize
        self._data = bytearray()
        self._dataLock = Condition()
        self._stopSignal = False
        self._thread = Thread(target = self._run)
        self._thread.setDaemon(True)
        self._thread.start()
        self._exception = None

    @property
    def isAlive(self):
        if self._thread is None:
            return False
        return self._thread.isAlive()

    @property
    def size(self):
        self._dataLock.acquire()
        size = len(self._data)
        self._dataLock.release()
        return size

    def read(self, size = None, timeout: int = None):
        """
        Reads data from the stream.

        Args:
            size (int): Number of bytes to read, or None to read everything that is available.
            timeout (float): Only used if size is not None. Number of seconds to wait for the method
                to return data, or None.

        Returns:
            bytes: The requested data, or None.
        """
        # Raise exception if no data will ever come in
        self._dataLock.acquire()
        if not self.isAlive and (not self._data or (size is not None and len(self._data) < size)):
            self._dataLock.release()
            if self._exception is not None:
                raise self._exception
            else:
                raise EndOfStreamError()

        # Return all available data
        if size is None:
            if len(self._data) > 0:
                data = bytes(self._data)
                self._data = bytearray()
            else:
                data = None

        # Return specified amount of data
        else:

            # Wait until there's enough data to fulfill the request
            if len(self._data) < size:
                if not self._dataLock.wait(timeout):
                    return None

            # Slice data according to size
            data = bytes(self._data[:size])
            del self._data[:size]

        # Release and return
        self._dataLock.release()
        return data

    def stop(self):
        """
        Signals the reader to stop.
        """
        self._stopSignal = True
        self._thread = None

    def _run(self):
        while not self._stopSignal:
            try:
                data = self._source.recv(self._chunkSize)
            except socket.timeout:
                continue
            except Exception as e:
                self._exception = e
                break
            self._dataLock.acquire()
            self._data.extend(data)
            self._dataLock.notify_all()
            self._dataLock.release()

class Event(object):
    def __init__(self, source, content):
        self.source = source
        self.content = content

class Observable(object):
    def __init__(self):
        self._callbacks = []

    @property
    def callbacks(self):
        return self._callbacks[:]

    def subscribe(self, callback):
        self._callbacks.append(callback)

class AccClient(object):

    endianess = "<"

    def __init__(self):
        self._server = (None, None)
        self._displayName = None
        self._updateIntervalMs = 100
        self._socket = None
        self._connectionState = "disconnected"

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
        self._writable = False
        self._entryList = []
        self._cars = {}

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
        self._reader = None

    def _update_connection_state(self, state):
        if state != self._connectionState:
            self._connectionState = state
            for callback in self._onConnectionStateChange.callbacks:
                callback(Event(self, content = self._connectionState))

    @property
    def connectionState(self):
        return self._connectionState

    @property
    def writable(self):
        return self._writable

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
        if not self.isAlive:
            raise ValueError("Must be started")
        fmt = self.endianess
        values = []
        for f, v in fmtValuePairs:
            if f == "s":
                encoded = v.encode("utf8")
                length = len(encoded)
                fmt += "H"
                values.append(length)
                if length > 0:
                    fmt += f"{length}s"
                    values.append(encoded)
            else:
                fmt += f
                values.append(v)
        packed = struct.pack(fmt, *values)
        self._socket.sendto(packed, self._server)

    def _receive(self, fmt):
        out = []
        for f in fmt:
            if f == "s":
                length, = struct.unpack(f"{self.endianess}H", self._reader.read(2))
                if length > 0:
                    out.append(self._reader.read(length).decode("utf8"))
                else:
                    out.append("")
            else:
                val, = struct.unpack(f"{self.endianess}{f}", self._reader.read(struct.calcsize(f)))
                out.append(val)
        return out

    def _receive_registration_result(self):
        result = RegistrationResult.receive(self._receive)
        if not result.success:
            self._stop(state = f"rejected ({result.errorMessage})")
        self._connectionId = result.connectionId
        self._writable = result.writable
        self._update_connection_state("established")
        self._request_entry_list()
        self._request_track_data()

    def _receive_realtime_update(self):
        args = RealtimeUpdate.receive_args(self._receive)
        for callback in self._onRealtimeUpdate.callbacks:
            update = RealtimeUpdate(*args)
            callback(Event(self, update))

    def _receive_realtime_car_udpate(self):
        args = RealtimeCarUpdate.receive_args(self._receive)
        update = RealtimeCarUpdate(*args)
        if update.carIndex in self._cars and self._cars[update.carIndex] == update.driverCount:
            for callback in self._onRealtimeCarUpdate.callbacks:
                update = RealtimeCarUpdate(*args)
                callback(Event(self, update))
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
            callback(Event(self, car))

    def _receive_track_data(self):
        args = TrackData.receive_args(self._receive)
        for callback in self._onTrackDataUpdate.callbacks:
            data = TrackData(*args)
            callback(Event(self, data))

    def _receive_broadcasting_event(self):
        args = BroadcastingEvent.receive_args(self._receive)
        for callback in self._onBroadcastingEvent.callbacks:
            event = BroadcastingEvent(*args)
            callback(Event(self, event))

    def _request_connection(
        self,
        password: str,
        commandPassword: str
    ):
        self._send(
            ("B", OutboundMessageTypes.REGISTER_COMMAND_APPLICATION.value),
            ("B", self._broadcastingProtocolVersion),
            ("s", self._displayName),
            ("s", password),
            ("i", self._updateIntervalMs),
            ("s", commandPassword)
        )

    def _request_disconnection(self):
        self._send(
            ("B", OutboundMessageTypes.UNREGISTER_COMMAND_APPLICATION.value),
            ("i", self._connectionId)
        )

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
        try:
            while not self._stopSignal:
                try:
                    messageTypeData = self._reader.read(1, timeout = 0.1)
                except (ConnectionResetError, EndOfStreamError):
                    self._update_connection_state("lost")
                    break
                if messageTypeData is None:
                    continue
                messageType, = struct.unpack("B", messageTypeData)
                self._receiveMethods[messageType]()
        finally:
            try:
                self._request_disconnection()
            except:
                pass
        self._reader.stop()
        self._reader = None
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
        commandPassword: str = "",
        displayName: str = "Python ACCAPI",
        updateIntervalMs: int = 100
    ):
        if self.isAlive:
            raise ValueError("Must be stopped")
        self._update_connection_state("connecting")
        self._server = (url, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(1)
        self._reader = ThreadedSocketReader(self._socket)
        self._thread = Thread(target = self._run)
        self._stopSignal = False
        self._thread.start()
        self._connectionId = None
        self._writable = False
        self._displayName = displayName
        self._updateIntervalMs = updateIntervalMs
        self._request_connection(
            password,
            commandPassword
        )

    def stop(self):
        if not self.isAlive:
            raise ValueError("Must be started")
        self._stop()

    def _stop(self, state = "disconnected"):
        self._stopSignal = True
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self._update_connection_state(state)
