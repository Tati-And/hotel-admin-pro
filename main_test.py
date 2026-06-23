from guest import Guest
from room import LuxRoom
from booking import Booking
from database import add_booking_to_db, save_guest

def run_test():
    print("=== ЗАПУСК ПОЛНОГО ЦИКЛА БРОНИРОВАНИЯ ===")

    # 1. Создаем гостя (сначала сохраняем его в базу)
    new_guest = Guest("Светлова", "Марина", "+79112223344", "Игоревна")
    save_guest(new_guest)

    # 2. Выбираем комнату (допустим, Марина хочет Люкс 301)
    # В реальности мы будем брать ее из базы, но пока создадим объект
    booked_room = LuxRoom(301)

    # 3. Создаем бронь на 12 дней (чтобы сработал наш помощник по скидкам!)
    new_booking = Booking(new_guest, booked_room, "20-04-2026", "02-05-2026")

    # Имитируем работу "помощника" (здесь мы просто вручную поставим скидку)
    if new_booking.nights > 10:
        print(f"\nСистема: Обнаружено проживание {new_booking.nights} ночей.")
        new_booking.discount = 15 # Дарим Марине 15%
        print(f"Применена скидка 15%. Итого к оплате: {new_booking.total_price}")

    # 4. СОХРАНЯЕМ В БАЗУ ДАННЫХ
    print("\nСохраняем бронирование в базу...")
    add_booking_to_db(new_booking)

    print("\n=== ТЕСТ ЗАВЕРШЕН УСПЕШНО ===")

    # 5. ПРОВЕРКА ВЫЕЗДА
    print("\nПроверяем статус комнат перед выездом...")
    from database import get_free_rooms, check_out_guest

    # Постмотрим, какие комнаты свободны (301-й там быть не должно)
    print("Свободные номера:", [r[0] for r in get_free_rooms()])

    print(f"\nВыписываем гостя из номера 301...")
    check_out_guest(301)

    # Проверяем снова (301-й должен вернуться в список)
    print("Свободные номера после выезда:", [r[0] for r in get_free_rooms()])
if __name__ == "__main__":
    run_test()

