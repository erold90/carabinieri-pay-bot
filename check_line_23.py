#!/usr/bin/env python3
print("📋 Controllo riga 23 di service_handler.py")
print("=" * 50)

with open('handlers/service_handler.py', 'r') as f:
    lines = f.readlines()

print(f"\nTotale righe: {len(lines)}")
print("\nRighe 20-25:")
for i in range(19, min(25, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')

print("\n" + "=" * 50)
print("\nPrime 30 righe del file:")
for i in range(min(30, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')
