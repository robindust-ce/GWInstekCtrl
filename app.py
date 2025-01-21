import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout, QComboBox, QFrame
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import QTimer, QThread, pyqtSignal

import serial
import serial.tools.list_ports

# Separate thread for serial communication
class SerialWorker(QThread):
    voltage_updated = pyqtSignal(int, str)
    current_updated = pyqtSignal(int, str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True

    def run(self):
        while self.running:
            for i in range(4):
                self.serial_port.write(f'VOUT{i+1}?\n'.encode())
                voltage = self.serial_port.readline().decode('utf-8').strip()
                self.voltage_updated.emit(i, voltage)

                self.serial_port.write(f'IOUT{i+1}?\n'.encode())
                current = self.serial_port.readline().decode('utf-8').strip()
                self.current_updated.emit(i, current)
            self.msleep(500)  # Sleep for 500 ms

    def stop(self):
        self.running = False
        self.wait()

class PowerSupplyControl(QWidget):
    def __init__(self):
        super().__init__()

        self.serial_port = None  # Initialize the serial port variable
        self.serial_worker = None
        self.initUI()

    def initUI(self):
        main_layout = QGridLayout()

        self.channels = []
        for i in range(4):
            channel_layout = QGridLayout()

            # Channel Label
            channel_label = QLabel(f'Channel {i+1}')
            channel_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))

            # Actual Voltage and Current
            actual_voltage = self.create_segment_display('0.0V')
            actual_current = self.create_segment_display('0.0A')

            # Voltage and Current Settings
            set_voltage = QLineEdit()
            set_voltage.setFixedWidth(100)  # Set fixed width for voltage input
            set_current = QLineEdit()
            set_current.setFixedWidth(100)  # Set fixed width for current input

            # Set buttons
            set_voltage_button = QPushButton('Set')
            set_voltage_button.clicked.connect(lambda _, ch=i+1, sv=set_voltage: self.set_voltage(ch, sv.text()))
            set_current_button = QPushButton('Set')
            set_current_button.clicked.connect(lambda _, ch=i+1, sc=set_current: self.set_current(ch, sc.text()))

            # Add widgets to layout
            channel_layout.addWidget(channel_label, 0, 0, 1, 4)
            channel_layout.addWidget(actual_voltage, 1, 0)
            channel_layout.addWidget(set_voltage, 1, 1)
            channel_layout.addWidget(set_voltage_button, 1, 2)
            channel_layout.addWidget(actual_current, 2, 0)
            channel_layout.addWidget(set_current, 2, 1)
            channel_layout.addWidget(set_current_button, 2, 2)

            # Add a frame to visually separate the cells
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setLayout(channel_layout)

            row = i // 2
            col = i % 2
            main_layout.addWidget(frame, row, col)
            self.channels.append((actual_voltage, actual_current, set_voltage, set_current))

        # COM Port Dropdown and Connect Button
        control_layout = QVBoxLayout()
        self.com_ports_dropdown = QComboBox()
        self.refresh_com_ports()
        control_layout.addWidget(self.com_ports_dropdown)

        self.connect_button = QPushButton('Connect')
        self.connect_button.clicked.connect(self.connect_to_com_port)
        control_layout.addWidget(self.connect_button)

        # Connection Status Label
        self.connection_status = QLabel('')
        control_layout.addWidget(self.connection_status)

        # Single Output On/Off Toggle
        self.output_toggle = QPushButton('Output Off')
        self.output_toggle.setCheckable(True)
        self.output_toggle.clicked.connect(self.toggle_output)
        control_layout.addWidget(self.output_toggle)

        main_layout.addLayout(control_layout, 0, 2, 2, 1)  # Span the control layout over 2 rows

        self.setLayout(main_layout)
        self.setWindowTitle('GW Instek GPD-X303S Control')

    def create_segment_display(self, text):
        label = QLabel(text)
        font = QFont('DSEG7 Classic', 24)  # Use the 7-segment display font
        label.setFont(font)
        palette = label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor('green'))
        label.setPalette(palette)
        return label

    def toggle_output(self):
        if self.output_toggle.isChecked():
            self.serial_port.write(b'OUT1\n')
            self.output_toggle.setText('Output On')
            self.output_toggle.setStyleSheet('background-color: lightgreen; color: black')
            if not self.serial_worker:
                self.start_serial_worker()
        else:
            self.serial_port.write(b'OUT0\n')
            self.output_toggle.setText('Output Off')
            self.output_toggle.setStyleSheet('background-color: lightcoral; color: black')
            if self.serial_worker:
                self.stop_serial_worker()

    def refresh_com_ports(self):
        self.com_ports_dropdown.clear()
        com_ports = list(serial.tools.list_ports.comports())
        for port in com_ports:
            self.com_ports_dropdown.addItem(port.device)

    def set_output_status(self):
        if not self.serial_port:
            return

        self.serial_port.write(b'STATUS?\n')
        response = self.serial_port.readline().decode('utf-8').strip()

        if response[5] == '1':
            self.output_toggle.setChecked(True)
            self.output_toggle.setText('Output On')
            self.output_toggle.setStyleSheet('background-color: lightgreen; color: black')
            if not self.serial_worker:
                self.start_serial_worker()
        else:
            self.output_toggle.setChecked(False)
            self.output_toggle.setText('Output Off')
            self.output_toggle.setStyleSheet('background-color: lightcoral; color: black')
            if self.serial_worker:
                self.stop_serial_worker()

    def connect_to_com_port(self):
        selected_port = self.com_ports_dropdown.currentText()

        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

        if self.serial_worker:
            self.stop_serial_worker()

        try:
            self.serial_port = serial.Serial(selected_port, 9600, timeout=1)
            self.serial_port.write(b'*IDN?\n')
            response = self.serial_port.readline().decode('utf-8').strip()
            if 'gw instek' in response.lower():
                self.connection_status.setText(response)
                self.connection_status.setStyleSheet('color: black')
                self.set_output_status()
            else:
                self.connection_status.setText('Connection Failed')
                self.connection_status.setStyleSheet('color: red')
                self.serial_port.close()
                self.serial_port = None
        except Exception as e:
            self.connection_status.setText(f'Error: {e}')
            self.connection_status.setStyleSheet('color: red')
            if self.serial_port:
                self.serial_port.close()
                self.serial_port = None

    def start_serial_worker(self):
        self.serial_worker = SerialWorker(self.serial_port)
        self.serial_worker.voltage_updated.connect(self.update_voltage_display)
        self.serial_worker.current_updated.connect(self.update_current_display)
        self.serial_worker.start()

    def stop_serial_worker(self):
        if self.serial_worker:
            self.serial_worker.stop()
            self.serial_worker = None

    def update_voltage_display(self, channel, voltage):
        actual_voltage, _, _, _ = self.channels[channel]
        actual_voltage.setText(f'{voltage} ')

    def update_current_display(self, channel, current):
        _, actual_current, _, _ = self.channels[channel]
        actual_current.setText(f'{current}')

    def set_voltage(self, channel, voltage):
        if self.serial_port:
            command = f'VSET{channel}:{voltage}\n'
            self.serial_port.write(command.encode())

    def set_current(self, channel, current):
        if self.serial_port:
            command = f'ISET{channel}:{current}\n'
            self.serial_port.write(command.encode())

    def closeEvent(self, event):
        self.stop_serial_worker()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PowerSupplyControl()
    ex.show()
    sys.exit(app.exec())

