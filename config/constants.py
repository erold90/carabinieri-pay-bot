"""
Constants for CarabinieriPayBot
All amounts are NET (in pocket)
"""

# Overtime rates (NET per hour)
OVERTIME_RATES = {
    'weekday_day': 10.55,      # Feriale Diurno (Lun-Sab 06:00-22:00)
    'weekday_night': 11.95,    # Feriale Notturno (Lun-Sab 22:00-06:00)
    'holiday_day': 11.95,      # Festivo Diurno (Dom/Festivi 06:00-22:00)
    'holiday_night': 13.78     # Festivo Notturno (Dom/Festivi 22:00-06:00)
}

# Service allowances (NET per day)
SERVICE_ALLOWANCES = {
    'external_service': 5.45,           # Servizio Esterno (min 3h continuative)
    'holiday_presence': 12.70,          # Presenza Festiva
    'super_holiday_presence': 36.00,    # Presenza SUPER-FESTIVA
    'compensation': 10.90,              # Compensazione (richiamo da riposo/licenza)
    'territory_control_evening': 4.50,  # Controllo Territorio Serale (18:00-21:59)
    'territory_control_night': 9.00     # Controllo Territorio Notturno (22:00-03:00)
}

# Super holidays (€36 net)
SUPER_HOLIDAYS = [
    (12, 25),  # Natale
    (12, 26),  # Santo Stefano
    (1, 1),    # Capodanno
    # Easter and Easter Monday are calculated dynamically
    (5, 1),    # 1° Maggio
    (6, 2),    # 2 Giugno
    (8, 15)    # Ferragosto
]

# Mission allowances
MISSION_RATES = {
    'travel_hourly': 8.00,      # Maggiorazione viaggio (ore eccedenti)
    'daily_allowance': 20.45,   # Diaria giornaliera (per 24h)
    'hourly_allowance': 0.86,   # Indennità oraria (frazioni)
    'km_rate': 0.35            # Rimborso chilometrico
}

# Meal reimbursements
MEAL_RATES = {
    'single_meal_gross': 22.26,
    'single_meal_net': 14.29,
    'double_meal_gross': 44.52,
    'double_meal_net': 28.58
}

# Forfeit rates (already NET)
FORFEIT_RATES = {
    '24h': 110.00,
    '12h_extra': 50.00
}

# Service types
SERVICE_TYPES = {
    'LOCAL': 'Servizio Locale',
    'ESCORT': 'Servizio Scorta',
    'MISSION': 'Missione Generica'
}

# Ranks
RANKS = [
    'Carabiniere',
    'Carabiniere Scelto',
    'Appuntato',
    'Appuntato Scelto QS',
    'Vice Brigadiere',
    'Brigadiere',
    'Brigadiere CA QS',
    'Maresciallo',
    'Maresciallo Ordinario',
    'Maresciallo Capo',
    'Maresciallo Aiutante',
    'Maresciallo Aiutante QS',
    'Luogotenente',
    'Luogotenente QS',
    'Sottotenente',
    'Tenente',
    'Capitano'
]

# IRPEF tax brackets
IRPEF_BRACKETS = [
    (15000, 0.23),
    (28000, 0.25),
    (50000, 0.35),
    (float('inf'), 0.43)
]