# dto.py
#
# DTO (Data Transfer Object) — лёгкие объекты для передачи данных
# между доменным слоем (Guest, Room, Booking) и базой данных / GUI.
#
# Правила DTO:
#   - никакой бизнес-логики и валидации
#   - никаких вычислений
#   - только хранение данных
#   - собираются из доменных объектов через фабричные методы from_*

from __future__ import annotations
from datetime import date


# ----------------------------------------------------------------------
# GuestDTO
# ----------------------------------------------------------------------

class GuestDTO:
    """Транспортный объект гостя. Передаётся в database.py для сохранения."""

    def __init__(
        self,
        last_name:       str,
        first_name:      str,
        patronymic:      str  = "",
        phone:           str  = "",
        doc_type:        str  = "Паспорт гражданина РФ",
        doc_series:      str  = "",
        doc_number:      str  = "",
        loyalty_balance: int  = 0,
        guest_id:        int  = None,
    ):
        self.last_name       = last_name
        self.first_name      = first_name
        self.patronymic      = patronymic
        self.phone           = phone
        self.doc_type        = doc_type
        self.doc_series      = doc_series
        self.doc_number      = doc_number
        self.loyalty_balance = loyalty_balance
        self.guest_id        = guest_id        # None если гость ещё не сохранён в БД

    @property
    def full_name(self) -> str:
        """Фамилия Имя Отчество (отчество — если есть)."""
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return " ".join(parts)

    @classmethod
    def from_guest(cls, guest) -> GuestDTO:
        """Собирает GuestDTO из доменного объекта Guest."""
        return cls(
            last_name       = guest.last_name,
            first_name      = guest.first_name,
            patronymic      = guest.patronymic,
            phone           = guest.phone,
            loyalty_balance = guest.loyalty_balance,
        )

    def __repr__(self) -> str:
        return f"GuestDTO(full_name={self.full_name!r}, phone={self.phone!r})"


# ----------------------------------------------------------------------
# RoomDTO
# ----------------------------------------------------------------------

class RoomDTO:
    """Транспортный объект номера."""

    def __init__(
        self,
        number:     int,
        room_type:  str,
        daily_rate: int,
        is_busy:    bool = False,
        room_id:    int  = None,
    ):
        self.number     = number
        self.room_type  = room_type
        self.daily_rate = daily_rate
        self.is_busy    = is_busy
        self.room_id    = room_id          # None если номер ещё не сохранён в БД

    @classmethod
    def from_room(cls, room) -> RoomDTO:
        """Собирает RoomDTO из доменного объекта Room."""
        return cls(
            number    = room.number,
            room_type = room.room_type,
            daily_rate= room.daily_rate,
            is_busy   = room.is_busy,
        )

    def __repr__(self) -> str:
        return f"RoomDTO(number={self.number}, type={self.room_type!r}, rate={self.daily_rate})"


# ----------------------------------------------------------------------
# BookingDTO
# ----------------------------------------------------------------------

class BookingDTO:
    """Транспортный объект бронирования."""

    def __init__(
        self,
        guest:       GuestDTO,
        room:        RoomDTO,
        check_in:    date,
        check_out:   date,
        nights:      int,
        total_price: int,
        discount:    int  = 0,
        extras:      dict = None,
        booking_id:  int  = None,
    ):
        self.guest       = guest
        self.room        = room
        self.check_in    = check_in
        self.check_out   = check_out
        self.nights      = nights
        self.total_price = total_price
        self.discount    = discount
        self.extras      = extras or {}    # {"Ранний заезд": 500, ...}
        self.booking_id  = booking_id      # None если бронь ещё не сохранена в БД

    @classmethod
    def from_booking(cls, booking) -> BookingDTO:
        """
        Собирает BookingDTO из доменного объекта Booking.
        Все вычисления уже сделаны в Booking — DTO просто забирает готовые данные.
        """
        return cls(
            guest       = GuestDTO.from_guest(booking.guest),
            room        = RoomDTO.from_room(booking.room),
            check_in    = booking.check_in,
            check_out   = booking.check_out,
            nights      = booking.nights,
            total_price = booking.total_price,
            discount    = booking.discount,
            extras      = dict(booking._extras),
        )

    def __repr__(self) -> str:
        return (
            f"BookingDTO(guest={self.guest.full_name!r}, "
            f"room={self.room.number}, "
            f"check_in={self.check_in}, "
            f"total={self.total_price})"
        )
