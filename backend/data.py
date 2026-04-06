"""
SmartRescue EMS - Data Models
=============================
Contains static data structures representing the PCMC city map
and the ambulance medical equipment inventory.
"""

# --- City Graph (Adjacency Matrix) ---
# Represents travel times (in minutes) between 5 key PCMC locations.
# Indices: 0=Base, 1=YCM Hospital, 2=Aditya Birla Hospital, 3=PCCOE, 4=Nigdi
# float('inf') indicates no direct road connection between two nodes.

INF = float('inf')

LOCATIONS = ["Base", "YCM Hospital", "Aditya Birla Hospital", "PCCOE", "Nigdi"]

city_graph = [
    #  Base   YCM    Aditya  PCCOE  Nigdi
    [  0,     10,    15,     INF,   20  ],   # Base
    [  10,    0,     35,     25,    INF ],   # YCM Hospital
    [  15,    35,    0,      30,    10  ],   # Aditya Birla Hospital
    [  INF,   25,    30,     0,     5   ],   # PCCOE
    [  20,    INF,   10,     5,     0   ],   # Nigdi
]

# --- Medical Equipment Inventory ---
# Each item has a name, weight (kg), and a life-saving priority value.
# Used by the 0/1 Knapsack algorithm to optimize ambulance packing.

inventory_db = [
    {"name": "Defibrillator",       "weight": 5,  "value": 90},
    {"name": "Oxygen Cylinder",     "weight": 10, "value": 75},
    {"name": "Trauma Kit",          "weight": 3,  "value": 60},
    {"name": "Blood Supply Unit",   "weight": 8,  "value": 80},
    {"name": "Spinal Board",        "weight": 7,  "value": 50},
]
