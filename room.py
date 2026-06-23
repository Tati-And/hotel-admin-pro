# room.py

ROOM_TYPES = {
    "Эконом":           "EconomRoom",
    "Стандарт":         "StandardRoom",
    "Семейный":         "FamilyRoom",
    "Люкс":             "LuxRoom",
    "Президентский":    "PresidentialRoom",
}


class Room:
    """Базовый класс гостиничного номера."""

    room_type: str = "Номер"  # переопределяется в подклассах

    def __init__(self, number: int, daily_rate: int, is_busy: bool = False):
        self._number = 0
        self.number = number          # через сеттер с валидацией
        self.daily_rate = daily_rate
        self.is_busy = is_busy

    # ------------------------------------------------------------------
    # Валидация номера комнаты
    # ------------------------------------------------------------------
    @property
    def number(self) -> int:
        return self._number

    @number.setter
    def number(self, value):
        if not str(value).isdigit():
            raise ValueError("Номер комнаты должен состоять только из цифр!")
        self._number = int(value)

    # ------------------------------------------------------------------
    # Представление
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        status = "Занят" if self.is_busy else "Свободен"
        return (
            f"№{self.number} | {self.room_type} | "
            f"{self.daily_rate} руб/сут | {status}"
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(number={self.number}, daily_rate={self.daily_rate})"


# ----------------------------------------------------------------------
# Подклассы — отличаются только типом. Цена всегда берётся из БД.
# ----------------------------------------------------------------------

class EconomRoom(Room):
    room_type = "Эконом"


class StandardRoom(Room):
    room_type = "Стандарт"


class FamilyRoom(Room):
    room_type = "Семейный"


class LuxRoom(Room):
    room_type = "Люкс"


class PresidentialRoom(Room):
    room_type = "Президентский"


# ----------------------------------------------------------------------
# Фабричная функция: создаёт нужный подкласс по строке типа из БД
# ----------------------------------------------------------------------

_ROOM_CLASS_MAP = {
    "Эконом":           EconomRoom,
    "Стандарт":         StandardRoom,
    "Семейный":         FamilyRoom,
    "Люкс":             LuxRoom,
    "Президентский":    PresidentialRoom,
}

def create_room(number: int, room_type: str, daily_rate: int, is_busy: bool = False) -> Room:
    """
    Фабрика: возвращает экземпляр нужного подкласса Room.
    Если тип неизвестен — возвращает базовый Room.
    """
    cls = _ROOM_CLASS_MAP.get(room_type, Room)
    room = cls(number, daily_rate, is_busy)
    if cls is Room:
        room.room_type = room_type  # сохраняем тип как есть, даже если не знаем класс
    return room


# ----------------------------------------------------------------------
# Тест
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- Тестирование классов Room ---\n")

    rooms = [
        create_room(106, "Эконом",       2400),
        create_room(203, "Стандарт",     3400),
        create_room(103, "Семейный",     4000),
        create_room(301, "Люкс",         7000),
        create_room(303, "Президентский", 15000),
    ]

    print("Список номеров:")
    for r in rooms:
        print(r)

    print("\nБронируем Люкс 301...")
    rooms[3].is_busy = True
    print(rooms[3])

    print("\nПроверка isinstance:")
    print(f"LuxRoom является Room: {isinstance(rooms[3], Room)}")

    print("\nПроверка защиты номера:")
    try:
        bad = StandardRoom("30o1", 3000)
    except ValueError as e:
        print(f"Ошибка поймана: {e}")

    print("\nПроверка фабрики с неизвестным типом:")
    unknown = create_room(999, "Апартаменты", 10000)
    print(unknown)