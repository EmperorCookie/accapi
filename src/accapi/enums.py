from enum import Enum

__all__ = [
    "OutboundMessageTypes",
    "LAP_TYPE",
    "DRIVER_CATEGORY",
    "CAR_LOCATION",
    "SESSION_PHASE",
    "SESSION_TYPE",
    "BROADCASTING_EVENT_TYPE",
    "NATIONALITY",
]


class MissingHandlingDict(dict):
    def __missing__(self, k):
        return f"Not found ({k})"


class OutboundMessageTypes(Enum):
    REGISTER_COMMAND_APPLICATION = 1
    UNREGISTER_COMMAND_APPLICATION = 9

    REQUEST_ENTRY_LIST = 10
    REQUEST_TRACK_DATA = 11

    CHANGE_HUD_PAGE = 49
    CHANGE_FOCUS = 50
    INSTANT_REPLAY_REQUEST = 51

    PLAY_MANUAL_REPLAY_HIGHLIGHT = 52
    SAVE_MANUAL_REPLAY_HIGHLIGHT = 60


LAP_TYPE = {
    0: "Regular",
    1: "Outlap",
    2: "Inlap",
}

DRIVER_CATEGORY = {
    0: "Bronze",
    1: "Silver",
    2: "Gold",
    3: "Platinum",
    255: "Unknown",
}

CAR_LOCATION = {
    0: "Unknown",
    1: "Track",
    2: "Pitlane",
    3: "Pit Entry",
    4: "Pit Exit",
}

SESSION_PHASE = {
    0: "Unknown",
    1: "Starting",
    2: "Pre Formation",
    3: "Formation Lap",
    4: "Pre Session",
    5: "Session",
    6: "Session Over",
    7: "Post Session",
    8: "Result UI",
}

SESSION_TYPE = {
    0: "Practice",
    4: "Qualifying",
    9: "Superpole",
    10: "Race",
    11: "Hotlap",
    12: "Hot Stint",
    13: "Hotlap Superpole",
    14: "Replay",
}

BROADCASTING_EVENT_TYPE = {
    0: "Unknown",
    1: "Green Flag",
    2: "Session Over",
    3: "Penalty Communication Message",
    4: "Accident",
    5: "Lap Completed",
    6: "Best Session Lap",
    7: "Best Personal Lap",
}

NATIONALITY = MissingHandlingDict({
    0: "Unknown",
    1: "Italy",
    2: "Germany",
    3: "France",
    4: "Spain",
    5: "GreatBritain",
    6: "Hungary",
    7: "Belgium",
    8: "Switzerland",
    9: "Austria",
    10: "Russia",
    11: "Thailand",
    12: "Netherlands",
    13: "Poland",
    14: "Argentina",
    15: "Monaco",
    16: "Ireland",
    17: "Brazil",
    18: "SouthAfrica",
    19: "PuertoRico",
    20: "Slovakia",
    21: "Oman",
    22: "Greece",
    23: "SaudiArabia",
    24: "Norway",
    25: "Turkey",
    26: "SouthKorea",
    27: "Lebanon",
    28: "Armenia",
    29: "Mexico",
    30: "Sweden",
    31: "Finland",
    32: "Denmark",
    33: "Croatia",
    34: "Canada",
    35: "China",
    36: "Portugal",
    37: "Singapore",
    38: "Indonesia",
    39: "USA",
    40: "NewZealand",
    41: "Australia",
    42: "SanMarino",
    43: "UAE",
    44: "Luxembourg",
    45: "Kuwait",
    46: "HongKong",
    47: "Colombia",
    48: "Japan",
    49: "Andorra",
    50: "Azerbaijan",
    51: "Bulgaria",
    52: "Cuba",
    53: "CzechRepublic",
    54: "Estonia",
    55: "Georgia",
    56: "India",
    57: "Israel",
    58: "Jamaica",
    59: "Latvia",
    60: "Lithuania",
    61: "Macau",
    62: "Malaysia",
    63: "Nepal",
    64: "NewCaledonia",
    65: "Nigeria",
    66: "NorthernIreland",
    67: "PapuaNewGuinea",
    68: "Philippines",
    69: "Qatar",
    70: "Romania",
    71: "Scotland",
    72: "Serbia",
    73: "Slovenia",
    74: "Taiwan",
    75: "Ukraine",
    76: "Venezuela",
    77: "Wales",
})
