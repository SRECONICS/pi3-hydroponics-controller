# Wiring Guide — Raspberry Pi 3 Hydroponics Controller

## MCP3008 SPI (pH + EC sensors)

| MCP3008 Pin | Pi 3 Pin | Function         |
|-------------|----------|------------------|
| VDD         | 3.3V     | Power            |
| VREF        | 3.3V     | Reference        |
| AGND        | GND      | Analog GND       |
| CLK         | GPIO 11  | SPI0 SCLK        |
| D_OUT       | GPIO 9   | SPI0 MISO        |
| D_IN        | GPIO 10  | SPI0 MOSI        |
| CS/SHDN     | GPIO 8   | SPI0 CE0         |
| DGND        | GND      | Digital GND      |
| CH0         | pH probe output      |
| CH1         | EC/TDS signal        |

## DS18B20 Water Temperature (1-Wire)

| Sensor | Pi 3 Pin | Notes                         |
|--------|----------|-------------------------------|
| VCC    | 3.3V     |                               |
| GND    | GND      |                               |
| DATA   | GPIO 4   | 4.7 kΩ pull-up to 3.3V       |

Enable 1-Wire in `/boot/config.txt`:
```
dtoverlay=w1-gpio
```

## HC-SR04 Ultrasonic (Water Level)

| Sensor | Pi 3 Pin | Notes                                  |
|--------|----------|----------------------------------------|
| VCC    | 5V       |                                        |
| GND    | GND      |                                        |
| TRIG   | GPIO 24  |                                        |
| ECHO   | GPIO 25  | **Use voltage divider** (5V→3.3V!)     |

ECHO voltage divider: 1 kΩ (sensor→GPIO) + 2 kΩ (GPIO→GND).

## DHT22 Air Sensor

| Sensor | Pi 3 Pin | Notes                    |
|--------|----------|--------------------------|
| VCC    | 3.3V     |                          |
| GND    | GND      |                          |
| DATA   | GPIO 18  | 10 kΩ pull-up to 3.3V   |

## 4-Channel Relay Board (Pumps)

| Relay IN | Pi 3 Pin | Pump            |
|----------|----------|-----------------|
| IN1      | GPIO 17  | pH-Up solution  |
| IN2      | GPIO 27  | pH-Down solution|
| IN3      | GPIO 22  | Nutrient A      |
| IN4      | GPIO 23  | Nutrient B      |
| VCC      | 5V       |                 |
| GND      | GND      |                 |

> ⚠️ Use an isolated 12V power supply for the peristaltic pump motors.
> Connect pump VCC/GND to the relay COM/NO terminals, NOT directly to Pi.

## OLED Display SSD1306 (Optional)

| OLED | Pi 3 Pin |
|------|----------|
| VCC  | 3.3V     |
| GND  | GND      |
| SCL  | GPIO 3   |
| SDA  | GPIO 2   |

Enable I²C in `raspi-config` → Interface Options → I2C.
