# Etap 1: Raspberry Pi + 1× 74HC595 + ULN2803A (8 wyjść)

Cel: Pi wysyła stan 8 wyjść przez SPI do 74HC595, ten steruje ULN2803A, który włącza/wyłącza lasery (najpierw diody LED).
Kod: Python. Docelowo Resolume wysyła Art-Net prosto do Pi po Ethernecie (konwerter Art-Net→DMX na razie nieużywany).

---

## 0. Bezpieczeństwo (przeczytaj zanim cokolwiek podłączysz)

- **Pierwsze testy rób na diodach LED, nie na laserach.** Lasery podłączamy dopiero, gdy sekwencja na LED-ach działa poprawnie.
- Przy laserach: nigdy nie patrz w wiązkę, kieruj je w matową ścianę / ekran, usuń z drogi lustra i błyszczące powierzchnie. Jeśli lasery są mocniejsze niż ok. 5 mW (klasa 3B/4), używaj okularów ochronnych dobranych do długości fali.
- Po włączeniu zasilania 74HC595 ma **losowy stan wyjść**. Dlatego pin OE jest podciągnięty rezystorem do 3.3 V: dopóki skrypt go nie zwolni, wszystkie wyjścia są wyłączone. Nie pomijaj tego rezystora.
- Lasery zasilaj z **osobnego zasilacza**, nie z pinu 5 V Raspberry Pi. Masy (GND) Pi, zasilacza laserów i ULN2803A muszą być połączone.
- Podłączaj/rozłączaj przewody tylko przy wyłączonym zasilaniu.

---

## 1. System na Raspberry Pi

1. **Raspberry Pi Imager** → wybierz swój model Pi → **Raspberry Pi OS Lite (64-bit)** (bez pulpitu, wystarczy).
2. W ustawieniach Imagera (ikona zębatki / „Edytuj ustawienia”):
   - hostname: `lasers`
   - użytkownik i hasło
   - **włącz SSH**
   - Wi-Fi opcjonalnie (do instalacji pakietów); docelowo Art-Net pójdzie kablem Ethernet.
3. Włóż kartę, uruchom Pi, połącz się: `ssh <użytkownik>@lasers.local`
4. Aktualizacja i włączenie SPI:
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo raspi-config nonint do_spi 0
   sudo apt install -y python3-spidev python3-gpiozero
   sudo reboot
   ```
5. Po restarcie sprawdź: `ls /dev/spidev*` → powinno pokazać `/dev/spidev0.0` i `/dev/spidev0.1`.

---

## 2. Podłączenie

### Zasilanie 74HC595: 3.3 V z Pi
74HC595 zasilamy z **3.3 V** (nie 5 V). Wtedy sygnały z Pi (3.3 V) pasują bez konwertera poziomów, a wyjścia 3.3 V spokojnie wysterują ULN2803A.

### Raspberry Pi → 74HC595

| Pi (pin fizyczny) | Funkcja | 74HC595 (pin) |
|---|---|---|
| 1 | 3.3 V | 16 (VCC) i 10 (SRCLR) |
| 6 | GND | 8 (GND) |
| 19 | GPIO10 / SPI MOSI | 14 (SER, dane) |
| 23 | GPIO11 / SPI SCLK | 11 (SRCLK, zegar) |
| 24 | GPIO8 / SPI CE0 | 12 (RCLK, zatrzask) |
| 31 | GPIO6 | 13 (OE) **+ rezystor 10 kΩ z pinu 13 do 3.3 V** |

Dodatkowo: **kondensator 100 nF** między pinem 16 a 8 74HC595, jak najbliżej układu.
Pin 9 (QH') zostaw wolny; w kolejnych etapach idzie do pinu 14 następnego 74HC595.

### 74HC595 → ULN2803A

| 74HC595 | ULN2803A wejście | ULN2803A wyjście | Wyjście w kodzie |
|---|---|---|---|
| 15 (QA) | 1 (IN1) | 18 (OUT1) | 0 |
| 1 (QB) | 2 (IN2) | 17 (OUT2) | 1 |
| 2 (QC) | 3 (IN3) | 16 (OUT3) | 2 |
| 3 (QD) | 4 (IN4) | 15 (OUT4) | 3 |
| 4 (QE) | 5 (IN5) | 14 (OUT5) | 4 |
| 5 (QF) | 6 (IN6) | 13 (OUT6) | 5 |
| 6 (QG) | 7 (IN7) | 12 (OUT7) | 6 |
| 7 (QH) | 8 (IN8) | 11 (OUT8) | 7 |

ULN2803A pozostałe piny:
- **pin 9 (GND)** → wspólna masa (GND Pi + minus zasilacza laserów)
- **pin 10 (COM)** → plus zasilacza laserów (np. +5 V)

### Obciążenie (LED do testu, potem lasery)
ULN2803A **zwiera do masy** („low-side”), więc:
- **plus** zasilacza → **plus** LED-a/lasera
- **minus** LED-a/lasera → wyjście ULN (pin 18…11)

Test na LED-ach przy 5 V: LED + rezystor 220–330 Ω szeregowo.
Moduły laserowe 5 V zwykle mają własny ogranicznik prądu (rezystor/sterownik na płytce) i podłącza się je bez rezystora, ale sprawdź opis swoich modułów.

Limity ULN2803A: max 500 mA na kanał, ale cały układ nagrzewa się przy dużych prądach. Do kilkudziesięciu mA na laser (typowe małe moduły) jest z dużym zapasem.

---

## 3. Test

Pobierz repo na Pi (najpierw `sudo apt install -y git`):
```bash
git clone https://github.com/umatik/laser-array.git && cd laser-array
```
Potem:

```bash
python3 tools/test_outputs.py                     # sekwencja: wyjście 0,1,...,7 po kolei
python3 tools/test_outputs.py --delay 0.1         # szybciej
python3 tools/test_outputs.py --mode all          # wszystkie miga razem
python3 tools/test_outputs.py --mode single --index 3   # tylko wyjście 3
```
Ctrl+C kończy i wyłącza wszystkie wyjścia.

**Oczekiwany wynik:** LED-y zapalają się po kolei od OUT1 (pin 18) do OUT8 (pin 11), zawsze tylko jeden naraz.

### Gdy coś nie działa
- `No such file /dev/spidev0.0` → SPI niewłączone (krok 1.4) lub brak restartu.
- Nic się nie świeci → sprawdź OE (pin 13 musi być w stanie niskim, gdy skrypt działa), COM i GND ULN-a, kierunek LED-ów.
- Świecą losowe / przesunięte wyjścia → zamienione przewody SER/SRCLK/RCLK albo brak wspólnej masy.
- Wszystko świeci przed uruchomieniem skryptu → brak rezystora 10 kΩ na OE.
