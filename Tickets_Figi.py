"""
# Выводит информацию о всех инструментах со значениями FIGI
from tinkoff.invest import Client
import os

API_TOKEN = os.getenv("TINKOFF_TOKEN")

with Client(API_TOKEN) as client:
    # Fetch shares or other instruments, depending on your needs
    shares = client.instruments.shares()

    # Loop through each instrument and print its ticker and FIGI
    for instrument in shares.instruments:
        print(f"Ticker: {instrument.ticker}, FIGI: {instrument.figi}")

"""



# Выводит FIGI по названию тикета, инструмента
from tinkoff.invest import Client
import os

API_TOKEN = os.getenv("TINKOFF_TOKEN")
ticker = 'OZPH'  # Replace with the desired ticker

with Client(API_TOKEN) as client:
    # Get instrument details by ticker
    instruments = client.instruments.shares()

    # Search for the instrument with the desired ticker
    for instrument in instruments.instruments:
        if instrument.ticker == ticker:
            print(f"Ticker: {instrument.ticker}, FIGI: {instrument.figi}")
            break




"""
# Выводит название инструмента по FIGI
from tinkoff.invest import Client
import os

API_TOKEN = os.getenv("TINKOFF_TOKEN")
figi = 'BBG004S681W1'  # Replace with the desired FIGI

with Client(API_TOKEN) as client:
    # Get instrument details by FIGI
    instruments = client.instruments.shares()

    found = False  # Flag to check if the instrument is found

    # Search for the instrument with the desired FIGI
    for instrument in instruments.instruments:
        if instrument.figi == figi:
            print(f"FIGI: {instrument.figi}, Ticker: {instrument.ticker}, Instrument: {instrument.name}")
            found = True
            break

    if not found:
        print(f"No instrument found for FIGI: {figi}. Please check the identifier.")
"""


