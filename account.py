# Информация о счете: статус, id

import os
from tinkoff.invest import Client
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env файла
TOKEN = os.getenv("TINKOFF_TOKEN")


def main():
    with Client(TOKEN) as client:
        print(client.users.get_accounts())

if __name__ == "__main__":
    main()

def get_account_id():
    with Client(TOKEN) as client:
        try:
            accounts = client.users.get_accounts()
            for account in accounts.accounts:
                print(f"✅ Найден аккаунт: ID={account.id}, тип={account.type}, статус={account.status}")
        except Exception as e:
            print("❌ Ошибка при получении аккаунтов:", e)

get_account_id()






