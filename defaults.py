def seed_settings():
    conn = get_conn()
    cursor = conn.cursor()

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

    cursor.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        defaults
    )
    conn.commit()
    conn.close()

    def seed_rooms(rooms_data):
        """Заполняет номера — принимает список от пользователя"""
        conn = get_conn()
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT OR IGNORE INTO rooms (number, type, daily_rate) VALUES (?, ?, ?)",
            rooms_data
        )
        conn.commit()
        conn.close()

    def seed_rooms():
        rooms_data = [
            (101, "Стандарт", 2800),
            (102, "Стандарт", 2800),
            (103, "Семейный", 4000),
            (104, "Семейный", 4000),
            (105, "Стандарт", 2800),
            (106, "Эконом", 2400),
            (107, "Эконом", 2400),
            (108, "Эконом", 2400),
            (109, "Эконом", 2400),
            (201, "Семейный", 5000),
            (202, "Семейный", 5000),
            (203, "Стандарт", 3400),
            (204, "Стандарт", 3400),
            (205, "Стандарт", 3400),
            (206, "Эконом", 2800),
            (207, "Эконом", 2800),
            (208, "Эконом", 2800),
            (301, "Люкс", 7000),
            (302, "Люкс", 7000),
            (303, "Президентский", 15000),
        ]

        conn = get_conn()
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT OR IGNORE INTO rooms (number, type, daily_rate) VALUES (?, ?, ?)",
            rooms_data
        )
        conn.commit()
        conn.close()

