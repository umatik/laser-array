# laser-array

Control an array of lasers (on/off) from Resolume Arena over Art-Net.

A Raspberry Pi 5 receives Art-Net, maps DMX channels to an array of output states,
and sends this array over SPI to a chain of 74HC595 shift registers.
The 74HC595 outputs drive ULN2803A chips, and these switch the lasers.

The number of outputs is configurable: 8 for the first prototype, later 16, 32, 64 ... 256 or more.
To add 8 more outputs, you add one more 74HC595 + ULN2803A and change one setting.

## Signal path

```
Resolume Arena -> Art-Net (Ethernet) -> Raspberry Pi 5 -> SPI -> 74HC595 chain -> ULN2803A -> lasers
```

## Stages

1. [Basics: Pi + 1x 74HC595 + ULN2803A](docs/etap1.md) - wiring and output test (`tools/test_outputs.py`)
2. Receive Art-Net from Resolume (in progress)

## Safety

Do the first tests with LEDs, not lasers. Never look into a laser beam.
