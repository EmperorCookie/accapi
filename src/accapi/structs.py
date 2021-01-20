from .enums import (
    SESSION_TYPE,
    SESSION_PHASE,
    LAP_TYPE,
    CAR_LOCATION,
    DRIVER_CATEGORY,
    NATIONALITY,
    BROADCASTING_EVENT_TYPE,
)

__all__ = [
    "RegistrationResult",
    "RealtimeUpdate",
    "Lap",
    "RealtimeCarUpdate",
    "EntryList",
    "Driver",
    "EntryListCar",
    "TrackData",
    "BroadcastingEvent",
]


class RegistrationResult(object):
    def __init__(self, *args):
        args = list(args)
        self.connectionId = args.pop(0)
        self.success = args.pop(0)
        self.writable = args.pop(0)
        self.errorMessage = args.pop(0)
        self._leftovers = args

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("i??s")
        return args


class RealtimeUpdate(object):
    def __init__(self, *args):
        args = list(args)
        self.eventIndex = args.pop(0)
        self.sessionIndex = args.pop(0)
        self.sessionType = SESSION_TYPE[args.pop(0)]
        self.sessionPhase = SESSION_PHASE[args.pop(0)]
        self.sessionTimeMs = args.pop(0)
        self.sessionEndTimeMs = args.pop(0)
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
        self.timeOfDayMs = args.pop(0)
        self.ambientTemp = args.pop(0)
        self.trackTemp = args.pop(0)
        self.clouds = args.pop(0) / 10
        self.rainLevel = args.pop(0) / 10
        self.wetness = args.pop(0) / 10
        self.bestSessionLap = Lap(*args)
        self._leftovers = self.bestSessionLap._leftovers

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("HHBBffisss?")
        if args[-1]:
            args.extend(receiveMethod("ff"))
        args.extend(receiveMethod("fBBBBB"))
        args.extend(Lap.receive_args(receiveMethod))
        return args


class Lap(object):
    def __init__(self, *args):
        args = list(args)
        self.lapTimeMs = args.pop(0)
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
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("iHHB")
        args.extend(receiveMethod("i" * args[-1]))
        args.extend(receiveMethod("????"))
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
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("HHBBfffBHHHHfHi")
        for _ in range(3):
            args.extend(Lap.receive_args(receiveMethod))
        return args


class EntryList(object):
    def __init__(self, *args):
        args = list(args)
        self.connectionId = args.pop(0)
        self.carIndices = [args.pop(0) for _ in range(args.pop(0))]
        self._leftovers = args

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("iH")
        args.extend(receiveMethod("H" * args[-1]))
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
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("sssBH")
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
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("HBsiBBHB")
        for _ in range(args[-1]):
            args.extend(Driver.receive_args(receiveMethod))
        return args


class TrackData(object):
    def __init__(self, *args):
        args = list(args)
        self.connectionId = args.pop(0)
        self.trackName = args.pop(0)
        self.trackId = args.pop(0)
        self.trackMeters = args.pop(0)
        self.cameraSets = {}
        cameraSetCount = args.pop(0)
        for _ in range(cameraSetCount):
            cameraSetName = args.pop(0)
            self.cameraSets[cameraSetName] = []
            cameraCount = args.pop(0)
            for _ in range(cameraCount):
                cameraName = args.pop(0)
                self.cameraSets[cameraSetName].append(cameraName)
        self.hudPages = []
        hudPageCount = args.pop(0)
        for _ in range(hudPageCount):
            hudPageName = args.pop(0)
            self.hudPages.append(hudPageName)
        self._leftovers = args

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("isiiB")
        for _ in range(args[-1]):
            args.extend(receiveMethod("sB"))
            args.extend(receiveMethod("s" * args[-1]))
        args.extend(receiveMethod("B"))
        args.extend(receiveMethod("s" * args[-1]))
        return args


class BroadcastingEvent(object):
    def __init__(self, *args):
        args = list(args)
        self.type = BROADCASTING_EVENT_TYPE[args.pop(0)]
        self.message = args.pop(0)
        self.timeMs = args.pop(0)
        self.carIndex = args.pop(0)
        self._leftovers = args

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("Bsii")
        return args
