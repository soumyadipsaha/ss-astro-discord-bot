VEDIC_COMMAND = {
    "name": "vedic",
    "description": "Sidereal (Lahiri) positions of the Ascendant and the Hindu Navagraha.",
    "options": [
        {
            "name": "year",
            "description": "Year of birth (e.g. 1990)",
            "type": 4,
            "required": True,
        },
        {
            "name": "month",
            "description": "Month of birth (1–12)",
            "type": 4,
            "required": True,
            "min_value": 1,
            "max_value": 12,
        },
        {
            "name": "day",
            "description": "Day of birth (1–31)",
            "type": 4,
            "required": True,
            "min_value": 1,
            "max_value": 31,
        },
        {
            "name": "hour",
            "description": "Hour of birth, 24h (0–23)",
            "type": 4,
            "required": True,
            "min_value": 0,
            "max_value": 23,
        },
        {
            "name": "minute",
            "description": "Minute of birth (0–59)",
            "type": 4,
            "required": True,
            "min_value": 0,
            "max_value": 59,
        },
        {
            "name": "lat",
            "description": "Latitude of the birth place (e.g. 28.6139 for Delhi)",
            "type": 10,
            "required": True,
        },
        {
            "name": "lon",
            "description": "Longitude of the birth place (e.g. 77.2090 for Delhi)",
            "type": 10,
            "required": True,
        },
        {
            "name": "tz",
            "description": "UTC offset at birth (e.g. 5.5 for IST, -4 for EDT)",
            "type": 10,
            "required": True,
        },
        {
            "name": "chalit",
            "description": "Add Sripati (Porphyry) bhava/house placements for each graha.",
            "type": 5,
            "required": False,
        },
    ],
}

COMMANDS = [VEDIC_COMMAND]
