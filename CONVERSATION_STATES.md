# Stati Conversazione CarabinieriPayBot

## Stati Definiti in config/settings.py:
1. SELECT_DATE - Selezione data servizio
2. SETUP_RANK - Setup iniziale: selezione grado
3. SETUP_COMMAND - Setup iniziale: inserimento comando
4. SETUP_IRPEF - Setup iniziale: selezione IRPEF
5. SETUP_LEAVE - Setup iniziale: licenze residue
6. SELECT_TIME - Selezione orario servizio
7. SELECT_SERVICE_TYPE - Selezione tipo servizio
8. SERVICE_DETAILS - Dettagli servizio generico
9. TRAVEL_DETAILS - Dettagli foglio viaggio
10. TRAVEL_TYPE - Tipo viaggio/missione
11. MEAL_DETAILS - Dettagli pasti
12. CONFIRM_SERVICE - Conferma servizio
13. PAYMENT_DETAILS - [NON USATO - rimosso]
14. SELECT_TRAVEL_SHEETS - [NON USATO - rimosso]
15. LEAVE_DATES - Date licenza
16. LEAVE_TYPE - Tipo licenza

## Mappatura Stati per Handler:
- service_conversation_handler: USA stati 1, 6-12
- setup_conversation_handler: USA stati 2-5
- leave handlers: USANO stati 15-16
