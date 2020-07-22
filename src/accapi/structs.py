class RegistrationResult(object):

    def __init__(self, *args):
        args = list(args)
        self.connectionId = args.pop(0)
        self.success = args.pop(0)
        self.writable = args.pop(0)
        self.errorMessage = args.pop(0)

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("i??s")
        return args

class RealtimeUpdate(object):

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
        self.carCount = args.pop(0)
        self.carIndices = []
        for _ in range(self.carCount):
            self.carIndices.append(args.pop(0))

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("iH")
        args.extend(receiveMethod("H" * args[-1]))
        return args

class EntryListCar(object):

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("HBsiBBHB")
        driverCount = args[-1]
        args.extend(receiveMethod("sssBH" * driverCount))
        return args

class TrackData(object):

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

    @classmethod
    def receive(cls, receiveMethod):
        return cls(*cls.receive_args(receiveMethod))

    @staticmethod
    def receive_args(receiveMethod):
        args = receiveMethod("Bsii")
        return args
