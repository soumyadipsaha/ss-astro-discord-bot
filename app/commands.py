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
            "name": "city",
            "description": "Birth city (e.g. Mumbai, London, New York)",
            "type": 3,
            "required": True,
        },
        {
            "name": "chalit",
            "description": "Add Sripati (Porphyry) bhava/house placements for each graha.",
            "type": 5,
            "required": False,
        },
        {
            "name": "chart_style",
            "description": "Chart style: North Indian (diamond) or South Indian (grid). Default: North.",
            "type": 3,
            "required": False,
            "choices": [
                {"name": "North Indian", "value": "north"},
                {"name": "South Indian", "value": "south"},
            ],
        },
    ],
}

COMMANDS = [VEDIC_COMMAND]
