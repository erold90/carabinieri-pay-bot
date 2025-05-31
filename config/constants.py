"""
Constants for CarabinieriPayBot - VERSIONE CORRETTA
All amounts are GROSS where specified
"""

# Overtime rates (NET per hour)
OVERTIME_RATES = {
    'weekday_day': 10.55,      # Feriale Diurno
    'weekday_night': 11.95,    # Feriale Notturno
    'holiday_day': 11.95,      # Festivo Diurno
    'holiday_night': 13.78     # Festivo Notturno
}

# Service allowances (NET per day)
SERVICE_ALLOWANCES = {
    'external_service': 5.45,
    'holiday_presence': 12.70,
    'super_holiday_presence': 36.00,
    'compensation': 10.90,
    'territory_control_evening': 4.50,
    'territory_control_night': 9.00
}

# Super holidays
SUPER_HOLIDAYS = [
    (12, 25), (12, 26), (1, 1), (5, 1), (6, 2), (8, 15)
]

# Mission rates DIFFERENZIATE PER GRADO
MISSION_RATES_BY_RANK = {
    # Non Dirigenti (fino a Capitano)
    'non_dirigente': {
        'daily_allowance': 20.45,
        'hourly_allowance': 0.86,
        'meal_limit_gross': 22.26,
        'meal_limit_net': 14.29,
        'double_meal_gross': 44.52,
        'double_meal_net': 28.58
    },
    # Dirigenti fino a Gen. Brigata
    'dirigente_base': {
        'daily_allowance': 20.45,
        'hourly_allowance': 0.86,
        'meal_limit_gross': 30.55,
        'meal_limit_net': 19.61,
        'double_meal_gross': 61.10,
        'double_meal_net': 39.22
    },
    # Gen. Divisione
    'dirigente_divisione': {
        'daily_allowance': 24.12,
        'hourly_allowance': 1.01,
        'meal_limit_gross': 30.55,
        'meal_limit_net': 19.61,
        'double_meal_gross': 61.10,
        'double_meal_net': 39.22
    },
    # Gen. C.A.
    'dirigente_ca': {
        'daily_allowance': 28.82,
        'hourly_allowance': 1.20,
        'meal_limit_gross': 30.55,
        'meal_limit_net': 19.61,
        'double_meal_gross': 61.10,
        'double_meal_net': 39.22
    }
}

# Riduzioni indennità missione
MISSION_REDUCTIONS = {
    'one_meal': 0.50,      # 50% con un pasto
    'two_meals': 0.40,     # 40% con due pasti
    'free_lodging': 0.67,  # 2/3 con alloggio gratuito
    'free_meals': 0.60,    # 60% con vitto gratuito
    'both_free': 0.40      # 40% con vitto e alloggio
}

# Rimborso chilometrico
FUEL_REIMBURSEMENT = {
    'benzina_1_5': 0.35,  # 1/5 prezzo benzina (aggiornare)
    'percorsi_non_serviti_base': 0.1069,
    'percorsi_non_serviti_speciali': 0.1585
}

# Indennità supplementari biglietti
TICKET_SUPPLEMENTS = {
    'treno_nave': 0.10,  # 10%
    'aereo': 0.05        # 5%
}

# Mapping gradi -> categoria
RANK_CATEGORIES = {
    'Carabiniere': 'non_dirigente',
    'Carabiniere Scelto': 'non_dirigente',
    'Appuntato': 'non_dirigente',
    'Appuntato Scelto QS': 'non_dirigente',
    'Vice Brigadiere': 'non_dirigente',
    'Brigadiere': 'non_dirigente',
    'Brigadiere CA QS': 'non_dirigente',
    'Maresciallo': 'non_dirigente',
    'Maresciallo Ordinario': 'non_dirigente',
    'Maresciallo Capo': 'non_dirigente',
    'Maresciallo Aiutante': 'non_dirigente',
    'Maresciallo Aiutante QS': 'non_dirigente',
    'Luogotenente': 'non_dirigente',
    'Luogotenente QS': 'non_dirigente',
    'Sottotenente': 'non_dirigente',
    'Tenente': 'non_dirigente',
    'Capitano': 'non_dirigente',
    'Maggiore': 'dirigente_base',
    'Tenente Colonnello': 'dirigente_base',
    'Colonnello': 'dirigente_base',
    'Generale di Brigata': 'dirigente_base',
    'Generale di Divisione': 'dirigente_divisione',
    "Generale di Corpo d'Armata": 'dirigente_ca'
}

# Ranks list (aggiornata con gradi dirigenti)
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
    'Capitano',
    'Maggiore',
    'Tenente Colonnello',
    'Colonnello',
    'Generale di Brigata',
    'Generale di Divisione',
    "Generale di Corpo d'Armata"
]

# Forfeit rates (NET)
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

# IRPEF tax brackets
IRPEF_BRACKETS = [
    (15000, 0.23),
    (28000, 0.25),
    (50000, 0.35),
    (float('inf'), 0.43)
]

# Vecchie costanti per retrocompatibilità
MISSION_RATES = MISSION_RATES_BY_RANK['non_dirigente']
MEAL_RATES = {
    'single_meal_gross': MISSION_RATES_BY_RANK['non_dirigente']['meal_limit_gross'],
    'single_meal_net': MISSION_RATES_BY_RANK['non_dirigente']['meal_limit_net'],
    'double_meal_gross': MISSION_RATES_BY_RANK['non_dirigente']['double_meal_gross'],
    'double_meal_net': MISSION_RATES_BY_RANK['non_dirigente']['double_meal_net']
}
