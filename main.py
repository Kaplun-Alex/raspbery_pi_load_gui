#widget imports
import sys
import asyncio
import threading
from time import sleep
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QCheckBox, QRadioButton, QTextEdit, QComboBox,
    QListWidget, QSlider, QProgressBar, QLabel, QHBoxLayout, QStackedWidget
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
# Peripheral imports
from smbus2 import SMBus
from time import sleep

class VoltageLevelWorker(QThread):
    
    voltageChanged = pyqtSignal(int)
    currentChanged = pyqtSignal(int)
    powerChanged = pyqtSignal(int)
    shuntChanged = pyqtSignal(int)
    
    def run(self):
            
        measure_speed = 100 #in milliseconds    
        i2c_BUS = 1
        ina226_adr = 0x44
        cal_reg_dec_value = 1442
        voltage_register_multiplier = 1.1875 # 0.95*1.25mv
        
        #registers adresses
        config_register = 0x00
        shunt_voltage_register = 0x01
        bus_voltage_register = 0x02
        power_register = 0x03
        current_register = 0x04
        calibration_register = 0x05
        
        
        with SMBus(i2c_BUS) as bus:
            value_swapped = (cal_reg_dec_value >> 8) | ((cal_reg_dec_value  & 0xFF) << 8)
            bus.write_word_data(ina226_adr, calibration_register, value_swapped)
        
        while True:
            with SMBus(i2c_BUS) as bus:
                voltageValue = bus.read_word_data(ina226_adr, bus_voltage_register)
                voltageValue = ((voltageValue << 8)& 0xFF00) + (voltageValue >> 8)
                
                currentValue = bus.read_word_data(ina226_adr, current_register)
                currentValue = ((currentValue << 8)& 0xFF00) + (currentValue >> 8)
                
                powerValue = bus.read_word_data(ina226_adr, power_register)
                powerValue = ((powerValue << 8)& 0xFF00) + (powerValue >> 8)
                
                shuntValue = bus.read_word_data(ina226_adr, shunt_voltage_register)
                shuntValue = ((shuntValue << 8)& 0xFF00) + (shuntValue >> 8)
                
                self.voltageChanged.emit(voltageValue)
                self.currentChanged.emit(currentValue)
                self.powerChanged.emit(powerValue)
                self.shuntChanged.emit(shuntValue)
                
                self.msleep(measure_speed)

        

class FirstWindow(QWidget):

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.DataLineFont = QFont("Arial", 20)
        self.ButtonFont = QFont("Arial", 16)
        self.ArrowFont = QFont("Arial", 30)

        self.heaters = 10

        # Voltage Push Button
        VoltageButton = QPushButton("Voltage", self)
        VoltageButton.clicked.connect(self.start_voltage_measure)
        VoltageButton.setFixedSize(120, 60)
        VoltageButton.move(650, 30)
        VoltageButton.setFont(self.ButtonFont)

        # Current Push Button
        CurrentButton = QPushButton("Current", self)
        CurrentButton.clicked.connect(self.get_current_level)
        CurrentButton.setFixedSize(120, 60)
        CurrentButton.move(650, 100)
        CurrentButton.setFont(self.ButtonFont)


        # Power Push Button
        PowerButton = QPushButton("Power", self)
        PowerButton.clicked.connect(self.get_power_level)
        PowerButton.setFixedSize(120, 60)
        PowerButton.move(650, 170)
        PowerButton.setFont(self.ButtonFont)


        # Increase load Push Button
        IncLoadButton = QPushButton("\u02C4", self)
        IncLoadButton.clicked.connect(self.increase_load_level)
        IncLoadButton.setFixedSize(120, 60)
        IncLoadButton.move(650, 300)
        IncLoadButton.setFont(self.ArrowFont)

       
        # Decrease load Push Button
        DecLoadButton = QPushButton("\u02C5", self)
        DecLoadButton.clicked.connect(self.decrease_load_level)
        DecLoadButton.setFixedSize(120, 60)
        DecLoadButton.move(650, 370)
        DecLoadButton.setFont(self.ArrowFont)

        # VoltageDataLine
        self.VoltageDataLine = QLineEdit(self)
        self.VoltageDataLine.setPlaceholderText("0.000")
        self.VoltageDataLine.setFixedSize(400, 60)
        self.VoltageDataLine.move(50, 30)
        self.VoltageDataLine.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.VoltageDataLine.setFont(self.DataLineFont)

        # CurrentDataLine
        self.CurrentDataLine = QLineEdit(self)
        self.CurrentDataLine.setPlaceholderText("0.000")
        self.CurrentDataLine.setFixedSize(400, 60)
        self.CurrentDataLine.move(50, 100)
        self.CurrentDataLine.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.CurrentDataLine.setFont(self.DataLineFont)

        # PowerDataLine
        self.PowerDataLine = QLineEdit(self)
        self.PowerDataLine.setPlaceholderText("0.000")
        self.PowerDataLine.setFixedSize(400, 60)
        self.PowerDataLine.move(50, 170)
        self.PowerDataLine.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.PowerDataLine.setFont(self.DataLineFont)
        
        # ShuntDataLine
        self.ShuntDataLine = QLineEdit(self)
        self.ShuntDataLine.setPlaceholderText("0.000")
        self.ShuntDataLine.setFixedSize(400, 60)
        self.ShuntDataLine.move(50, 240)
        self.ShuntDataLine.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ShuntDataLine.setFont(self.DataLineFont)


        # Text Edit Multiline
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Enter multi-line text here")

        # Label
        self.label = QLabel(f"HEAT MODULE:  {str(self.heaters)}", self)
        self.label.setFixedSize(400, 60)
        self.label.move(50, 350)
        self.label.setFont(self.DataLineFont)  


#peripheral stack

    def start_voltage_measure(self):
        self.worker = VoltageLevelWorker()
        
        self.worker.voltageChanged.connect(self.onVoltageChanged)
        self.worker.currentChanged.connect(self.onCurrentChanged)
        self.worker.powerChanged.connect(self.onPowerChanged)
        self.worker.shuntChanged.connect(self.onShuntChanged)
                
        self.worker.start()
    
    def onVoltageChanged(self, value):
        self.VoltageDataLine.setText(f'{(((round(value*1.1875)))/1000):.3f}')
        #print(f'Voltage: {value}')

    def onCurrentChanged(self, value):
        self.CurrentDataLine.setText(str(round(value/24.1237)))
        
    def onPowerChanged(self, value):
        self.PowerDataLine.setText(str(value))
        
    def onShuntChanged(self, value):
        self.ShuntDataLine.setText(str(value))
        #print(f'Shunt voltage: {value}')

    def write_register(self, register, value):
        i2c_BUS = 1
        ina226_adrr = 0x44
        with SMBus(i2c_BUS) as bus:
            value_swapped = (value >> 8) | ((value & 0xFF) << 8)
            bus.write_word_data(ina226_adrr, register, value_swapped)

    def read_register(self, register):
        i2c_BUS = 1
        ina226_adrr = 0x44
        with SMBus(i2c_BUS) as bus:
            value = bus.read_word_data(ina226_adrr, register)
            value = ((value << 8)& 0xFF00) + (value >> 8)
            return value


    def get_voltage_level(self):        
        self.label.setText("Get Voltage level clicked!")
        self.VoltageDataLine.setText("Get Voltage level clicked!")
        config_register = 0x00
        shunt_voltage_register = 0x01
        bus_voltage_register = 0x02
        power_register = 0x03
        current_register = 0x04
        calibration_register = 0x05

        self.write_register(calibration_register, 1421) #write calibrate value to VBUS register
        voltage = self.read_register(bus_voltage_register)
        self.VoltageDataLine.setText(str(voltage))
        print(voltage*1.25*0.95)

    def voltage_wrapper(self):
        interval = 1
        def wrapper():
            self.get_voltage_level()
            threading.Timer(interval, wrapper).start()
        wrapper()
    
    def get_current_level(self):
        self.label.setText("Get Current level clicked!")
        self.CurrentDataLine.setText("Get Current level clicked!")
    
    def get_power_level(self):
        self.label.setText("Get Power level clicked!")
        self.PowerDataLine.setText("Get Power level clicked!")
                 
    def increase_load_level(self):
        if self.heaters < 16:
            self.heaters += 1
            self.label.setText(f"HEAT MODULE:  {str(self.heaters)}")
            print(self.heaters)
        else: 
            pass

    def decrease_load_level(self):
        if self.heaters > 0 or 0:
            self.heaters -= 1
            self.label.setText(f"HEAT MODULE:  {str(self.heaters)}")
        else: 
            pass
        
class SecondWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.DataLineFont = QFont("Arial", 16)
        self.ButtonFont = QFont("Arial", 16)
        self.ArrowFont = QFont("Arial", 30)

class ThirdWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.DataLineFont = QFont("Arial", 16)
        self.ButtonFont = QFont("Arial", 16)
        self.ArrowFont = QFont("Arial", 30)

class CalibrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.DataLineFont = QFont("Arial", 16)
        self.ButtonFont = QFont("Arial", 16)
        self.ArrowFont = QFont("Arial", 30)

        # Voltage Push Button
        VoltageMultiplierButton = QPushButton("Set voltage multiplier", self)
        VoltageMultiplierButton.clicked.connect(self.set_voltage_multiplyer)
        VoltageMultiplierButton.setFixedSize(240, 60)
        VoltageMultiplierButton.move(500, 30)
        VoltageMultiplierButton.setFont(self.ButtonFont)

        # VoltageDataLine
        self.VoltageMultiplierDataLine = QLineEdit(self)
        self.VoltageMultiplierDataLine.setPlaceholderText("0.000")
        self.VoltageMultiplierDataLine.setFixedSize(200, 60)
        self.VoltageMultiplierDataLine.move(50, 30)
        self.VoltageMultiplierDataLine.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.VoltageMultiplierDataLine.setFont(self.DataLineFont)

        # Label
        self.CalLabel = QLabel("This is a label", self)
        self.CalLabel.setFixedSize(400, 60)
        self.CalLabel.move(50, 350)
        self.CalLabel.setFont(self.DataLineFont) 

    def set_voltage_multiplyer(self):
        self.CalLabel.setText("Voltage multiplier set!")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Two Windows Example")
        self.setGeometry(100, 100, 800, 600)
        self.ButtonFont = QFont("Arial", 16)

        # Create the two windows
        self.first_window = FirstWindow()
        self.second_window = SecondWindow()
        self.third_window = ThirdWindow()
        self.four_window = CalibrationWindow()

        # Create the stacked widget and add the four windows
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.first_window)
        self.stacked_widget.addWidget(self.second_window)
        self.stacked_widget.addWidget(self.third_window)
        self.stacked_widget.addWidget(self.four_window)

        # Create buttons to switch between windows
        switch_to_first_button = QPushButton("MAIN")
        switch_to_first_button.setFixedSize(120, 60)
        switch_to_first_button.move(50, 400)
        switch_to_first_button.setFont(self.ButtonFont)
        switch_to_first_button.clicked.connect(self.show_first_window)

        switch_to_second_button = QPushButton("NEXT")
        switch_to_second_button.setFixedSize(120, 60)
        switch_to_second_button.move(100, 400)
        switch_to_second_button.setFont(self.ButtonFont)
        switch_to_second_button.clicked.connect(self.show_second_window)

        switch_to_third_button = QPushButton("NEXT_ONE")
        switch_to_third_button.setFixedSize(120, 60)
        switch_to_third_button.move(50, 400)
        switch_to_third_button.setFont(self.ButtonFont)
        switch_to_third_button.clicked.connect(self.show_third_window)

        switch_to_four_button = QPushButton("Calibration")
        switch_to_four_button.setFixedSize(200, 60)
        switch_to_four_button.move(50, 400)
        switch_to_four_button.setFont(self.ButtonFont)
        switch_to_four_button.clicked.connect(self.show_four_window)

        # Layout for the main window
        button_layout = QHBoxLayout()
        button_layout.addWidget(switch_to_first_button)
        button_layout.addWidget(switch_to_second_button)
        button_layout.addWidget(switch_to_third_button)
        button_layout.addWidget(switch_to_four_button)

        # Vertical layout for the main window
        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        layout.addLayout(button_layout)

        # Central widget setup
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def show_first_window(self):
        self.stacked_widget.setCurrentWidget(self.first_window)

    def show_second_window(self):
        self.stacked_widget.setCurrentWidget(self.second_window)

    def show_third_window(self):
        self.stacked_widget.setCurrentWidget(self.third_window)

    def show_four_window(self):
        self.stacked_widget.setCurrentWidget(self.four_window)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
