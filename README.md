# GW Instek GPD-X303S Control

## Overview
This application provides a graphical user interface (GUI) to control the GW Instek GPD-X303S power supply. It allows users to set and monitor voltage and current for up to four channels. The app also includes functionality to connect to the power supply via a serial port and toggle the output on and off.

## Features
- Set and monitor voltage and current for up to four channels.
- Connect to the power supply via a serial port.
- Toggle the output on and off with visual feedback.
- Real-time updates of voltage and current values.

## Dependencies
- Python 3.6+
- PyQt6
- pyserial

```bash
pip install PyQt6 pyserial
```

## Building an Executable with PyInstaller

```bash
pip install PyQt6 pyserial
PyInstaller --onefile --windowed app.py
```


## Usage

1. Connect your GW Instek GPD-X303S power supply to your computer via a USB Cable. Make sure that the "Lock" button on the power supply is lit.
2. Run the application.
3. Select the appropriate COM port from the dropdown menu and click "Connect".
4. Use the interface to set and monitor voltage and current for each channel.
