# database.py

import sqlite3
import os
from contextlib import contextmanager

DB_NAME = "hotel_admin.db"


# ----------------------------------------------------------------------
# Подключение
# ----------------------------------------------------------------------

@contextmanager
def get_conn():
    """
    Контекстный менеджер подключения к БД.
    Автоматически делает commit при успехе и rollback при ошибке.

    Использование:
        with get_conn() as conn:
            conn.execute(...)
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row          # строки как словари: row["last_name"]
    conn.execute("PRAGMA foreign_keys = ON") # включаем каскадное удаление
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ----------------------------------------------------------------------
# Инициализация базы данных
# ----------------------------------------------------------------------

def init_db():
    """Создаёт таблицы если их нет. Вызывается при каждом старте приложения."""
    with get_conn() as conn:

        # 1. Гости
        conn.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name             TEXT    NOT NULL,
                first_name            TEXT    NOT NULL,
                patronymic            TEXT,
                phone                 TEXT,
                loyalty_balance       INTEGER DEFAULT 0,
                birth_date            TEXT,
                nationality           TEXT    DEFAULT "Россия",
                citizenship           TEXT    DEFAULT "РФ",
                language              TEXT    DEFAULT "Русский",
                registration_address  TEXT,
                doc_type              TEXT    DEFAULT "Паспорт гражданина РФ",
                doc_series            TEXT,
                doc_number            TEXT,
                doc_issued_by         TEXT,
                doc_issue_date        TEXT,
                doc_expiry_date       TEXT,
                doc_department_code   TEXT,
                migration_card_number TEXT,
                migration_card_expiry TEXT,
                passport_scan         TEXT,
                is_complete           INTEGER DEFAULT 0,
                created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Номера
        conn.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                number     INTEGER PRIMARY KEY,
                type       TEXT    NOT NULL,
                daily_rate INTEGER NOT NULL,
                is_busy    INTEGER DEFAULT 0
            )
        ''')

        # 3. Бронирования
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_id         INTEGER NOT NULL,
                room_number      INTEGER NOT NULL,
                check_in         TEXT,
                check_out        TEXT,
                check_in_time    TEXT    DEFAULT "14:00",
                check_out_time   TEXT    DEFAULT "12:00",
                discount         INTEGER DEFAULT 0,
                total_price      INTEGER DEFAULT 0,
                composition      TEXT    DEFAULT "Один",
                adults_count     INTEGER DEFAULT 1,
                children_count   INTEGER DEFAULT 0,
                welcome_gift     TEXT    DEFAULT "Ничего",
                special_requests TEXT,
                complaints       TEXT,
                status           TEXT    DEFAULT "active",
                FOREIGN KEY (guest_id)    REFERENCES guests(id) ON DELETE CASCADE,
                FOREIGN KEY (room_number) REFERENCES rooms(number)
            )
        ''')

        # 4. Доп. услуги к брони
        conn.execute('''
            CREATE TABLE IF NOT EXISTS booking_extras (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                type       TEXT    NOT NULL,
                description TEXT,
                price      INTEGER DEFAULT 0,
                status     TEXT    DEFAULT "requested",
                FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
            )
        ''')

        # 5. Настройки (тарифы раннего заезда / позднего выезда и др.)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # 6. Дополнительные гости в номере
        conn.execute('''
            CREATE TABLE IF NOT EXISTS booking_guests (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                guest_id   INTEGER NOT NULL,
                is_primary INTEGER DEFAULT 0,
                FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                FOREIGN KEY (guest_id)   REFERENCES guests(id)   ON DELETE CASCADE
            )
        ''')

    os.makedirs("scans", exist_ok=True)


def seed_settings():
    """Заполняет тарифы раннего заезда и позднего выезда если их ещё нет."""
    defaults = [
        ("early_checkin_00", "3000"), ("early_checkin_01", "3000"),
        ("early_checkin_02", "3000"), ("early_checkin_03", "2500"),
        ("early_checkin_04", "2500"), ("early_checkin_05", "2000"),
        ("early_checkin_06", "2000"), ("early_checkin_07", "2000"),
        ("early_checkin_08", "1500"), ("early_checkin_09", "1500"),
        ("early_checkin_10", "1000"), ("early_checkin_11", "1000"),
        ("early_checkin_12", "500"),  ("early_checkin_13", "500"),
        ("late_checkout_13", "500"),  ("late_checkout_14", "500"),
        ("late_checkout_15", "1000"), ("late_checkout_16", "1000"),
        ("late_checkout_17", "1500"), ("late_checkout_18", "1500"),
        ("late_checkout_19", "2000"), ("late_checkout_20", "2000"),
        ("late_checkout_21", "2500"), ("late_checkout_22", "2500"),
        ("late_checkout_23", "3000"), ("late_checkout_00", "3000"),
        ("late_checkout_01", "3500"), ("late_checkout_02", "3500"),
        ("late_checkout_03", "3500"), ("late_checkout_04", "3500"),
        ("late_checkout_05", "3000"),
    ]
    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            defaults
        )


def seed_rooms(rooms_data: list[tuple] = None):
    """
    Заполняет номерной фонд.
    rooms_data — список кортежей (number, type, daily_rate).
    Если не передан — используются тестовые данные по умолчанию.
    """
    if rooms_data is None:
        rooms_data = [
            (101, "Стандарт", 2800), (102, "Стандарт", 2800),
            (103, "Семейный", 4000), (104, "Семейный", 4000),
            (105, "Стандарт", 2800), (106, "Эконом",   2400),
            (107, "Эконом",   2400), (108, "Эконом",   2400),
            (109, "Эконом",   2400), (201, "Семейный", 5000),
            (202, "Семейный", 5000), (203, "Стандарт", 3400),
            (204, "Стандарт", 3400), (205, "Стандарт", 3400),
            (206, "Эконом",   2800), (207, "Эконом",   2800),
            (208, "Эконом",   2800), (301, "Люкс",     7000),
            (302, "Люкс",     7000), (303, "Президентский", 15000),
        ]
    with get_conn() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO rooms (number, type, daily_rate) VALUES (?, ?, ?)",
            rooms_data
        )


# ----------------------------------------------------------------------
# Гости
# ----------------------------------------------------------------------

def save_guest(guest_dto) -> int:
    """
    Сохраняет нового гостя. Принимает GuestDTO.
    Возвращает ID созданной записи.
    """
    with get_conn() as conn:
        cursor = conn.execute('''
            INSERT INTO guests (
                last_name, first_name, patronymic, phone,
                doc_type, doc_series, doc_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            guest_dto.last_name,
            guest_dto.first_name,
            guest_dto.patronymic,
            guest_dto.phone,
            guest_dto.doc_type,
            guest_dto.doc_series,
            guest_dto.doc_number,
        ))
        return cursor.lastrowid


def save_guest_extended(guest_dto, extra: dict = None) -> int:
    """
    Сохраняет гостя с расширенными полями (миграционная карта, скан и т.д.).
    extra — словарь с дополнительными полями:
        migration_card_number, migration_card_expiry,
        doc_expiry_date, citizenship, birth_date
    Возвращает ID созданной записи.
    """
    extra = extra or {}
    with get_conn() as conn:
        cursor = conn.execute('''
            INSERT INTO guests (
                last_name, first_name, patronymic, phone,
                doc_type, doc_series, doc_number,
                migration_card_number, migration_card_expiry,
                doc_expiry_date, citizenship, birth_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            guest_dto.last_name,
            guest_dto.first_name,
            guest_dto.patronymic,
            guest_dto.phone,
            guest_dto.doc_type,
            guest_dto.doc_series,
            guest_dto.doc_number,
            extra.get("migration_card_number"),
            extra.get("migration_card_expiry"),
            extra.get("doc_expiry_date"),
            extra.get("citizenship", "РФ"),
            extra.get("birth_date"),
        ))
        return cursor.lastrowid


def update_guest_phone(guest_id: int, new_phone: str):
    """Обновляет телефон гостя."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE guests SET phone = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_phone, guest_id)
        )


def update_guest_full_profile(guest_id: int, data: dict) -> bool:
    """
    Обновляет полную карточку гостя из формы детальной регистрации.
    data — словарь с полями карточки.
    Возвращает True при успехе.
    """
    with get_conn() as conn:
        conn.execute('''
            UPDATE guests SET
                doc_type              = ?,
                doc_series            = ?,
                doc_number            = ?,
                doc_issued_by         = ?,
                doc_issue_date        = ?,
                doc_department_code   = ?,
                doc_expiry_date       = ?,
                registration_address  = ?,
                birth_date            = ?,
                language              = ?,
                migration_card_number = ?,
                migration_card_expiry = ?,
                passport_scan         = ?,
                citizenship           = ?,
                is_complete           = 1,
                updated_at            = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get("doc_type"),
            data.get("doc_series"),
            data.get("doc_number"),
            data.get("doc_issued_by"),
            data.get("doc_issue_date"),
            data.get("doc_department_code"),
            data.get("doc_expiry_date"),
            data.get("registration_address"),
            data.get("birth_date"),
            data.get("language"),
            data.get("migration_card_number"),
            data.get("migration_card_expiry"),
            data.get("passport_scan"),
            data.get("citizenship", "РФ"),
            guest_id,
        ))
    return True


def find_guest_by_doc(doc_type: str, doc_number: str):
    """Ищет гостя по типу и номеру документа. Возвращает строку или None."""
    with get_conn() as conn:
        return conn.execute('''
            SELECT id, last_name, first_name, patronymic, phone
            FROM guests
            WHERE doc_type = ? AND doc_number = ?
        ''', (doc_type, doc_number)).fetchone()


def find_guest_by_russian_passport(series: str, number: str):
    """Ищет гостя по паспорту РФ (серия + номер). Возвращает строку или None."""
    with get_conn() as conn:
        return conn.execute('''
            SELECT id, last_name, first_name, patronymic, phone
            FROM guests
            WHERE doc_type = "Паспорт гражданина РФ"
              AND doc_series = ? AND doc_number = ?
        ''', (series, number)).fetchone()


def get_all_guests() -> list:
    """Возвращает всех гостей (id, last_name, first_name, patronymic, phone, is_complete)."""
    with get_conn() as conn:
        return conn.execute('''
            SELECT id, last_name, first_name, patronymic, phone, is_complete
            FROM guests ORDER BY last_name
        ''').fetchall()


def search_guests(query: str) -> list:
    """Поиск гостей по ID, фамилии или телефону."""
    pattern = f"%{query}%"
    with get_conn() as conn:
        return conn.execute('''
            SELECT id, last_name, first_name, patronymic, phone, is_complete
            FROM guests
            WHERE CAST(id AS TEXT) LIKE ?
               OR last_name LIKE ?
               OR phone LIKE ?
            ORDER BY last_name
        ''', (pattern, pattern, pattern)).fetchall()


def get_guest_by_id(guest_id: int):
    """Возвращает полную строку гостя по ID или None."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM guests WHERE id = ?", (guest_id,)
        ).fetchone()


# ----------------------------------------------------------------------
# Номера
# ----------------------------------------------------------------------

def get_free_rooms() -> list:
    """Возвращает список свободных номеров (number, type, daily_rate)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT number, type, daily_rate FROM rooms WHERE is_busy = 0"
        ).fetchall()


def get_rooms_with_status() -> list:
    """
    Возвращает все номера с текущим статусом и данными гостя если занят.
    Поля: number, type, daily_rate, is_busy,
          last_name, first_name, check_in, check_out, guest_id
    """
    with get_conn() as conn:
        return conn.execute('''
            SELECT
                r.number, r.type, r.daily_rate, r.is_busy,
                COALESCE(g.last_name,  "") AS last_name,
                COALESCE(g.first_name, "") AS first_name,
                COALESCE(b.check_in,   "") AS check_in,
                COALESCE(b.check_out,  "") AS check_out,
                COALESCE(b.guest_id,    0) AS guest_id
            FROM rooms r
            LEFT JOIN bookings b ON r.number = b.room_number AND b.status = "active"
            LEFT JOIN guests   g ON b.guest_id = g.id
            ORDER BY r.number
        ''').fetchall()


def check_out_guest(room_number: int) -> bool:
    """
    Выселяет гостя: закрывает активную бронь и освобождает номер.
    Возвращает True при успехе, False если номер уже свободен.
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT is_busy FROM rooms WHERE number = ?", (room_number,)
        ).fetchone()

        if not row or row["is_busy"] == 0:
            return False

        conn.execute(
            "UPDATE bookings SET status = 'closed' WHERE room_number = ? AND status = 'active'",
            (room_number,)
        )
        conn.execute(
            "UPDATE rooms SET is_busy = 0 WHERE number = ?",
            (room_number,)
        )
        return True


# ----------------------------------------------------------------------
# Бронирования
# ----------------------------------------------------------------------

def add_booking(booking_dto, check_in_time: str = "14:00", check_out_time: str = "12:00") -> int:
    """
    Сохраняет бронь и помечает номер как занятый.
    Принимает BookingDTO.
    Возвращает ID созданной брони.
    """
    with get_conn() as conn:
        # Проверяем что номер существует
        room = conn.execute(
            "SELECT number FROM rooms WHERE number = ?", (booking_dto.room.number,)
        ).fetchone()
        if not room:
            raise ValueError(f"Номер {booking_dto.room.number} не найден в базе.")

        # Помечаем номер занятым
        conn.execute(
            "UPDATE rooms SET is_busy = 1 WHERE number = ?",
            (booking_dto.room.number,)
        )

        # Сохраняем бронь
        cursor = conn.execute('''
            INSERT INTO bookings (
                guest_id, room_number,
                check_in, check_out,
                check_in_time, check_out_time,
                discount, total_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            booking_dto.guest.guest_id,
            booking_dto.room.number,
            booking_dto.check_in.strftime("%d.%m.%Y"),
            booking_dto.check_out.strftime("%d.%m.%Y"),
            check_in_time,
            check_out_time,
            booking_dto.discount,
            booking_dto.total_price,
        ))

        booking_id = cursor.lastrowid

        # Сохраняем доп. услуги если есть
        if booking_dto.extras:
            conn.executemany(
                "INSERT INTO booking_extras (booking_id, type, price) VALUES (?, ?, ?)",
                [(booking_id, name, price) for name, price in booking_dto.extras.items()]
            )

        return booking_id


def update_booking_gr_data(guest_id: int, gr_data: dict):
    """
    Обновляет Guest Relation данные в последней активной брони гостя.
    gr_data — словарь: composition, adults, children, welcome_gift,
                        special_requests, complaints
    """
    with get_conn() as conn:
        row = conn.execute('''
            SELECT id FROM bookings
            WHERE guest_id = ? AND status = "active"
            ORDER BY id DESC LIMIT 1
        ''', (guest_id,)).fetchone()

        if not row:
            return  # нет активной брони — ничего не делаем

        conn.execute('''
            UPDATE bookings SET
                composition      = ?,
                adults_count     = ?,
                children_count   = ?,
                welcome_gift     = ?,
                special_requests = ?,
                complaints       = ?
            WHERE id = ?
        ''', (
            gr_data.get("composition",      "Один"),
            gr_data.get("adults",           1),
            gr_data.get("children",         0),
            gr_data.get("welcome_gift",     "Ничего"),
            gr_data.get("special_requests", ""),
            gr_data.get("complaints",       ""),
            row["id"],
        ))


def get_booking_by_room(room_number: int):
    """Возвращает активную бронь для номера или None."""
    with get_conn() as conn:
        return conn.execute('''
            SELECT check_in, check_out, total_price, discount
            FROM bookings
            WHERE room_number = ? AND status = "active"
            ORDER BY id DESC LIMIT 1
        ''', (room_number,)).fetchone()


def get_active_booking_id(room_number: int) -> int | None:
    """Возвращает ID активной брони для номера или None."""
    with get_conn() as conn:
        row = conn.execute('''
            SELECT id FROM bookings
            WHERE room_number = ? AND status = "active"
            ORDER BY id DESC LIMIT 1
        ''', (room_number,)).fetchone()
        return row["id"] if row else None


def get_all_bookings() -> list:
    """Возвращает все брони (для истории / отчётов)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM bookings ORDER BY id DESC"
        ).fetchall()

def auto_checkout_expired_bookings():
    with get_conn() as conn:
        conn.execute("""
            UPDATE bookings 
            SET status = 'completed'
            WHERE status = 'active' 
            AND substr(check_out, 7, 4) || '-' || 
                substr(check_out, 4, 2) || '-' || 
                substr(check_out, 1, 2) < DATE('now')
        """)
        conn.execute("""
            UPDATE rooms
            SET is_busy = 0
            WHERE number IN (
                SELECT room_number FROM bookings
                WHERE status = 'completed'
                AND substr(check_out, 7, 4) || '-' || 
                    substr(check_out, 4, 2) || '-' || 
                    substr(check_out, 1, 2) < DATE('now')
            )
        """)


# ----------------------------------------------------------------------
# Гости в номере (доп. жильцы)
# ----------------------------------------------------------------------

def add_guest_to_booking(booking_id: int, guest_id: int, is_primary: int = 0):
    """Добавляет гостя в бронь (для доп. жильцов)."""
    with get_conn() as conn:
        conn.execute('''
            INSERT INTO booking_guests (booking_id, guest_id, is_primary)
            VALUES (?, ?, ?)
        ''', (booking_id, guest_id, is_primary))


def get_booking_guests(booking_id: int) -> list:
    """Возвращает список гостей в брони."""
    with get_conn() as conn:
        return conn.execute('''
            SELECT
                g.id, g.last_name, g.first_name, g.patronymic,
                g.doc_type, g.doc_number, g.birth_date, bg.is_primary
            FROM booking_guests bg
            JOIN guests g ON bg.guest_id = g.id
            WHERE bg.booking_id = ?
            ORDER BY bg.is_primary DESC
        ''', (booking_id,)).fetchall()


# ----------------------------------------------------------------------
# Настройки
# ----------------------------------------------------------------------

def save_setting(key: str, value: str):
    """Сохраняет или обновляет настройку."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )


def get_setting(key: str, default: str = None) -> str | None:
    """Возвращает значение настройки или default если не найдена."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default


# ----------------------------------------------------------------------
# Точка входа
# ----------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    seed_settings()
    seed_rooms()
    print("БД инициализирована.")
    print(f"Свободных номеров: {len(get_free_rooms())}")
    print(f"Всего гостей: {len(get_all_guests())}")
