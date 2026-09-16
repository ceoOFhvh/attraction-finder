from datetime import datetime

# Данные одной достопримечательности
name = "Городской краеведческий музей"
category = "музей"
open_hour = 10
close_hour = 18
ticket_price = 350.0
is_discount_available = True


def is_open_now(open_hour, close_hour):
    current_hour = datetime.now().hour
    if open_hour <= current_hour < close_hour:
        return True
    return False


def search_by_category(item_category, target_category):
    if item_category.lower() == target_category.lower():
        return True
    return False


def calculate_price(base_price, has_discount, discount_percent=20):
    if has_discount:
        final_price = base_price - base_price * discount_percent / 100
    else:
        final_price = base_price
    return round(final_price, 2)


# Основной сценарий
print(f"Достопримечательность: {name}")
print(f"Категория: {category}")
print(f"Часы работы: {open_hour}:00 - {close_hour}:00")

if is_open_now(open_hour, close_hour):
    print("Статус: открыто сейчас")
else:
    print("Статус: закрыто сейчас")

target_category = "Музей"
if search_by_category(category, target_category):
    print(f"Найдено совпадение по категории '{target_category}'")
else:
    print(f"Совпадений по категории '{target_category}' не найдено")

final_price = calculate_price(ticket_price, is_discount_available)
print(f"Стоимость билета: {ticket_price} руб.")
print(f"Итоговая стоимость с учётом скидки: {final_price} руб.")