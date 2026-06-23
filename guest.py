# guest.py

import phonenumbers
from phonenumbers import NumberParseException


class Guest:
    """
    Доменный класс гостя отеля.
    Отвечает за валидацию персональных данных и управление бонусным балансом.
    """

    def __init__(
        self,
        last_name:       str,
        first_name:      str,
        patronymic:      str = "",
        phone:           str = "",
        loyalty_balance: int = 0,
    ):
        # Обязательные поля — сразу через сеттер, валидация внутри
        self.last_name  = last_name
        self.first_name = first_name
        self.patronymic = patronymic

        # Телефон необязателен — сначала пустая строка,
        # сеттер вызывается только если значение передано
        self._phone = ""
        if phone:
            self.phone = phone

        # Баланс необязателен — сначала 0,
        # сеттер проверяет что значение не отрицательное
        self._loyalty_balance = 0
        self.loyalty_balance = loyalty_balance

    # ------------------------------------------------------------------
    # Валидация имени / фамилии
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_name(value: str, field: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"Поле '{field}' не может быть пустым.")
        if any(ch.isdigit() for ch in value):
            raise ValueError(f"Поле '{field}' не должно содержать цифры.")
        return value

    @property
    def last_name(self) -> str:
        return self._last_name

    @last_name.setter
    def last_name(self, value: str):
        self._last_name = self._validate_name(value, "Фамилия")

    @property
    def first_name(self) -> str:
        return self._first_name

    @first_name.setter
    def first_name(self, value: str):
        self._first_name = self._validate_name(value, "Имя")

    # ------------------------------------------------------------------
    # Телефон — международный формат E.164
    # ------------------------------------------------------------------

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str):
        if not value:
            self._phone = ""
            return
        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(f"Номер «{value}» не является действительным.")
            self._phone = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except NumberParseException:
            raise ValueError(
                f"Номер «{value}» должен начинаться с «+» и содержать код страны."
            )

    # ------------------------------------------------------------------
    # Бонусный баланс
    # ------------------------------------------------------------------

    @property
    def loyalty_balance(self) -> int:
        return self._loyalty_balance

    @loyalty_balance.setter
    def loyalty_balance(self, value: int):
        if not isinstance(value, int) or value < 0:
            raise ValueError("Бонусный баланс должен быть целым неотрицательным числом.")
        self._loyalty_balance = value

    def add_bonuses(self, amount: int) -> int:
        """Начисляет бонусы. Возвращает новый баланс."""
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("Сумма начисления должна быть положительным целым числом.")
        self._loyalty_balance += amount
        return self._loyalty_balance

    def spend_bonuses(self, amount: int) -> int:
        """Списывает бонусы. Возвращает новый баланс."""
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError("Сумма списания должна быть положительным целым числом.")
        if amount > self._loyalty_balance:
            raise ValueError(
                f"Недостаточно бонусов: баланс {self._loyalty_balance}, запрошено {amount}."
            )
        self._loyalty_balance -= amount
        return self._loyalty_balance

    # ------------------------------------------------------------------
    # Представление
    # ------------------------------------------------------------------

    @property
    def full_name(self) -> str:
        """Фамилия Имя Отчество (отчество — если есть)."""
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return " ".join(parts)

    def __str__(self) -> str:
        phone_str = self.phone or "не указан"
        return (
            f"Гость: {self.full_name} | "
            f"Тел: {phone_str} | "
            f"Бонусы: {self.loyalty_balance}"
        )

    def __repr__(self) -> str:
        return (
            f"Guest(last_name={self.last_name!r}, "
            f"first_name={self.first_name!r}, "
            f"phone={self.phone!r})"
        )


# ----------------------------------------------------------------------
# Тест
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- Тестирование класса Guest ---\n")

    # 1. Корректный гость с отчеством
    g1 = Guest("Иванов", "Иван", "Петрович", "+79001112233")
    print(f"Создан: {g1}")

    # 2. Гость без отчества и телефона
    g2 = Guest("Смирнова", "Анна")
    print(f"Создан: {g2}")

    # 3. Бонусы
    new_balance = g1.add_bonuses(500)
    print(f"\nНачислено 500 бонусов. Баланс: {new_balance}")
    new_balance = g1.spend_bonuses(200)
    print(f"Списано 200 бонусов. Баланс: {new_balance}")

    # 4. Защита: пустая фамилия
    print("\n--- Проверка защиты ---")
    try:
        Guest("", "Иван")
    except ValueError as e:
        print(f"Пустая фамилия: {e}")

    # 5. Защита: цифры в имени
    try:
        Guest("Иванов", "Ив4н")
    except ValueError as e:
        print(f"Цифры в имени: {e}")

    # 6. Защита: неверный телефон
    try:
        Guest("Петров", "Пётр", phone="12345")
    except ValueError as e:
        print(f"Неверный телефон: {e}")

    # 7. Защита: списание больше баланса
    try:
        g2.spend_bonuses(100)
    except ValueError as e:
        print(f"Списание сверх баланса: {e}")