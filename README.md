# laser-array

Sterowanie macierzą laserów (on/off) z Resolume Arena przez Art-Net.

Raspberry Pi 5 odbiera Art-Net, mapuje kanały DMX na tablicę stanów wyjść i wysyła ją przez SPI do łańcucha 74HC595 → ULN2803A → lasery.
Liczba wyjść jest konfigurowalna (8 na start, docelowo 16/32/64/…/256+).

## Etapy
1. [Podstawy: Pi + 1× 74HC595 + ULN2803A](docs/etap1.md) – podłączenie i test wyjść (`tools/test_outputs.py`)
2. Odbiór Art-Net z Resolume (w przygotowaniu)
# laser-array
