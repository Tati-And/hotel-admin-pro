# booking.py

from datetime import date

from guest import Guest
from room import Room, create_room


class Booking:
    """
    Доменный класс бронирования.
    Отвечает за валидацию дат, расчёт стоимости и управление скидкой.
    """

    def __init__(
        self,
        guest:     Guest,
        room:      Room,
        check_in:  date,
        check_out: date,
        discount:  int = 0,
    ):
        # Гость и номер — обязательны
        self.guest = guest
        self.room  = room

        # Даты — через сеттеры с валидацией
        self._check_in  = None
        self._check_out = None
        self.check_in   = check_in
        self.check_out  = check_out

        # Скидка — через сеттер (0–100%)
        self._discount = 0
        self.discount  = discount

        # Доп. услуги (ранний заезд, поздний выезд и т.д.) — копятся здесь
        # GUI добавляет через add_extra(), не трогая total_price напрямую
        self._extras: dict[str, int] = {}

        # Помечаем номер как занятый
        self.room.is_busy = True

    # ------------------------------------------------------------------
    # Валидация дат
    # ------------------------------------------------------------------

    @property
    def check_in(self) -> date:
        return self._check_in

    @check_in.setter
    def check_in(self, value: date):
        if not isinstance(value, date):
            raise TypeError("Дата заезда должна быть объектом datetime.date.")
        self._check_in = value

    @property
    def check_out(self) -> date:
        return self._check_out

    @check_out.setter
    def check_out(self, value: date):
        if not isinstance(value, date):
            raise TypeError("Дата выезда должна быть объектом datetime.date.")
        if self._check_in and value <= self._check_in:
            raise ValueError("Дата выезда должна быть позже даты заезда.")
        self._check_out = value

    # ------------------------------------------------------------------
    # Скидка
    # ------------------------------------------------------------------

    @property
    def discount(self) -> int:
        return self._discount

    @discount.setter
    def discount(self, value):
        try:
            numeric = int(value)
        except (ValueError, TypeError):
            raise ValueError("Скидка должна быть целым числом.")
        if not (0 <= numeric <= 100):
            raise ValueError("Скидка должна быть от 0 до 100%.")
        self._discount = numeric

    # ------------------------------------------------------------------
    # Доп. услуги
    # ------------------------------------------------------------------

    def add_extra(self, name: str, price: int):
        """Добавляет доп. услугу (ранний заезд, поздний выезд и т.д.)."""
        if price < 0:
            raise ValueError("Стоимость услуги не может быть отрицательной.")
        self._extras[name] = price

    def remove_extra(self, name: str):
        """Убирает доп. услугу по названию."""
        self._extras.pop(name, None)

    @property
    def extras_total(self) -> int:
        """Сумма всех доп. услуг."""
        return sum(self._extras.values())

    # ------------------------------------------------------------------
    # Расчёт стоимости
    # ------------------------------------------------------------------

    @property
    def nights(self) -> int:
        """Количество ночей."""
        return max(1, (self.check_out - self.check_in).days)

    @property
    def base_price(self) -> int:
        """Стоимость проживания без скидки и доп. услуг."""
        return self.nights * self.room.daily_rate

    @property
    def total_price(self) -> int:
        """
        Итоговая стоимость:
        (базовая цена со скидкой) + доп. услуги.
        """
        discounted = self.base_price * (1 - self.discount / 100)
        return int(discounted) + self.extras_total

    # ------------------------------------------------------------------
    # Представление
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return (
            f"Бронь: {self.guest.full_name} | "
            f"Номер: {self.room.number} ({self.room.room_type}) | "
            f"Заезд: {self.check_in.strftime('%d.%m.%Y')} | "
            f"Выезд: {self.check_out.strftime('%d.%m.%Y')} | "
            f"Ночей: {self.nights} | "
            f"Итого: {self.total_price} руб."
        )

    def __repr__(self) -> str:
        return (
            f"Booking(guest={self.guest.last_name!r}, "
            f"room={self.room.number}, "
            f"check_in={self.check_in}, "
            f"check_out={self.check_out})"
        )


# ----------------------------------------------------------------------
# Тест
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- Тестирование класса Booking ---\n")

    guest1 = Guest("Иванов", "Иван", "Петрович", "+79032314586")
    room1  = create_room(356, "Люкс", 7000)

    b = Booking(guest1, room1, date(2026, 4, 15), date(2026, 4, 26))
    print(b)
    print(f"Ночей: {b.nights} | Базовая цена: {b.base_price} руб.")

    # Скидка
    b.discount = 10
    print(f"\nСкидка {b.discount}% → итого: {b.total_price} руб.")

    # Доп. услуги
    b.add_extra("Ранний заезд", 500)
    b.add_extra("Поздний выезд", 700)
    print(f"Доп. услуги: {b._extras} → +{b.extras_total} руб.")
    print(f"Итого с услугами: {b.total_price} руб.")

    # Убираем услугу
    b.remove_extra("Ранний заезд")
    print(f"Убрали ранний заезд → итого: {b.total_price} руб.")

    print("\n--- Проверка защиты ---")

    # Неверный тип даты
    try:
        Booking(guest1, room1, "15.04.2026", date(2026, 4, 26))
    except TypeError as e:
        print(f"Неверный тип даты: {e}")

    # Выезд раньше заезда
    try:
        Booking(guest1, room1, date(2026, 4, 26), date(2026, 4, 15))
    except ValueError as e:
        print(f"Выезд раньше заезда: {e}")

    # Скидка вне диапазона
    try:
        b.discount = 150
    except ValueError as e:
        print(f"Неверная скидка: {e}")

    # Скидка строкой
    try:
        b.discount = "много"
    except ValueError as e:
        print(f"Скидка строкой: {e}")
