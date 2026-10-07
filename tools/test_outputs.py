#!/usr/bin/env python3
"""Etap 1: test łańcucha 74HC595 -> ULN2803A przez SPI.

Podłączenie (numery fizycznych pinów Raspberry Pi):
  pin 19  GPIO10 / SPI MOSI  -> 74HC595 pin 14 (SER)
  pin 23  GPIO11 / SPI SCLK  -> 74HC595 pin 11 (SRCLK)
  pin 24  GPIO8  / SPI CE0   -> 74HC595 pin 12 (RCLK, zatrzask)
  pin 31  GPIO6              -> 74HC595 pin 13 (OE, aktywne niskim, + 10k do 3.3V)

Liczba wyjść jest parametrem (--outputs), więc ten sam skrypt działa
dla 8, 16, 64... wyjść po dołożeniu kolejnych 74HC595 w łańcuchu.
"""
import argparse
import time

import spidev
from gpiozero import DigitalOutputDevice

OE_GPIO = 6          # BCM
SPI_BUS, SPI_DEV = 0, 0
SPI_HZ = 1_000_000   # 1 MHz: bezpiecznie nawet na płytce stykowej


class ShiftRegisterChain:
    """Łańcuch N rejestrów 74HC595. Stan to lista bool, indeks = numer wyjścia."""

    def __init__(self, outputs: int):
        if outputs % 8:
            raise ValueError("liczba wyjść musi być wielokrotnością 8")
        self.outputs = outputs
        # OE aktywne niskim: True = wyjścia WYŁĄCZONE. Start w stanie bezpiecznym.
        self.oe = DigitalOutputDevice(OE_GPIO, initial_value=True)
        self.spi = spidev.SpiDev()
        self.spi.open(SPI_BUS, SPI_DEV)
        self.spi.max_speed_hz = SPI_HZ
        self.spi.mode = 0
        self.write([False] * outputs)  # wyczyść śmieci z momentu włączenia zasilania
        self.oe.off()                  # dopiero teraz włącz wyjścia

    def write(self, state):
        # Wyjście i -> układ i//8, bit i%8 (QA = bit 0 ... QH = bit 7).
        chips = [0] * (self.outputs // 8)
        for i, on in enumerate(state):
            if on:
                chips[i // 8] |= 1 << (i % 8)
        # Pierwszy wysłany bajt "przepływa" do ostatniego układu w łańcuchu,
        # więc wysyłamy od ostatniego do pierwszego. Zbocze CE0 na końcu = zatrzask.
        self.spi.xfer2(list(reversed(chips)))

    def close(self):
        self.write([False] * self.outputs)
        self.oe.on()
        self.spi.close()
        self.oe.close()


def main():
    p = argparse.ArgumentParser(description="Test wyjść 74HC595")
    p.add_argument("--outputs", type=int, default=8)
    p.add_argument("--delay", type=float, default=0.5, help="sekundy na krok")
    p.add_argument("--mode", choices=["chase", "all", "single"], default="chase")
    p.add_argument("--index", type=int, default=0, help="dla --mode single")
    args = p.parse_args()

    chain = ShiftRegisterChain(args.outputs)
    n = args.outputs
    try:
        if args.mode == "single":
            print(f"Wyjście {args.index} włączone. Ctrl+C kończy.")
            chain.write([i == args.index for i in range(n)])
            while True:
                time.sleep(1)
        elif args.mode == "all":
            while True:
                print("wszystkie ON"); chain.write([True] * n); time.sleep(args.delay)
                print("wszystkie OFF"); chain.write([False] * n); time.sleep(args.delay)
        else:
            while True:
                for k in range(n):
                    print(f"wyjście {k}")
                    chain.write([i == k for i in range(n)])
                    time.sleep(args.delay)
    except KeyboardInterrupt:
        pass
    finally:
        chain.close()
        print("Wyjścia wyłączone.")


if __name__ == "__main__":
    main()
