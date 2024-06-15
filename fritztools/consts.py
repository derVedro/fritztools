"""
Constants for fritztools.
"""


class WIFI:
    NAMES = {
        1: "2.4GHz",
        2: "5GHz",
        3: "guests",
    }

    FREQ_STR = {
        "2400": "2.4GHz",
        "5000": "5GHz",
        "6000": "6GHz",
        "unknown": "-",
    }

    NAMES_TO_CONNECTION_NUMBERS = {
        "1": [1],
        "2": [2],
        "3": [3],
        "2.4": [1],
        "2.4GHz": [1],
        "5": [2],
        "5GHz": [2],
        "guests": [3],
        "guest": [3],
        "first": [1],
        "second": [2],
        "third": [3],
        "all": [1, 2, 3],
    }
