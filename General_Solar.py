import tkinter as tk
from tkinter import ttk
import serial
import json
import requests
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from datetime import datetime

# Глобальные переменные
current_voltage = 0.0
current_illuminance = 0
current_mode = "UNKNOWN"
current_power = 0.0
forecast_times = []
forecast_power = []
voltage_history = []
power_history = []
illuminance_history = []

# Константы для расчётов
VOLTAGE_REF = 5.0  # Опорное напряжение Arduino
R1 = 120.0
R2 = 220.0
VOLTAGE_DIVIDER_RATIO = (R1 + R2) / R2  # ≈1.545
PANEL_AREA = 0.5
PANEL_EFFICIENCY = 0.15

'''Настройки порта (укажите нужный порт: "COM3" для Windows или "/dev/ttyACM0" для Linux)'''
SERIAL_PORT = "COM3"

BAUDRATE = 9600

def read_serial_data():
    global current_voltage, current_illuminance, current_mode, current_power
    try:
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    except Exception as e:
        print("Ошибка открытия порта:", e)
        return

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            data = json.loads(line)
            voltage_raw = data.get("voltage_raw", 0)
            illuminance_raw = data.get("illuminance_raw", 0)
            current_mode = data.get("mode", "UNKNOWN")

            measured_voltage = (voltage_raw / 1023.0) * VOLTAGE_REF
            current_voltage = measured_voltage * VOLTAGE_DIVIDER_RATIO
            current_illuminance = illuminance_raw
            normalized_illuminance = illuminance_raw / 1023.0
            current_power = current_voltage * normalized_illuminance * 10

            voltage_history.append(current_voltage)
            power_history.append(current_power)
            illuminance_history.append(current_illuminance)

            time.sleep(1)
        except Exception as e:
            print("Ошибка чтения данных:", e)
            time.sleep(1)


# Получение прогноза с апишки
def fetch_forecast():
    global forecast_times, forecast_power
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 55.3333,
        "longitude": 86.0833,
        "hourly": "shortwave_radiation",
        "forecast_days": 3,
        "timezone": "UTC"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        times = data.get("hourly", {}).get("time", [])
        irradiances = data.get("hourly", {}).get("shortwave_radiation", [])

        forecast_times = [datetime.fromisoformat(t) for t in times]
        forecast_power = [ir * PANEL_AREA * PANEL_EFFICIENCY for ir in irradiances]
    except Exception as e:
        print("Ошибка получения прогноза:", e)
        forecast_times = []
        forecast_power = []


def update_gui():
    sensor_label.config(text=f" Напряжение: {current_voltage:.2f} V\n"
                             f"Освещённость: {current_illuminance}\n"
                             f"Мощность: {current_power:.2f} W\n"
                             f"Режим: {current_mode}")

    ax1.clear()
    ax1.plot(voltage_history[-50:], label="Напряжение (V)", color='blue')
    ax1.plot(power_history[-50:], label="Мощность (W)", color='red')
    ax1.set_title("Напряжение и мощность")
    ax1.legend()

    ax2.clear()
    ax2.plot(illuminance_history[-50:], color='orange')
    ax2.set_title("Освещённость")

    ax3.clear()
    if forecast_times and forecast_power:
        ax3.plot(forecast_times, forecast_power, marker='o', color='green')
        ax3.set_title("Прогноз мощности")
        ax3.set_xlabel("Время")
        ax3.set_ylabel("Мощность (W)")
        fig3.autofmt_xdate()

    canvas1.draw()
    canvas2.draw()
    canvas3.draw()

    root.after(5000, update_gui)


root = tk.Tk()
root.title("Мониторинг")
root.geometry("800x600")
root.configure(bg="#f0f0f0")

frame_top = ttk.Frame(root, padding=10)
frame_top.pack(fill="x")

sensor_label = ttk.Label(frame_top, text="Ожидание данных...", font=("Arial", 14))
sensor_label.pack(pady=10)

frame_graphs = ttk.Frame(root)
frame_graphs.pack(fill="both", expand=True)

fig1, ax1 = plt.subplots(figsize=(4, 2))
canvas1 = FigureCanvasTkAgg(fig1, master=frame_graphs)
canvas1.get_tk_widget().grid(row=0, column=0, padx=5, pady=5)

fig2, ax2 = plt.subplots(figsize=(4, 2))
canvas2 = FigureCanvasTkAgg(fig2, master=frame_graphs)
canvas2.get_tk_widget().grid(row=0, column=1, padx=5, pady=5)

fig3, ax3 = plt.subplots(figsize=(8, 3))
canvas3 = FigureCanvasTkAgg(fig3, master=root)
canvas3.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

threading.Thread(target=read_serial_data, daemon=True).start()
threading.Thread(target=fetch_forecast, daemon=True).start()

root.after(1000, update_gui)
root.mainloop()
