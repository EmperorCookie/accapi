import struct

from .enums import *

_MAX_INT = 2 ** 31 - 1


def unpack_next(msg: list, fmt):
    out = []
    for f in fmt:
        if f == "s":
            length, = struct.unpack("<H", bytes(msg[:2]))
            del msg[:2]
            if length > 0:
                out.append(bytes(msg[:length]).decode("utf8"))
                del msg[:length]
            else:
                out.append("")
        else:
            fmt_size = struct.calcsize(f)
            val, = struct.unpack(f"<{f}", bytes(msg[:fmt_size]))
            del msg[:fmt_size]
            out.append(val)
    return out


class RegistrationResult(object):

    def __init__(self, *args):
        args = list(args)
        self.connectionId = args.pop(0)
        self.success = args.pop(0)
        self.writable = args.pop(0)
        self.errorMessage = args.pop(0)
        self._leftovers = args

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        return unpack_next(msg, "i??s")


class RealtimeUpdate(object):

    def __init__(self, *args):
        args = list(args)
        self.eventIndex = args.pop(0)
        self.sessionIndex = args.pop(0)
        self.sessionType = SESSION_TYPE[args.pop(0)]
        self.sessionPhase = SESSION_PHASE[args.pop(0)]
        self.sessionTime = args.pop(0) * 1000
        self.sessionEndTime = args.pop(0) * 1000
        self.focusedCarIndex = args.pop(0)
        self.activeCameraSet = args.pop(0)
        self.activeCamera = args.pop(0)
        self.currentHudPage = args.pop(0)
        self.isReplayPlaying = args.pop(0)
        if self.isReplayPlaying:
            self.replaySessionTime = args.pop(0)
            self.replayRemainingTime = args.pop(0)
        else:
            self.replaySessionTime = 0
            self.replayRemainingTime = 0
        self.timeOfDay = args.pop(0) * 1000
        self.ambientTemp = args.pop(0)
        self.trackTemp = args.pop(0)
        self.clouds = args.pop(0) / 10
        self.rainLevel = args.pop(0) / 10
        self.wetness = args.pop(0) / 10
        self.bestSessionLap = Lap(*args)
        self._leftovers = args

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        args = unpack_next(msg, "HHBBffisss?")
        if args[-1]:
            args.extend(unpack_next(msg, "ff"))
        args.extend(unpack_next(msg, "fBBBBB"))
        args.extend(Lap.parse(msg))
        return args


class Lap(object):

    def __init__(self, *args):
        args = list(args)
        self.lapTime = args.pop(0) * 1000
        self.carIndex = args.pop(0)
        self.driverIndex = args.pop(0)
        self.splits = [args.pop(0) for _ in range(args.pop(0))]
        if len(self.splits) < 3:
            self.splits.extend([None] * (3 - len(self.splits)))
        self.isInvalid = args.pop(0)
        self.isValidForBest = args.pop(0)
        self.isOutlap = args.pop(0)
        self.isInlap = args.pop(0)
        self.type = LAP_TYPE[1 if self.isOutlap else 0 + 2 if self.isInlap else 0]
        self._leftovers = args

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        args = unpack_next(msg, "iHHB")
        args.extend(unpack_next(msg, "i" * args[-1]))
        args.extend(unpack_next(msg, "????"))
        return args


class RealtimeCarUpdate(object):

    def __init__(self, *args):
        args = list(args)
        self.carIndex = args.pop(0)
        self.driverIndex = args.pop(0)
        self.driverCount = args.pop(0)
        self.gear = args.pop(0) - 2
        self.worldPosX = args.pop(0)
        self.worldPosY = args.pop(0)
        self.yaw = args.pop(0)
        self.location = CAR_LOCATION[args.pop(0)]
        self.kmh = args.pop(0)
        self.position = args.pop(0)
        self.cupPosition = args.pop(0)
        self.trackPosition = args.pop(0)
        self.splinePosition = args.pop(0)
        self.laps = args.pop(0)
        self.delta = args.pop(0)
        self.bestSessionLap = Lap(*args)
        self.lastLap = Lap(*self.bestSessionLap._leftovers)
        self.currentLap = Lap(*self.lastLap._leftovers)
        self._leftovers = self.currentLap._leftovers

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        args = unpack_next(msg, "HHBBfffBHHHHfHi")
        for _ in range(3):
            args.extend(Lap.parse(msg))
        return args


class EntryList(object):

    def __init__(self, *args):
        args = list(args)
        self.connectionId = args.pop(0)
        self.carIndices = [args.pop(0) for _ in range(args.pop(0))]
        self._leftovers = args

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        args = unpack_next(msg, "iH")
        args.extend(unpack_next(msg, "H" * args[-1]))
        return args


class Driver(object):

    def __init__(self, *args):
        args = list(args)
        self.firstName = args.pop(0)
        self.lastName = args.pop(0)
        self.shortName = args.pop(0)
        self.category = DRIVER_CATEGORY[args.pop(0)]
        self.nationality = NATIONALITY[args.pop(0)]
        self._leftovers = args

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        args = unpack_next(msg, "sssBH")
        return args


class EntryListCar(object):

    def __init__(self, *args):
        args = list(args)
        self.carIndex = args.pop(0)
        self.modelType = args.pop(0)
        self.teamName = args.pop(0)
        self.raceNumber = args.pop(0)
        self.cupCategory = args.pop(0)
        self.currentDriverIndex = args.pop(0)
        self.nationality = NATIONALITY[args.pop(0)]
        self.drivers = []
        for _ in range(args.pop(0)):
            self.drivers.append(Driver(*args))
            args = self.drivers[-1]._leftovers
        self._leftovers = args

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        args = unpack_next(msg, "HBsiBBHB")
        for _ in range(args[-1]):
            args.extend(Driver.parse(msg))
        return args


class TrackData(object):

    def __init__(self, *args):
        args = list(args)
        self.connectionId = args.pop(0)
        self.trackName = args.pop(0)
        self.trackId = args.pop(0)
        self.trackMeters = args.pop(0)
        self.cameraSets = {args.pop(0): [args.pop(0) for _ in range(args.pop(0))] for _ in range(args.pop(0))}
        self.hudPages = [args.pop(0) for _ in range(args.pop(0))]
        self._leftovers = args

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        args = unpack_next(msg, "isiiB")
        for _ in range(args[-1]):
            args.extend(unpack_next(msg, "sB"))
            args.extend(unpack_next(msg, "s" * args[-1]))
        args.extend(unpack_next(msg, "B"))
        args.extend(unpack_next(msg, "s" * args[-1]))
        return args


class BroadcastingEvent(object):

    def __init__(self, *args):
        args = list(args)
        self.type = BROADCASTING_EVENT_TYPE[args.pop(0)]
        self.message = args.pop(0)
        self.time = args.pop(0) * 1000
        self.carIndex = args.pop(0)
        self._leftovers = args

    @classmethod
    def from_message(cls, msg):
        return cls(*cls.parse(msg))

    @staticmethod
    def parse(msg):
        args = unpack_next(msg, "Bsii")
        return args
