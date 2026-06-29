VEDIC_COMMAND = {
    "name": "vedic",
    "description": "Sidereal (Lahiri) positions of the Ascendant and the Hindu Navagraha.",
    "options": [
        {
            "name": "date",
            "description": "Date of birth (YYYY-MM-DD)",
            "type": 3,
            "required": True,
        },
        {
            "name": "time",
            "description": "Time of birth at the location, 24h (HH:MM)",
            "type": 3,
            "required": True,
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
