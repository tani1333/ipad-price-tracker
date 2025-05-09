import requests
from bs4 import BeautifulSoup
from datetime import datetime, time
import os
import re
from pathlib import Path
import schedule
import time
import pytz

# Конфигурационные параметры
PRODUCT_URL = "https://store77.net/apple_ipad_pro_11_m4_2024/planshet_apple_ipad_pro_11_m4_2024_512gb_wi_fi_serebristyy/"
PRICE_FILE = Path("C:/price_tracking/ipad_price_history.txt")  # Путь к файлу на диске C
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}
SAVE_TIME = "23:59"  # Время сохранения (по Москве)

def setup_price_file():
    """Создает файл и директорию при необходимости"""
    try:
        PRICE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not PRICE_FILE.exists():
            PRICE_FILE.touch()
            print(f"Создан новый файл для хранения цен: {PRICE_FILE}")
    except Exception as e:
        print(f"Ошибка при создании файла: {e}")
        return False
    return True

def extract_price(html):
    """Извлекает цену из HTML страницы"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Поиск в атрибуте onClick
        onclick_elements = soup.find_all(attrs={"onclick": True})
        for element in onclick_elements:
            if 'YandexEcommerce.getInstance().click' in element.get('onclick', ''):
                match = re.search(r'"price":(\d+)', element['onclick'])
                if match:
                    return int(match.group(1))
        
        # 2. Поиск в JavaScript блоках
        for script in soup.find_all('script'):
            if script.string and 'YandexEcommerce' in script.string:
                match = re.search(r'"price":(\d+)', script.string)
                if match:
                    return int(match.group(1))
        
        # 3. Альтернативные методы поиска
        price_elements = [
            soup.find(attrs={'data-price': True}),
            soup.find('span', class_='price'),
            soup.find('div', class_='product-price')
        ]
        
        for element in price_elements:
            if element:
                price_text = element.get_text(strip=True) or element.get('content', '')
                if price_text:
                    cleaned = re.sub(r'[^\d]', '', price_text)
                    if cleaned:
                        return int(cleaned)
        
        return None
    except Exception as e:
        print(f"Ошибка при парсинге цены: {e}")
        return None

def save_price_to_file(price):
    """Сохраняет цену в текстовый файл"""
    try:
        moscow_tz = pytz.timezone('Europe/Moscow')
        timestamp = datetime.now(moscow_tz).strftime("%d.%m.%Y %H:%M:%S")
        price_line = f"{timestamp} - {price:,} руб.\n".replace(",", " ")
        
        # Проверяем последнюю запись
        last_entry = ""
        if PRICE_FILE.exists() and os.path.getsize(PRICE_FILE) > 0:
            with open(PRICE_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_entry = lines[-1]
        
        # Проверяем, не сохраняли ли уже сегодня
        today_date = timestamp.split()[0]
        if today_date in last_entry:
            print(f"Цена за {today_date} уже сохранена")
            return False
        
        # Добавляем новую запись
        with open(PRICE_FILE, 'a', encoding='utf-8') as f:
            f.write(price_line)
        
        print(f"Цена успешно сохранена в файл: {PRICE_FILE}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении в файл: {e}")
        return False

def get_price_change():
    """Возвращает изменение цены по сравнению с предыдущей записью"""
    try:
        if not PRICE_FILE.exists() or os.path.getsize(PRICE_FILE) < 2:
            return None
        
        with open(PRICE_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) < 2:
                return None
            
            # Получаем последнюю и предпоследнюю цены
            last_price = int(re.sub(r'[^\d]', '', lines[-1].split('-')[1].strip()))
            prev_price = int(re.sub(r'[^\d]', '', lines[-2].split('-')[1].strip()))
            
            return last_price - prev_price
    except Exception as e:
        print(f"Ошибка при сравнении цен: {e}")
        return None

def daily_price_check():
    """Ежедневная проверка и сохранение цены"""
    try:
        print(f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Запуск ежедневной проверки цены...")
        
        # Получаем HTML страницы
        response = requests.get(PRODUCT_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Извлекаем цену
        price = extract_price(response.text)
        if price is None:
            print("Не удалось определить цену товара")
            return
        
        print(f"Текущая цена: {price:,} руб.".replace(",", " "))
        
        # Сохраняем цену
        if save_price_to_file(price):
            # Анализируем изменение цены
            change = get_price_change()
            if change is not None:
                if change > 0:
                    print(f"↑ Цена выросла на {change:,} руб.".replace(",", " "))
                elif change < 0:
                    print(f"↓ Цена снизилась на {abs(change):,} руб.".replace(",", " "))
                else:
                    print("→ Цена не изменилась")
    
    except requests.RequestException as e:
        print(f"Ошибка при загрузке страницы: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

def schedule_daily_check():
    """Настраивает ежедневную проверку по расписанию"""
    moscow_tz = pytz.timezone('Europe/Moscow')
    
    # Запланировать ежедневную проверку
    schedule.every().day.at(SAVE_TIME, moscow_tz).do(daily_price_check)
    
    print(f"Мониторинг цен запущен. Ежедневное сохранение в {SAVE_TIME} по Москве")
    print("Для остановки нажмите Ctrl+C\n")
    
    # Первая проверка при запуске
    daily_price_check()
    
    # Бесконечный цикл для работы планировщика
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    if not setup_price_file():
        exit()
    
    try:
        schedule_daily_check()
    except KeyboardInterrupt:
        print("\nМониторинг цен остановлен")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
