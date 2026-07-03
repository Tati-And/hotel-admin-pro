import customtkinter as ctk
import tkinter as tk
import datetime

from database import init_db, seed_rooms
from database import (
    get_all_guests, get_free_rooms, add_booking,
    get_rooms_with_status, get_guest_by_id, update_guest_full_profile,
    find_guest_by_russian_passport, find_guest_by_doc, update_guest_phone,
    save_guest_extended, update_booking_gr_data, get_setting, save_setting,
    add_guest_to_booking, get_booking_guests, get_active_booking_id,
    check_out_guest, auto_checkout_expired_bookings
)
from dto import GuestDTO, BookingDTO, RoomDTO
from tkcalendar import Calendar


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Список типов документов — единое место, используется во всех формах
DOC_TYPES_RF = [
    "Паспорт гражданина РФ",
    "Паспорт гражданина СССР",
    "Загранпаспорт",
    "Водительское удостоверение РФ",
    "Удостоверение военнослужащего",
    "Временное удостоверение личности",
]
DOC_TYPES_FOREIGN = ["Загранпаспорт"]
DOC_TYPES_ALL = DOC_TYPES_RF + ["Свидетельство о рождении"]

class HotelApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        auto_checkout_expired_bookings()

        self.columns_count = 4
        self._ui_scale = 1.0

        self.title("HotelAdmin Pro - Система управления отелем")
        self.after(0, lambda: self.state('zoomed'))

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="HOTEL ADMIN", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20, padx=20)

        self.btn_rooms = ctk.CTkButton(self.sidebar_frame, text="Номера", command=self.show_rooms)
        self.btn_rooms.pack(pady=10, padx=20)

        self.btn_guests = ctk.CTkButton(self.sidebar_frame, text="Гости", command=self.show_guests)
        self.btn_guests.pack(pady=10, padx=20)

        self.btn_book = ctk.CTkButton(self.sidebar_frame, text="Забронировать", command=self.show_booking_form)
        self.btn_book.pack(pady=10, padx=20)

        self.btn_settings = ctk.CTkButton(
            self.sidebar_frame,
            text="Настройки",
            command=self.open_settings,
            fg_color="transparent",
            border_width=1,
            text_color=("#1a1a1a", "#D3D3D3")
        )
        self.btn_settings.pack(side="bottom", pady=20, padx=20)

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.label_welcome = ctk.CTkLabel(self.main_frame, text="Добро пожаловать в систему!", font=ctk.CTkFont(size=20))
        self.label_welcome.pack(pady=20)

        self.tooltip_window = None
        self.tooltip_timer = None
        self._tooltip_text = ""
        self._tooltip_x = 0
        self._tooltip_y = 0

        self._early_checkin_price = 0
        self._late_checkout_price = 0

        self.current_screen = "rooms"
        self._details_window = None  # отслеживаем единственное окно деталей номера

    document_rules = {
        "Паспорт гражданина РФ": {
            "show_series": True,
            "series_placeholder": "Серия",
            "number_placeholder": "Номер паспорта",
            "show_expiry": False,
            "expiry_label": "",
            "block_title": "Паспортные данные"
        },
        "Паспорт гражданина СССР": {
            "show_series": True,
            "series_placeholder": "Серия",
            "number_placeholder": "Номер паспорта",
            "show_expiry": False,
            "expiry_label": "",
            "block_title": "Паспортные данные"
        },
        "Загранпаспорт": {
            "show_series": False,
            "series_placeholder": "",
            "number_placeholder": "Номер загранпаспорта",
            "show_expiry": True,
            "expiry_label": "Срок действия загранпаспорта:",
            "block_title": "Данные загранпаспорта"
        },
        "Водительское удостоверение РФ": {
            "show_series": True,
            "series_placeholder": "Серия ВУ",
            "number_placeholder": "Номер ВУ",
            "show_expiry": True,
            "expiry_label": "Срок действия ВУ:",
            "block_title": "Реквизиты ВУ"
        },
        "Удостоверение военнослужащего": {
            "show_series": True,
            "series_placeholder": "Серия",
            "number_placeholder": "Номер удостоверения",
            "show_expiry": False,
            "expiry_label": "",
            "block_title": "Реквизиты удостоверения"
        },
        "Временное удостоверение личности": {
            "show_series": False,
            "series_placeholder": "",
            "number_placeholder": "Номер удостоверения",
            "show_expiry": True,
            "expiry_label": "Срок действия удостоверения:",
            "block_title": "Данные временного удостоверения"
        },
        "Свидетельство о рождении": {
            "show_series": False,
            "series_placeholder": "",
            "number_placeholder": "Номер свидетельства",
            "show_expiry": False,
            "block_title": "Данные свидетельства о рождении"
        }
    }

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_rooms(self):

        self.current_screen = "rooms"
        self.clear_main_frame()

        auto_checkout_expired_bookings()

        ctk.CTkLabel(self.main_frame, text="Состояние номерного фонда", font=("Arial", 20)).pack(pady=20)

        # Создаем контейнер для карточек (сетка)
        scroll_frame = ctk.CTkScrollableFrame(self.main_frame, width=800, height=450, fg_color="transparent")

        rooms_data = get_rooms_with_status()

        # Настройка колонок
        cols = self.columns_count
        scroll_frame.grid_columnconfigure(list(range(cols)), weight=1,  uniform="group1")


        for i, r in enumerate(rooms_data):
            # r[0]-№, r[1]-тип, r[2]-цена, r[3]-статус, r[4]-фамилия, r[5]-имя
            num, r_type, price, is_busy, l_name, f_name, check_in, check_out, guest_id = r

            # Выбираем цвет: зеленый если свободен, красный если занят
            color = "#27ae60" if not is_busy else "#c0392b"

            if is_busy:
                hint_text = f"Бронь:\nГость: {l_name} {f_name[0]}.\nЗаезд: {check_in}\nВыезд: {check_out}\nСтатус: Оплачено"
            else:
                hint_text = "СВОБОДЕН\nБронирований нет"

            # Функция-обработчик клика (лямбда)
            click_handler = lambda event, n=num:self.open_room_details(n, event)

            # Создаем ОДНУ карточку
            card = ctk.CTkFrame(scroll_frame, fg_color=color, corner_radius=12, width=140, height=125)
            card.pack_propagate(False)
            card.grid_propagate(False)
            card.grid(row=i // cols, column=i % cols, padx=5, pady=5, sticky="nsew")
            card.bind("<Button-1>", click_handler) # Привязываем клик к самой карточке

            card.bind("<Enter>", lambda e, t=hint_text: self.show_tooltip(e, t))

            card.bind("<Leave>", lambda e: self.hide_tooltip(e))

            content_inner = ctk.CTkFrame(card, fg_color="transparent")
            content_inner.pack(expand=True)
            content_inner.bind("<Button-1>", click_handler)

            # Наполняем карточку текстом и КАЖДОМУ тексту тоже привязываем клик
            lbl_num = ctk.CTkLabel(content_inner, text=f"№ {num}", font=("Arial", 16), text_color="white")
            lbl_num.pack()
            lbl_num.bind("<Button-1>", click_handler)

            lbl_type = ctk.CTkLabel(content_inner, text=r_type, text_color="white")
            lbl_type.pack()
            lbl_type.bind("<Button-1>", click_handler)

            lbl_price = ctk.CTkLabel(content_inner, text=f"{price} руб/сут", text_color="white")
            lbl_price.pack()
            lbl_price.bind("<Button-1>", click_handler)

            lbl_status = None
            if is_busy:
                status_text = f"{l_name} {f_name[0]}."
                if len(status_text) > 15:
                    status_text = status_text[:13] + ".."

                f_size = 12 if len(status_text) <= 13 else 10

                lbl_status = ctk.CTkLabel(
                    content_inner,
                    text=status_text,
                    font=("Arial", f_size),
                    text_color="white",
                )
                lbl_status.pack(pady=(0, 5))
                lbl_status.bind("<Button-1>", click_handler)

            all_widgets = [card, content_inner, lbl_num, lbl_type, lbl_price]
            if is_busy:
                all_widgets.append(lbl_status)

            for w in all_widgets:
                w.bind("<Enter>", lambda e, t=hint_text: self.show_tooltip(e, t))
                w.bind("<Leave>", lambda e: self.hide_tooltip(e))
                w.bind("<Motion>", lambda e: self.move_tooltip(e))

        # Показываем с задержкой 80мс — за это время шрифты успевают загрузиться
        self.after(80, lambda: scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10)))

    def show_guests(self):

        self.current_screen = "guests"
        self.clear_main_frame()

        ctk.CTkLabel(
            self.main_frame,
            text="Список гостей",
            font=("Arial", 20)
        ).pack(pady=(20, 5))

        guests = get_all_guests()

        ctk.CTkLabel(
            self.main_frame,
            text=f"Всего в базе: {len(guests)} гостей",
            font=("Arial", 13),
            text_color="#888888"
        ).pack(pady=(0, 15))

        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.pack(pady=(0, 20))

        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍   Поиск по ID, имени или телефону...",
            textvariable=self.search_var,
            width=500,
            height=45,
            font=("Arial", 15),
            corner_radius=8
        )
        search_entry.pack()
        search_entry.focus()

        table_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            corner_radius=12,
            fg_color="transparent",
        )
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 25))

        # Создаём заголовок таблицы (один раз)
        headers = ["ID", "👤  Фамилия", "Имя", "Отчество", "📞  Телефон", "Карточка"]
        widths = [60, 140, 110, 140, 130, 90]

        header_row = ctk.CTkFrame(table_frame, fg_color="#2b2b2b", corner_radius=8, height=45)
        header_row.pack(fill="x", padx=5, pady=(8, 4))
        header_row.pack_propagate(False)

        for h, w in zip(headers, widths):
            ctk.CTkLabel(
                header_row,
                text=h,
                font=("Arial", 14),
                width=w,
                anchor="w",
                text_color="#4a9eff"
            ).pack(side="left", padx=(15, 0))

        # Сохраняем виджеты как атрибуты для доступа в _update_guest_table
        self.guest_table_frame = table_frame
        self.guest_header_row = header_row
        self._all_guests = guests

        # Отрисовываем таблицу первый раз
        self._update_guest_table(guests)

        # Функция поиска
        def on_search(*args):
            query = self.search_var.get().strip().lower()
            if not query:
                self._update_guest_table(self._all_guests)
            else:
                filtered = [
                    g for g in self._all_guests
                    if query in str(g[0]).lower()
                       or query in g[1].lower()
                       or query in g[2].lower()
                       or query in (g[3] or "").lower()
                       or query in (g[4] or "").lower()
                ]
                self._update_guest_table(filtered)

        self.search_var.trace_add("write", on_search)

    def _update_guest_table(self, data):
        """
        Отрисовывает строки таблицы гостей в self.guest_table_frame,
        не трогая self.guest_header_row.
        """
        # Удаляем всё, кроме заголовка
        for widget in self.guest_table_frame.winfo_children():
            if widget != self.guest_header_row:
                widget.destroy()

        if not data:
            ctk.CTkLabel(
                self.guest_table_frame,
                text="😔  Ничего не найдено",
                text_color="#666666",
                font=("Arial", 15)
            ).pack(pady=40)
            return

        for i, g in enumerate(data):
            guest_id, last_name, first_name, patronymic, phone, is_complete = g
            bg = "#222233" if i % 2 == 0 else "#1e1e2e"

            row_frame = ctk.CTkFrame(self.guest_table_frame, fg_color=bg, corner_radius=6, height=42)
            row_frame.pack(fill="x", padx=5, pady=1)
            row_frame.pack_propagate(False)

            ctk.CTkLabel(row_frame, text=f"#{int(guest_id):05d}",
                         font=("Arial", 12), width=60,
                         anchor="w", text_color="#888888").pack(side="left", padx=(15, 0))

            values = [last_name, first_name, patronymic or "—", phone or "—"]
            col_widths = [140, 110, 140, 130]
            for val, w in zip(values, col_widths):
                ctk.CTkLabel(row_frame, text=val, font=("Arial", 13), text_color="white",
                             width=w, anchor="w").pack(side="left", padx=(15, 0))

            status_text = "✅ Полная" if is_complete else "⚠️ Не полная"
            status_color = "#2ecc71" if is_complete else "#f39c12"
            ctk.CTkLabel(row_frame, text=status_text,
                         font=("Arial", 12), width=100,
                         anchor="w", text_color=status_color).pack(side="left", padx=(15, 0))

            def on_enter(e, f=row_frame):
                f.configure(fg_color="#2d2d5a")

            def on_leave(e, f=row_frame, b=bg):
                f.configure(fg_color=b)

            row_frame.bind("<Enter>", on_enter)
            row_frame.bind("<Leave>", on_leave)
            for child in row_frame.winfo_children():
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)

    def show_booking_form(self):

        self.current_screen = "booking"

        self.clear_main_frame()
        self.main_frame.grid_propagate(False)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.main_frame, text="Регистрация гостя", font=("Arial", 20)).grid(row=0, column=0, pady=(20, 10))

        # --- Вкладки ---
        self.tab_view = ctk.CTkTabview(
            self.main_frame,
            fg_color="transparent",  # прозрачный фон
            segmented_button_fg_color="#2b2b2b",  # цвет полоски с кнопками вкладок
            segmented_button_selected_color="#1f538d",  # цвет активной вкладки
            segmented_button_unselected_color="#2b2b2b",  # цвет неактивной
            segmented_button_selected_hover_color="#1a4a7a",
        )

        self.tab_view.add("⚡  Быстрая регистрация")
        self.tab_view.add("📋  Полная регистрация")

        self._build_quick_tab()
        self._build_full_tab()

        # Сначала строим всё, потом показываем одним разом
        self.main_frame.update_idletasks()
        self.tab_view.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _build_quick_tab(self):
        """Быстрая вкладка — двухколоночная версия с перераспределением полей"""
        tab = self.tab_view.tab("⚡  Быстрая регистрация")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Добавляем скролл
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Главный контейнер с 2 колонками
        main_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)

        # ========== ЛЕВАЯ КОЛОНКА (ФИО + паспортные данные) ==========
        left_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        left_frame.grid_columnconfigure(0, weight=1)

        # --- ФИО ---
        self.entry_last_name = ctk.CTkEntry(left_frame, placeholder_text="Фамилия", width=325)
        self.entry_last_name.grid(row=0, column=0, pady=6, sticky="ew")

        self.entry_first_name = ctk.CTkEntry(left_frame, placeholder_text="Имя", width=325)
        self.entry_first_name.grid(row=1, column=0, pady=6, sticky="ew")

        self.entry_patronymic = ctk.CTkEntry(left_frame, placeholder_text="Отчество", width=325)
        self.entry_patronymic.grid(row=2, column=0, pady=6, sticky="ew")

        self.entry_phone = ctk.CTkEntry(left_frame, placeholder_text="Телефон", width=325)
        self.entry_phone.grid(row=3, column=0, pady=6, sticky="ew")

        # --- Дата рождения ---
        birth_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        birth_row.grid(row=4, column=0, pady=(6, 0), sticky="ew")
        birth_row.grid_columnconfigure(0, weight=0)

        ctk.CTkLabel(birth_row, text="Дата рождения:", font=("Arial", 12)).grid(
            row=0, column=0, padx=(0, 10), sticky="w")
        self.entry_birth_quick = ctk.CTkEntry(birth_row, placeholder_text="ДД.ММ.ГГГГ", width=130)
        self.entry_birth_quick.grid(row=0, column=1, sticky="w")
        self.entry_birth_quick.bind("<FocusOut>", lambda e: self._check_age_quick())
        # Кнопка календаря для даты рождения
        ctk.CTkButton(
            birth_row,
            text="📅",
            width=35,
            command=lambda: self.open_calendar(self.entry_birth_quick)
        ).grid(row=0, column=2, padx=(5, 5), sticky="w")

        # Предупреждение о возрасте
        self.lbl_age_warning = ctk.CTkLabel(
            left_frame, text="", font=("Arial", 11),
            text_color="#f39c12", wraplength=325, justify="left"
        )
        self.lbl_age_warning.grid(row=5, column=0, sticky="w")

        # Кнопка скана согласия родителей (скрыта по умолчанию)
        self.minor_consent_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.minor_consent_frame.grid(row=6, column=0, pady=(5, 0), sticky="ew")
        self.minor_consent_frame.grid_remove()

        self.minor_consent_label = ctk.CTkLabel(
            self.minor_consent_frame, text="Скан согласия не прикреплён",
            text_color="#888888", font=("Arial", 11)
        )
        self.minor_consent_label.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            self.minor_consent_frame,
            text="📎 Согласие родителей",
            width=165,
            command=self._attach_minor_consent
        ).pack(side="left")

        self.minor_consent_btn_remove = ctk.CTkButton(
            self.minor_consent_frame,
            text="✕",
            width=30,
            fg_color="#c0392b",
            hover_color="#a93226",
            command=self._remove_minor_consent
        )
        self.minor_consent_btn_remove.pack(side="left", padx=(5, 0))
        self.minor_consent_btn_remove.pack_forget()  # скрыта по умолчанию

        # --- Гражданство ---
        citizen_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        citizen_frame.grid(row=7, column=0, pady=10, sticky="ew")
        ctk.CTkLabel(citizen_frame, text="Гражданство:", font=("Arial", 13)).grid(row=0, column=0, padx=(0, 15))
        self.citizenship_quick_var = ctk.StringVar(value="РФ")
        ctk.CTkOptionMenu(
            citizen_frame,
            values=["РФ", "Иностранец"],
            variable=self.citizenship_quick_var,
            width=180,
            command=self._on_quick_citizenship_change
        ).grid(row=0, column=1)

        # --- Тип документа ---
        ctk.CTkLabel(left_frame, text="Тип документа:", font=("Arial", 13)).grid(row=8, column=0, pady=(10, 5),
                                                                                 sticky="w")
        self.doc_type_quick = ctk.CTkOptionMenu(
            left_frame,
            values=DOC_TYPES_RF,
            width=325,
            command=self._on_quick_doc_type_change
        )
        self.doc_type_quick.grid(row=9, column=0, pady=5, sticky="ew")

        # --- Паспортные данные (серия + номер в одну строку) ---
        self.quick_passport_label = ctk.CTkLabel(left_frame, text="Паспортные данные:", font=("Arial", 13, "bold"))
        self.quick_passport_label.grid(row=10, column=0, pady=(10, 5), sticky="w")

        self.quick_passport_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.quick_passport_frame.grid(row=11, column=0, pady=5, sticky="ew")

        self.quick_passport_series = ctk.CTkEntry(self.quick_passport_frame, placeholder_text="Серия", width=110)
        self.quick_passport_series.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.quick_passport_number = ctk.CTkEntry(self.quick_passport_frame, placeholder_text="Номер паспорта", width=200)
        self.quick_passport_number.grid(row=0, column=1, sticky="ew")

        # --- Миграционная карта (только для иностранцев, скрыта по умолчанию) ---
        self.migration_frame_quick = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.migration_frame_quick.grid(row=13, column=0, pady=8, sticky="ew")
        self.migration_frame_quick.grid_remove()

        ctk.CTkLabel(self.migration_frame_quick, text="Миграционная карта №:", font=("Arial", 12)).grid(row=0, column=0,
                                                                                                        padx=(0, 10),
                                                                                                        sticky="w")
        self.entry_migration_quick = ctk.CTkEntry(self.migration_frame_quick, width=180)
        self.entry_migration_quick.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(self.migration_frame_quick, text="Срок действия:", font=("Arial", 12)).grid(row=1, column=0,
                                                                                                 padx=(0, 10),
                                                                                                 pady=(10, 0),
                                                                                                 sticky="w")
        self.entry_migration_expiry = ctk.CTkEntry(self.migration_frame_quick, width=120, placeholder_text="ДД.ММ.ГГГГ")
        self.entry_migration_expiry.grid(row=1, column=1, pady=(15, 0), sticky="w")

        # --- Срок действия документа (для загранпаспорта, ВУ, временного удостоверения) ---
        self.doc_expiry_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.doc_expiry_frame.grid(row=12, column=0, pady=8, sticky="ew")
        self.doc_expiry_frame.grid_remove()

        self.doc_expiry_label = ctk.CTkLabel(
            self.doc_expiry_frame, text="",
            font=("Arial", 12), wraplength=160, anchor="w", justify="left"
        )
        self.doc_expiry_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.entry_doc_expiry = ctk.CTkEntry(self.doc_expiry_frame, width=120, placeholder_text="ДД.ММ.ГГГГ")
        self.entry_doc_expiry.grid(row=0, column=1, sticky="w")

        # --- Согласие на ПДн ---
        self.agree_var = tk.BooleanVar(value=False)
        self.agree_check = ctk.CTkCheckBox(
            left_frame,
            text="Я согласен(на) на обработку персональных данных",
            variable=self.agree_var,
            font=("Arial", 12),
            command=self._toggle_submit_button
        )
        self.agree_check.grid(row=14, column=0, pady=20, sticky="w")

        # Инициализируем поля под начальный тип документа
        self._on_quick_doc_type_change("Паспорт гражданина РФ")

        # ========== ПРАВАЯ КОЛОНКА (даты, время, номер, скидка) ==========
        right_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="n", padx=(10, 0))
        right_frame.grid_columnconfigure(0, weight=1)

        # --- ДАТЫ ---
        dates_label = ctk.CTkLabel(right_frame, text="Даты проживания:", font=("Arial", 13, "bold"))
        dates_label.grid(row=0, column=0, pady=(0, 5), sticky="w")

        dates_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        dates_frame.grid(row=1, column=0, pady=5, sticky="ew")

        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        # Заезд
        ctk.CTkLabel(dates_frame, text="Заезд:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.entry_checkin = ctk.CTkEntry(dates_frame, width=120)
        self.entry_checkin.insert(0, today.strftime("%d.%m.%Y"))
        self.entry_checkin.grid(row=1, column=0, padx=(0, 5))
        ctk.CTkButton(dates_frame, text="📅", width=35, command=lambda: self.open_calendar(self.entry_checkin)).grid(
            row=1, column=1, padx=(0, 25))

        # Выезд
        ctk.CTkLabel(dates_frame, text="Выезд:").grid(row=0, column=2, padx=(10, 5), sticky="w")
        self.entry_checkout = ctk.CTkEntry(dates_frame, width=120)
        self.entry_checkout.insert(0, tomorrow.strftime("%d.%m.%Y"))
        self.entry_checkout.grid(row=1, column=2, padx=(0, 5))
        ctk.CTkButton(dates_frame, text="📅", width=35, command=lambda: self.open_calendar(self.entry_checkout)).grid(
            row=1, column=3)

        # --- ВРЕМЯ ---
        time_label = ctk.CTkLabel(right_frame, text="Время заезда/выезда:", font=("Arial", 13, "bold"))
        time_label.grid(row=2, column=0, pady=(15, 5), sticky="w")

        time_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        time_frame.grid(row=3, column=0, pady=5, sticky="ew")

        ctk.CTkLabel(time_frame, text="Заезд:").grid(row=0, column=0, padx=(0, 10))
        self.checkin_time_var = ctk.StringVar(value="14:00")
        ctk.CTkOptionMenu(
            time_frame,
            values=self._get_time_values(),
            variable=self.checkin_time_var,
            width=100,
            command=self._update_extras
        ).grid(row=0, column=1, padx=(0, 25))

        ctk.CTkLabel(time_frame, text="Выезд:").grid(row=0, column=2, padx=(0, 10))
        self.checkout_time_var = ctk.StringVar(value="12:00")
        ctk.CTkOptionMenu(
            time_frame,
            values=self._get_time_values(),
            variable=self.checkout_time_var,
            width=100,
            command=self._update_extras
        ).grid(row=0, column=3)

        # --- НОМЕР ---
        room_label = ctk.CTkLabel(right_frame, text="Выберите номер:", font=("Arial", 13, "bold"))
        room_label.grid(row=4, column=0, pady=(15, 5), sticky="w")

        free_rooms_data = get_free_rooms()
        self._free_rooms_data = {str(r[0]): r for r in free_rooms_data}
        room_options = [f"{r[0]} - {r[1]} ({r[2]} руб/сут)" for r in free_rooms_data]
        if not room_options:
            room_options = ["Нет свободных номеров"]

        self.room_selection = ctk.CTkOptionMenu(right_frame, values=room_options, width=320)
        self.room_selection.grid(row=5, column=0, pady=5, sticky="ew")

        # --- СКИДКА ---
        discount_label = ctk.CTkLabel(right_frame, text="Скидка:", font=("Arial", 13, "bold"))
        discount_label.grid(row=6, column=0, pady=(15, 5), sticky="w")

        discount_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        discount_frame.grid(row=7, column=0, pady=5, sticky="ew")

        self.discount_var = ctk.StringVar(value="Без скидки")
        ctk.CTkOptionMenu(
            discount_frame,
            values=["Без скидки", "5%", "10%", "15%", "20%", "25%", "30%"],
            variable=self.discount_var,
            width=120,
            command=self._sync_discount_entry
        ).grid(row=0, column=0, padx=(0, 15))

        self.discount_entry = ctk.CTkEntry(discount_frame, width=80, placeholder_text="0-100")
        self.discount_entry.grid(row=0, column=1)

        # --- ДОПЛАТЫ (ранний заезд/поздний выезд) ---
        self.extras_frame = ctk.CTkFrame(right_frame, fg_color="#1e2d45", corner_radius=8)
        self.extras_frame.grid(row=8, column=0, pady=8, sticky="ew")
        self.extras_frame.grid_remove()

        self.lbl_extras = ctk.CTkLabel(self.extras_frame, text="", font=("Arial", 11), text_color="#f39c12")
        self.lbl_extras.pack(pady=6, padx=12)

        # --- ИТОГО ---
        self.lbl_total = ctk.CTkLabel(
            right_frame, text="", font=("Arial", 14), text_color="#2ecc71",
            height=40, wraplength=325, justify="left", anchor="w"
        )
        self.lbl_total.grid(row=9, column=0, pady=8, sticky="ew")

        # --- ОШИБКИ ---
        self.lbl_error = ctk.CTkLabel(
            right_frame, text="", font=("Arial", 12), text_color="#e74c3c",
            wraplength=325, justify="left", anchor="w"
        )
        self.lbl_error.grid(row=10, column=0, pady=5, sticky="ew")

        # --- КНОПКИ ---
        btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_frame.grid(row=11, column=0, pady=15)

        self.calc_button = ctk.CTkButton(btn_frame, text="Рассчитать стоимость", command=self.calculate_price)
        self.calc_button.grid(row=0, column=0, padx=10)

        self.submit_button = ctk.CTkButton(
            btn_frame,
            text="⚡  Заселить",
            width=150,
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=self.submit_guest,
            state="disabled"
        )
        self.submit_button.grid(row=0, column=1, padx=10)

        # --- Очистка зелёной надписи при фокусе на полях (убираем "висящий" success) ---
        def clear_success(event=None):
            self.lbl_total.configure(text="")

        focus_fields = [
            self.entry_last_name, self.entry_first_name, self.entry_patronymic,
            self.entry_phone, self.quick_passport_series, self.quick_passport_number,
            self.entry_checkin, self.entry_checkout, self.room_selection,
            self.discount_entry
        ]
        # Дополнительные поля (миграционная карта, срок действия) – если есть
        if hasattr(self, 'entry_migration_quick'):
            focus_fields.append(self.entry_migration_quick)
            focus_fields.append(self.entry_migration_expiry)
        if hasattr(self, 'entry_doc_expiry'):
            focus_fields.append(self.entry_doc_expiry)

        for field in focus_fields:
            try:
                field.bind("<FocusIn>", clear_success)
            except:
                pass

    def _get_time_values(self):
        """Возвращает список доступных значений времени"""
        return ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00",
                "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
                "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
                "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"]

    def _toggle_submit_button(self):
        """Включает/выключает кнопку 'Заселить' в зависимости от чекбокса согласия"""
        if self.agree_var.get():
            self.submit_button.configure(state="normal")
        else:
            self.submit_button.configure(state="disabled")

    def _reset_entry_placeholder(self, entry: ctk.CTkEntry, placeholder: str):
        """Очищает поле и восстанавливает placeholder как будто поле свежесозданное"""
        entry.delete(0, "end")
        entry.configure(placeholder_text=placeholder)
        # Принудительно вызываем внутренний метод CTk для отрисовки placeholder
        entry._activate_placeholder()
        entry.master.focus()

    def _check_age_quick(self):
        """Проверяет возраст гостя и показывает предупреждение"""
        birth_str = self.entry_birth_quick.get().strip()
        if not birth_str:
            self.lbl_age_warning.configure(text="")
            self.minor_consent_frame.grid_remove()
            return
        try:
            birth = datetime.datetime.strptime(birth_str, "%d.%m.%Y").date()
            today = datetime.date.today()
            age = (today - birth).days // 365

            is_foreign = self.citizenship_quick_var.get() == "Иностранец"

            if age < 0 or age > 120:
                self.lbl_age_warning.configure(text="⚠️ Проверьте дату рождения!")
                self.minor_consent_frame.grid_remove()
            elif age < 14:
                self.lbl_age_warning.configure(
                    text="🚫 Ребёнок до 14 лет — заселение только с родителем/опекуном!")
                self.minor_consent_frame.grid_remove()
                self.minor_consent_btn_remove.pack_forget()
                self.submit_button.configure(state="disabled")

            elif age < 18:
                if is_foreign:
                    self.lbl_age_warning.configure(
                        text="🚫 Несовершеннолетний иностранец — заселение без родителей невозможно! "
                             "Обратитесь к руководству.")
                    self.minor_consent_frame.grid_remove()
                    self.minor_consent_btn_remove.pack_forget()
                else:
                    self.lbl_age_warning.configure(
                        text="⚠️ Подросток 14-17 лет — необходимо нотариальное согласие родителей!")
                    self.minor_consent_frame.grid()
            else:
                self.lbl_age_warning.configure(text="")
                self.minor_consent_frame.grid_remove()
                self.minor_consent_btn_remove.pack_forget()  # ← и сюда
                self.submit_button.configure(
                    state="normal" if self.agree_var.get() else "disabled"
                )
        except ValueError:
            self.lbl_age_warning.configure(text="⚠️ Неверный формат даты! Используйте ДД.ММ.ГГГГ")
            self.minor_consent_frame.grid_remove()

    def _attach_minor_consent(self):
        self._attach_scan("minor_consent_path", self.minor_consent_label)
        if hasattr(self, 'minor_consent_path') and self.minor_consent_path:
            self.minor_consent_btn_remove.pack(side="left", padx=(5, 0))

    def _remove_minor_consent(self):
        if hasattr(self, 'minor_consent_path'):
            del self.minor_consent_path
        self.minor_consent_label.configure(
            text="Скан согласия не прикреплён", text_color="#888888")
        self.minor_consent_btn_remove.pack_forget()

    def _on_quick_doc_type_change(self, value):
        rules = self.document_rules.get(value, {})

        new_title = rules.get("block_title", "Реквизиты документа")
        if hasattr(self, 'quick_passport_label'):
            self.quick_passport_label.configure(text=new_title)


        # Серия
        if rules.get("show_series", True):
            self.quick_passport_series.grid()
            self._reset_entry_placeholder(
                self.quick_passport_series,
                rules.get("series_placeholder", "Серия")
            )
            self.quick_passport_frame.grid_columnconfigure(0, weight=1)
            self.quick_passport_frame.grid_columnconfigure(1, weight=2)
            self.quick_passport_number.grid(row=0, column=1, sticky="ew")
            self.quick_passport_number.configure(width=200)
        else:
            self.quick_passport_series.grid_remove()
            self.quick_passport_frame.grid_columnconfigure(0, weight=0)
            self.quick_passport_frame.grid_columnconfigure(1, weight=1)
            self.quick_passport_number.grid(row=0, column=1, sticky="ew")
            self.quick_passport_number.configure(width=0)

        # Номер
        self._reset_entry_placeholder(
            self.quick_passport_number,
            rules.get("number_placeholder", "Номер паспорта")
        )

        # Срок действия
        if rules.get("show_expiry", False):
            self.doc_expiry_frame.grid()
            self.doc_expiry_label.configure(text=rules.get("expiry_label", "Срок действия документа:"))
        else:
            self.doc_expiry_frame.grid_remove()
            if hasattr(self, 'entry_doc_expiry'):
                self._reset_entry_placeholder(self.entry_doc_expiry, "ДД.ММ.ГГГГ")


    def  _on_quick_citizenship_change(self, value):
        """Показывает/скрывает миграционную карту для иностранцев"""
        if value == "Иностранец":
            self.quick_passport_series.grid_remove()
            self.migration_frame_quick.grid()  # показать поле миграционной карты
            self._reset_entry_placeholder(self.entry_migration_quick, "Номер карты")
            self._reset_entry_placeholder(self.entry_migration_expiry, "ДД.ММ.ГГГГ")

            # Подсказка для администратора
            self.lbl_error.configure(text="⚠️ Для иностранца обязательна миграционная карта!", text_color="#f39c12")

            # Убираем вес первой колонки, отдаём всё второй
            self.quick_passport_frame.grid_columnconfigure(0, weight=0)
            self.quick_passport_frame.grid_columnconfigure(1, weight=1)

            # Разрешаем полю номера растягиваться
            self.quick_passport_number.configure(width=0)
            self.quick_passport_number._activate_placeholder()  # обновить плейсхолдер

            self.doc_type_quick.configure(values=DOC_TYPES_FOREIGN)
            self.doc_type_quick.set("Загранпаспорт")
            self._on_quick_doc_type_change("Загранпаспорт")
            self._check_age_quick()

        else:
            self.quick_passport_series.grid()
            self.migration_frame_quick.grid_remove()
            self.lbl_error.configure(text="")

            # Восстанавливаем веса
            self.quick_passport_frame.grid_columnconfigure(0, weight=1)
            self.quick_passport_frame.grid_columnconfigure(1, weight=2)

            # Возвращаем фиксированную ширину
            self.quick_passport_number.configure(width=200)

            # Возвращаем все типы документов
            self.doc_type_quick.configure(values=DOC_TYPES_RF)
            self.doc_type_quick.set("Паспорт гражданина РФ")
            self._on_quick_doc_type_change("Паспорт гражданина РФ")
            self._check_age_quick()

    def _build_full_tab(self):
        """Полная регистрация — двухколоночная версия с вертикальным скроллом"""
        tab = self.tab_view.tab("📋  Полная регистрация")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Скроллируемый контейнер для всей вкладки
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Главный контейнер с 2 колонками (внутри скролла)
        main_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)

        # ========== ЛЕВАЯ КОЛОНКА (компактная) ==========
        left_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        left_frame.grid_columnconfigure(0, weight=1)


        # Поиск гостя
        ctk.CTkLabel(left_frame, text="Поиск гостя", font=("Arial", 14, "bold")).grid(
            row=0, column=0, pady=(0, 10), sticky="w")
        search_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, pady=5, sticky="ew")
        self.full_search_entry = ctk.CTkEntry(search_frame, placeholder_text="Введите ID гостя...", width=200)
        self.full_search_entry.grid(row=0, column=0, padx=(0, 10))
        ctk.CTkButton(search_frame, text="🔍 Найти", width=100, command=self._find_guest_for_full).grid(row=0, column=1)
        self.lbl_guest_found_full = ctk.CTkLabel(left_frame, text="", font=("Arial", 12), text_color="#2ecc71")
        self.lbl_guest_found_full.grid(row=2, column=0, pady=(5, 15), sticky="w")

        # Гражданство
        citizen_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        citizen_frame.grid(row=3, column=0, pady=8, sticky="ew")
        ctk.CTkLabel(citizen_frame, text="Гражданство:", font=("Arial", 13)).grid(row=0, column=0, padx=(0, 15))
        self.full_citizenship_var = ctk.StringVar(value="РФ")
        ctk.CTkOptionMenu(
            citizen_frame, values=["РФ", "Иностранец"], variable=self.full_citizenship_var, width=180,
            command=self._on_full_citizenship_change
        ).grid(row=0, column=1)

        # Тип документа
        ctk.CTkLabel(left_frame, text="Тип документа:", font=("Arial", 13)).grid(
            row=4, column=0, pady=(10, 5), sticky="w")
        self.full_doc_type = ctk.CTkOptionMenu(
            left_frame,
            values=DOC_TYPES_RF,
            width=325,
            command=self._on_full_doc_type_change
        )
        self.full_doc_type.grid(row=5, column=0, pady=5, sticky="ew")
        self.full_doc_type.set("Паспорт гражданина РФ")

        # Паспортные данные
        self.full_passport_label = ctk.CTkLabel(left_frame, text="Паспортные данные *", font=("Arial", 13, "bold"))
        self.full_passport_label.grid(row=6, column=0, pady=(10, 5), sticky="w")

        self.full_passport_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.full_passport_frame.grid(row=7, column=0, pady=5, sticky="ew")

        self.full_passport_series = ctk.CTkEntry(self.full_passport_frame, placeholder_text="Серия", width=110)
        self.full_passport_series.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.full_passport_number = ctk.CTkEntry(self.full_passport_frame, placeholder_text="Номер паспорта", width=200)
        (self.full_passport_number.grid(row=0, column=1, sticky="ew"))

        # Кем выдан и т.д.
        self.full_issued_by_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.full_issued_by_frame.grid(row=8, column=0, pady=5, sticky="ew")
        self.full_issued_by_frame.grid_remove()
        ctk.CTkLabel(self.full_issued_by_frame, text="Кем выдан:", font=("Arial", 12)).grid(row=0, column=0,
                                                                                            pady=(10, 2), sticky="w")
        self.full_issued_by = ctk.CTkEntry(self.full_issued_by_frame, placeholder_text="Полное наименование органа",
                                           width=325)
        self.full_issued_by.grid(row=1, column=0, pady=(0, 5), sticky="ew")
        date_code_frame = ctk.CTkFrame(self.full_issued_by_frame, fg_color="transparent")
        date_code_frame.grid(row=2, column=0, pady=5, sticky="ew")
        date_code_frame.grid_columnconfigure(0, weight=1)
        date_code_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(date_code_frame, text="Дата выдачи:", font=("Arial", 12)).grid(row=0, column=0, sticky="w")
        self.full_issue_date = ctk.CTkEntry(date_code_frame, placeholder_text="ДД.ММ.ГГГГ", width=130)
        self.full_issue_date.grid(row=1, column=0, sticky="w", padx=(0, 20))
        ctk.CTkLabel(date_code_frame, text="Код подразделения:", font=("Arial", 12)).grid(row=0, column=1, sticky="w")
        self.full_department_code = ctk.CTkEntry(date_code_frame, placeholder_text="XXX-XXX", width=110)
        self.full_department_code.grid(row=1, column=1, sticky="w")

        # Срок действия документа
        self.full_expiry_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.full_expiry_frame.grid(row=9, column=0, pady=8, sticky="ew")
        self.full_expiry_frame.grid_remove()
        self.full_expiry_label = ctk.CTkLabel(
            self.full_expiry_frame, text="Срок действия:",
            font=("Arial", 12), wraplength=160, anchor="w", justify="left"
        )
        self.full_expiry_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.full_doc_expiry = ctk.CTkEntry(self.full_expiry_frame, width=120, placeholder_text="ДД.ММ.ГГГГ")
        self.full_doc_expiry.grid(row=0, column=1, sticky="w")

        # Миграционная карта
        self.full_migration_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.full_migration_frame.grid(row=10, column=0, pady=8, sticky="ew")
        self.full_migration_frame.grid_remove()
        ctk.CTkLabel(self.full_migration_frame, text="Миграционная карта №:", font=("Arial", 12)).grid(row=0, column=0,
                                                                                                       padx=(0, 10),
                                                                                                       sticky="w")
        self.full_migration_card = ctk.CTkEntry(self.full_migration_frame, width=180)
        self.full_migration_card.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(self.full_migration_frame, text="Срок действия:", font=("Arial", 12)).grid(row=1, column=0,
                                                                                                padx=(0, 10),
                                                                                                pady=(15, 0), sticky="w")
        self.full_migration_expiry = ctk.CTkEntry(self.full_migration_frame, width=120, placeholder_text="ДД.ММ.ГГГГ")
        self.full_migration_expiry.grid(row=1, column=1, pady=(10, 0), sticky="w")

        # Адрес регистрации
        ctk.CTkLabel(left_frame, text="Адрес регистрации", font=("Arial", 13, "bold")).grid(
            row=11, column=0, pady=(15, 5), sticky="w")
        self.full_registration_address = ctk.CTkEntry(left_frame, placeholder_text="Полный адрес по месту регистрации",
                                                      width=300)
        self.full_registration_address.grid(row=12, column=0, pady=4, sticky="ew")
        ctk.CTkLabel(left_frame, text="Например: г. Москва, ул. Тверская, д. 1, кв. 1",
                     font=("Arial", 10), text_color="#888888").grid(row=13, column=0, sticky="w")

        # Дополнительные данные
        ctk.CTkLabel(left_frame, text="Дополнительные данные", font=("Arial", 13, "bold")).grid(
            row=14, column=0, pady=(15, 5), sticky="w")
        birth_lang_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        birth_lang_row.grid(row=15, column=0, pady=5, sticky="ew")
        # birth_lang_row.grid_columnconfigure(0, weight=1)
        # birth_lang_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(birth_lang_row, text="Дата рождения:", font=("Arial", 12)).grid(row=0, column=0, sticky="w")
        birth_lang_row.grid_columnconfigure(0, weight=1)  # Дата
        birth_lang_row.grid_columnconfigure(1, weight=0)  # Кнопка календаря
        birth_lang_row.grid_columnconfigure(2, weight=1)  # Язык
        self.full_birth_date = ctk.CTkEntry(birth_lang_row, placeholder_text="ДД.ММ.ГГГГ", width=130)
        self.full_birth_date.grid(row=1, column=0, sticky="w")
        # Кнопка календаря для даты рождения
        ctk.CTkButton(
            birth_lang_row,
            text="📅",
            width=35,
            command=lambda: self.open_calendar(self.full_birth_date),
        ).grid(row=1, column=1, padx=(5, 25), sticky="w")
        ctk.CTkLabel(birth_lang_row, text="Язык:", font=("Arial", 12)).grid(row=0, column=2, sticky="w")
        self.full_language = ctk.CTkOptionMenu(birth_lang_row, width=130,
                                               values=["RU — Русский", "EN — English", "DE — Deutsch", "FR — Français",
                                                       "ZH — 中文", "AR — العربية", "ES — Español", "IT — Italiano",
                                                       "TR — Türkçe", "KO — 한국어", "JA — 日本語", "HI — Hindi"])
        self.full_language.grid(row=1, column=2, sticky="w")
        self.full_language.set("RU — Русский")

        # Скан паспорта
        scan_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        scan_row.grid(row=16, column=0, pady=8, sticky="ew")
        scan_row.grid_columnconfigure(0, weight=0, minsize=150)  # фикс. ширина под лейбл
        scan_row.grid_columnconfigure(1, weight=0, minsize=130)  # фикс. ширина под кнопку "Прикрепить"
        scan_row.grid_columnconfigure(2, weight=0, minsize=90)  # фикс. ширина под кнопку "Удалить"


        # Лейбл статуса скана
        self.full_scan_label = ctk.CTkLabel(
            scan_row,
            text="Скан не прикреплён",
            text_color="#888888",
            width=110,
            anchor="w"
        )
        self.full_scan_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        #Кнопка "Прикрепить"
        ctk.CTkButton(
            scan_row,
            text="📎 Прикрепить",
            width=120,
            command=lambda: self._attach_scan("full_scan_path", self.full_scan_label, self.full_scan_delete_btn)
        ).grid(row=0, column=1, padx=(0, 5), sticky="w")

        # Кнопка "Удалить" (изначально скрыта)
        self.full_scan_delete_btn = ctk.CTkButton(
            scan_row,
            text="✕ Удалить",
            width=80,
            fg_color="#c0392b",
            hover_color="#a93226",
            command=lambda: self._remove_scan("full_scan_path", self.full_scan_label, self.full_scan_delete_btn)
        )
        self.full_scan_delete_btn.grid(row=0, column=2, sticky="w")
        self.full_scan_delete_btn.grid_remove()  # Скрыта по умолчанию

        # ========== ПРАВАЯ КОЛОНКА ==========
        right_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="n", padx=(10, 0))
        right_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_frame, text="Состав номера", font=("Arial", 14, "bold")).grid(
            row=0, column=0, sticky="w")

        # Состав и Взрослых в одной строке
        row1 = ctk.CTkFrame(right_frame, fg_color="transparent")
        row1.grid(row=1, column=0, pady=5, sticky="ew")
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row1, text="Состав:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.full_composition = ctk.CTkOptionMenu(
            row1, values=["Один", "Пара", "Семья с детьми", "Группа"], width=150,
            command=self._on_full_composition_change
        )
        self.full_composition.grid(row=1, column=0, sticky="w")
        self.full_composition.set("Один")

        ctk.CTkLabel(row1, text="Взрослых:", font=("Arial", 12)).grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.full_adults = ctk.CTkEntry(row1, width=60)
        self.full_adults.insert(0, "1")
        self.full_adults.grid(row=1, column=1, sticky="w", padx=(10, 0))

        # Дети
        self.full_children_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.full_children_frame.grid(row=2, column=0, pady=5, sticky="ew")
        self.full_children_frame.grid_remove()
        ctk.CTkLabel(self.full_children_frame, text="Детей:", font=("Arial", 12)).grid(row=0, column=0, sticky="w")
        self.full_children = ctk.CTkEntry(self.full_children_frame, width=60)
        self.full_children.insert(0, "0")
        self.full_children.grid(row=1, column=0, sticky="w")

        ctk.CTkLabel(right_frame, text="Пожелания и сервис", font=("Arial", 14, "bold")).grid(
            row=3, column=0, pady=(20, 5), sticky="w")

        # Приветственный подарок
        ctk.CTkLabel(right_frame, text="Приветственный подарок:", font=("Arial", 12)).grid(row=4, column=0,
                                                                                           pady=(5, 5), sticky="w")
        self.full_welcome_gift = ctk.CTkOptionMenu(right_frame, width=220,
                                                   values=["Ничего", "🍾 Шампанское", "🍓 Фрукты", "🎂 Торт",
                                                           "🍾 Шампанское + фрукты"])
        self.full_welcome_gift.grid(row=5, column=0, pady=5, sticky="w")
        self.full_welcome_gift.set("Ничего")

        # Особые пожелания
        ctk.CTkLabel(right_frame, text="Особые пожелания:", font=("Arial", 12)).grid(row=6, column=0, pady=(15, 5),
                                                                                     sticky="w")
        self.full_requests = ctk.CTkTextbox(right_frame, width=325, height=60, corner_radius=6)
        self.full_requests.grid(row=7, column=0, pady=5, sticky="ew")

        # Жалобы
        ctk.CTkLabel(right_frame, text="Жалобы / Замечания:", font=("Arial", 12)).grid(row=8, column=0, pady=(15, 5),
                                                                                       sticky="w")
        self.full_complaints = ctk.CTkTextbox(right_frame, width=325, height=60, corner_radius=6)
        self.full_complaints.grid(row=9, column=0, pady=5, sticky="ew")

        self.full_error_label = ctk.CTkLabel(right_frame, text="", font=("Arial", 12), text_color="#e74c3c")
        self.full_error_label.grid(row=11, column=0, pady=5)
        self.full_success_label = ctk.CTkLabel(right_frame, text="", font=("Arial", 12), text_color="#2ecc71")
        self.full_success_label.grid(row=12, column=0, pady=5)

        # Кнопка сохранения
        btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_frame.grid(row=13, column=0, pady=20)
        self.full_save_btn = ctk.CTkButton(btn_frame, text="💾 Сохранить полную карточку",
                                           width=220, fg_color="#1f538d", hover_color="#1a4a7a",
                                           command=self._save_full_profile)
        self.full_save_btn.grid(row=0, column=0)

        self._on_full_doc_type_change(self.full_doc_type.get())  # инициализация полей документа
        self._on_full_citizenship_change(self.full_citizenship_var.get())  # инициализация гражданства (если нужно)


    def _on_composition_change(self, value):
        """Показывает поле детей для семьи"""
        if value == "Семья с детьми":
            self.children_frame.grid()
        else:
            self.children_frame.grid_remove()

    def _attach_scan(self, path_attr_name, label_widget, delete_btn_widget=None):
        """ Метод для прикрепления скана документа """
        from tkinter import filedialog
        import shutil
        import os

        filepath = filedialog.askopenfilename(
            title="Выберите скан паспорта",
            filetypes=[("Изображения и PDF", "*.pdf *.jpg *.jpeg *.png")]
        )
        if not filepath:
            return

        os.makedirs("scans", exist_ok=True)
        filename = os.path.basename(filepath)
        dest = os.path.join("scans", filename)
        shutil.copy2(filepath, dest)

        # Сохраняем путь в указанном атрибуте
        setattr(self, path_attr_name, dest)

        MAX_LEN = 12
        if len(filename) <= MAX_LEN:
            display_name = filename
        else:
            name, ext = os.path.splitext(filename)
            display_name = name[:8] + "…" + ext

        # Обновляем метку
        label_widget.configure(text=display_name, text_color="#2ecc71", width=110)

        if delete_btn_widget:
            delete_btn_widget.grid()

    def _remove_scan(self, path_attr_name, label_widget, delete_btn_widget):
        """Удаляет прикреплённый скан"""
        import os

        filepath = getattr(self, path_attr_name, None)
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

        if hasattr(self, path_attr_name):
            delattr(self, path_attr_name)

        label_widget.configure(text="Скан не прикреплён", text_color="#888888")
        delete_btn_widget.grid_remove()

    def _on_full_citizenship_change(self, value):
        """Показывает/скрывает миграционную карту и адаптирует поля документа для иностранца"""

        if value == "Иностранец":
            # --- Скрыть поле серии ---
            self.full_passport_series.grid_remove()

            # Показать блок миграционной карты
            self.full_migration_frame.grid()
            self._reset_entry_placeholder(self.full_migration_card, "Номер карты")
            self._reset_entry_placeholder(self.full_migration_expiry, "ДД.ММ.ГГГГ")
            # Подсказка администратору
            self.full_error_label.configure(text="⚠️ Для иностранца обязательна миграционная карта!",
                                            text_color="#f39c12")

            # --- Изменяем веса колонок, чтобы поле номера растянулось на всю ширину ---
            self.full_passport_frame.grid_columnconfigure(0, weight=0)  # колонка серии не растягивается
            self.full_passport_frame.grid_columnconfigure(1, weight=1)  # колонка номера получает всё место
            # Убираем фиксированную ширину, разрешаем растяжение
            self.full_passport_number.configure(width=0)
            # Принудительно обновляем плейсхолдер (чтобы он не пропал)
            self.full_passport_number._activate_placeholder()

            # --- Ограничиваем выбор типов документов только загранпаспортом ---
            self.full_doc_type.configure(values=DOC_TYPES_FOREIGN)
            self.full_doc_type.set("Загранпаспорт")
            self._on_full_doc_type_change("Загранпаспорт")

        else:  # Гражданин РФ
            # --- Показать поле серии ---
            self.full_passport_series.grid()
            # Скрыть блок миграционной карты
            self.full_migration_frame.grid_remove()
            self.full_error_label.configure(text="")

            # --- Восстанавливаем исходные веса колонок ---
            self.full_passport_frame.grid_columnconfigure(0, weight=1)
            self.full_passport_frame.grid_columnconfigure(1, weight=2)
            # Возвращаем фиксированную ширину полю номера
            self.full_passport_number.configure(width=200)
            self.full_passport_number._activate_placeholder()

            # --- Возвращаем полный список типов документов ---
            self.full_doc_type.configure(values=DOC_TYPES_RF)
            self.full_doc_type.set("Паспорт гражданина РФ")
            self._on_full_doc_type_change("Паспорт гражданина РФ")

    def _on_full_doc_type_change(self, value):
        """Адаптирует поля паспортных данных под выбранный тип документа"""
        rules = self.document_rules.get(value, {})

        # Обновление заголовка блока документа
        new_title = rules.get("block_title", "Реквизиты документа")
        if hasattr(self, 'full_passport_label'):
            self.full_passport_label.configure(text=new_title)

        # Серия
        if rules.get("show_series", True):
            self.full_passport_series.grid()
            self._reset_entry_placeholder(
                self.full_passport_series,
                rules.get("series_placeholder", "Серия")
            )
            self.full_passport_frame.grid_columnconfigure(0, weight=1)
            self.full_passport_frame.grid_columnconfigure(1, weight=2)
            self.full_passport_number.grid(row=0, column=1, sticky="ew")
            self.full_passport_number.configure(width=200)

        else:
            self.full_passport_series.grid_remove()
            self.full_passport_frame.grid_columnconfigure(0, weight=0)
            self.full_passport_frame.grid_columnconfigure(1, weight=1)
            self.full_passport_number.grid(row=0, column=1, sticky="ew")
            self.full_passport_number.configure(width=0)

        # Номер
        self._reset_entry_placeholder(
            self.full_passport_number,
            rules.get("number_placeholder", "Номер паспорта")
        )

        # Блок "Кем выдан/дата/код" — только для паспорта РФ/СССР
        if value in ["Паспорт гражданина РФ", "Паспорт гражданина СССР"]:
            self.full_issued_by_frame.grid()
            self._reset_entry_placeholder(self.full_issued_by, "Полное наименование органа")
            self._reset_entry_placeholder(self.full_issue_date, "ДД.ММ.ГГГГ")
            self._reset_entry_placeholder(self.full_department_code, "XXX-XXX")
        else:
            self.full_issued_by_frame.grid_remove()
            self.full_issued_by.delete(0, "end")
            self.full_issue_date.delete(0, "end")
            self.full_department_code.delete(0, "end")

        # Срок действия документа
        if rules.get("show_expiry", False):
            self.full_expiry_frame.grid()
            self.full_expiry_label.configure(text=rules.get("expiry_label", "Срок действия:"))
            self._reset_entry_placeholder(self.full_doc_expiry, "ДД.ММ.ГГГГ")
        else:
            self.full_expiry_frame.grid_remove()

    def _on_full_composition_change(self, value):
        """Показывает/скрывает поле для детей при выборе 'Семья с детьми'"""
        if value == "Семья с детьми":
            self.full_children_frame.grid()
        else:
            self.full_children_frame.grid_remove()

        # Автозаполнение числа взрослых
        if value == "Один":
            self.full_adults.delete(0, "end")
            self.full_adults.insert(0, "1")
        elif value == "Пара":
            self.full_adults.delete(0, "end")
            self.full_adults.insert(0, "2")
        elif value == "Семья с детьми":
            self.full_adults.delete(0, "end")
            self.full_adults.insert(0, "2")
        elif value == "Группа":
            self.full_adults.delete(0, "end")
            self.full_adults.insert(0, "3")


    def _find_guest_for_full(self):
        """Поиск гостя по ID для полной регистрации"""
        guest_id_str = self.full_search_entry.get().strip()
        if not guest_id_str:
            self.lbl_guest_found_full.configure(text="Введите ID гостя!", text_color="#e74c3c")
            return
        try:
            guest_id = int(guest_id_str)
            guest = get_guest_by_id(guest_id)
            if guest:
                self.current_full_guest_id = guest_id
                self.lbl_guest_found_full.configure(
                    text=f"✓ Гость: {guest[1]} {guest[2]} {guest[3] or ''}".strip(),
                    text_color="#2ecc71"
                )
                # Загружаем данные гостя в форму (опционально, можно потом)
                self._load_guest_data_to_full_form(guest)
            else:
                self.lbl_guest_found_full.configure(text=f"Гость #{guest_id} не найден", text_color="#e74c3c")
        except ValueError:
            self.lbl_guest_found_full.configure(text="ID должен быть числом!", text_color="#e74c3c")

    def _load_guest_data_to_full_form(self, guest):
        """Заполняет форму полной регистрации данными найденного гостя."""
        try:
            # Гражданство
            citizenship = guest["citizenship"] or "РФ"
            self.full_citizenship_var.set("Иностранец" if citizenship not in ("РФ", "РФ ") else "РФ")
            self._on_full_citizenship_change(self.full_citizenship_var.get())

            # Тип документа
            doc_type = guest["doc_type"] or "Паспорт гражданина РФ"
            if doc_type in DOC_TYPES_RF:
                self.full_doc_type.set(doc_type)
                self._on_full_doc_type_change(doc_type)

            # Серия и номер
            if guest["doc_series"]:
                self.full_passport_series.delete(0, "end")
                self.full_passport_series.insert(0, guest["doc_series"])
            if guest["doc_number"]:
                self.full_passport_number.delete(0, "end")
                self.full_passport_number.insert(0, guest["doc_number"])

            # Кем выдан / дата / код
            if guest["doc_issued_by"] and self.full_issued_by_frame.winfo_ismapped():
                self.full_issued_by.delete(0, "end")
                self.full_issued_by.insert(0, guest["doc_issued_by"])
            if guest["doc_issue_date"] and self.full_issued_by_frame.winfo_ismapped():
                self.full_issue_date.delete(0, "end")
                self.full_issue_date.insert(0, guest["doc_issue_date"])
            if guest["doc_department_code"] and self.full_issued_by_frame.winfo_ismapped():
                self.full_department_code.delete(0, "end")
                self.full_department_code.insert(0, guest["doc_department_code"])

            # Срок действия документа
            if guest["doc_expiry_date"] and self.full_expiry_frame.winfo_ismapped():
                self.full_doc_expiry.delete(0, "end")
                self.full_doc_expiry.insert(0, guest["doc_expiry_date"])

            # Дата рождения
            if guest["birth_date"]:
                self.full_birth_date.delete(0, "end")
                self.full_birth_date.insert(0, guest["birth_date"])

            # Адрес регистрации
            if guest["registration_address"]:
                self.full_registration_address.delete(0, "end")
                self.full_registration_address.insert(0, guest["registration_address"])

            # Язык
            if guest["language"]:
                self.full_language.set(guest["language"])

            # Миграционная карта (для иностранцев)
            if citizenship == "Иностранец" and self.full_migration_frame.winfo_ismapped():
                if guest["migration_card_number"]:
                    self.full_migration_card.delete(0, "end")
                    self.full_migration_card.insert(0, guest["migration_card_number"])
                if guest["migration_card_expiry"]:
                    self.full_migration_expiry.delete(0, "end")
                    self.full_migration_expiry.insert(0, guest["migration_card_expiry"])

        except Exception:
            pass  # если поле отсутствует — просто не заполняем

    def _save_full_profile(self):
        if not hasattr(self, 'current_full_guest_id'):
            self.full_error_label.configure(text="Сначала найдите гостя по ID!")
            return
        guest_id = self.current_full_guest_id

        # берем дату из поля, но если она пустая —
        # загружаем существующую из БД, чтобы не удалить
        birth_date_from_form = self.full_birth_date.get().strip()

        if birth_date_from_form:
            birth_date_to_save = birth_date_from_form
        else:
            # Если поле пустое — получаем существующую дату из БД
            existing_guest = get_guest_by_id(guest_id)
            birth_date_to_save = existing_guest["birth_date"] if existing_guest else None

        data = {
            'doc_type': self.full_doc_type.get(),
            'doc_series': self.full_passport_series.get().strip() or None,
            'doc_number': self.full_passport_number.get().strip() or None,
            'doc_issued_by': self.full_issued_by.get().strip() if self.full_issued_by.winfo_ismapped() else None,
            'doc_issue_date': self.full_issue_date.get().strip() if self.full_issue_date.winfo_ismapped() else None,
            'doc_department_code': self.full_department_code.get().strip() if self.full_department_code.winfo_ismapped() else None,
            'doc_expiry_date': self.full_doc_expiry.get().strip() if self.full_expiry_frame.winfo_ismapped() else None,
            'registration_address': self.full_registration_address.get().strip() or None,
            'birth_date': birth_date_to_save,
            'language': self.full_language.get(),
            'migration_card_number': self.full_migration_card.get().strip() if self.full_migration_frame.winfo_ismapped() else None,
            'migration_card_expiry': self.full_migration_expiry.get().strip() if self.full_migration_frame.winfo_ismapped() else None,
            'passport_scan': getattr(self, 'full_scan_path', None),
            'citizenship': self.full_citizenship_var.get(),
        }

        # Проверка срока действия документа (если он задан)
        doc_expiry_str = data.get('doc_expiry_date')
        if doc_expiry_str:
            try:
                expiry_date = datetime.datetime.strptime(doc_expiry_str, "%d.%m.%Y").date()
                if expiry_date < datetime.date.today():
                    self.full_error_label.configure(text="Срок действия документа истёк! Исправьте дату.")
                    return
            except ValueError:
                self.full_error_label.configure(text="Неверный формат даты срока действия! Используйте ДД.ММ.ГГГГ")
                return

        # Проверка срока миграционной карты
        migr_expiry_str = data.get('migration_card_expiry')
        if migr_expiry_str:
            try:
                migr_date = datetime.datetime.strptime(migr_expiry_str, "%d.%m.%Y").date()
                if migr_date < datetime.date.today():
                    self.full_error_label.configure(text="Срок миграционной карты истёк!")
                    return
            except ValueError:
                self.full_error_label.configure(text="Неверный формат даты миграционной карты! Используйте ДД.ММ.ГГГГ")
                return

        success = update_guest_full_profile(guest_id, data)

        if success:
            # Сохраняем GR данные
            gr_data = {
                'composition': self.full_composition.get(),
                'adults': int(self.full_adults.get() or 1),
                'children': int(self.full_children.get() or 0) if self.full_children_frame.winfo_ismapped() else 0,
                'welcome_gift': self.full_welcome_gift.get(),
                'special_requests': self.full_requests.get("1.0", "end").strip(),
                'complaints': self.full_complaints.get("1.0", "end").strip(),
            }
            update_booking_gr_data(guest_id, gr_data)

            self.full_error_label.configure(text="")
            self.full_success_label.configure(text=f"✓ Карточка гостя #{guest_id:05d} сохранена!")
        else:
            self.full_error_label.configure(text="Ошибка сохранения!")

    def calculate_price(self):
        '''Считает и показывает стоимость не сохраняя, с учетом скидок'''
        self.lbl_total.configure(text="")
        result = self._parse_form()
        if result is None:
            return

        check_in, check_out, room_data = result
        discount = self._get_discount()
        if discount is None:
            return

        nights = (check_out - check_in).days
        base = nights * room_data[2]
        total = int(base * (1 - discount / 100))

        extras_total = self._early_checkin_price + self._late_checkout_price
        total += extras_total

        msg = f"Итого: {nights} ночей x {room_data[2]} руб"
        if discount > 0:
            msg += f" - скидка {discount}%"
        if extras_total > 0:
            msg += f" + доп. услуги {extras_total} руб"
        msg += f" = {total} руб"

        self.lbl_total.configure(text=msg)
        self.lbl_error.configure(text="")

    def _get_discount(self):
        # Сначала смотрим ручной ввод
        manual = self.discount_entry.get().strip().replace("%", "")
        if manual:
            try:
                val = int(manual)
                if 0 <= val <= 100:
                    return val
                else:
                    self.lbl_error.configure(text="Скидка должна быть от 0 до 100%!")
                    return None
            except ValueError:
                self.lbl_error.configure(text="Скидка должна быть числом!")
                return None

        # Если ручной ввод пустой — берём из меню
        val = self.discount_var.get()
        if val == "Без скидки":
            return 0
        return int(val.replace("%", ""))

    def _sync_discount_entry(self, value):
        self.discount_entry.delete(0, "end")
        if value != "Без скидки":
            self.discount_entry.insert(0, value.replace("%", ""))

    def _update_extras(self, value=None):
        """Показывает доплату за ранний заезд или поздний выезд (тарифы берутся из БД)"""
        checkin  = self.checkin_time_var.get()
        checkout = self.checkout_time_var.get()
        extras   = []

        # Ранний заезд — до 14:00
        early_key = f"early_checkin_{checkin[:2]}"
        early_price = int(get_setting(early_key, "0") or "0")
        if early_price > 0:
            extras.append(f"⚡ Ранний заезд {checkin} — +{early_price} руб")
            self._early_checkin_price = early_price
        else:
            self._early_checkin_price = 0

        # Поздний выезд — после 12:00
        late_key = f"late_checkout_{checkout[:2]}"
        late_price = int(get_setting(late_key, "0") or "0")
        if late_price > 0:
            extras.append(f"🕐 Поздний выезд {checkout} — +{late_price} руб")
            self._late_checkout_price = late_price
        else:
            self._late_checkout_price = 0

        if extras:
            self.lbl_extras.configure(text="\n".join(extras))
            self.extras_frame.grid()
        else:
            self.extras_frame.grid_remove()

    def _parse_form(self):
        """Валидирует форму и возвращает (check_in, check_out, room_data) или None"""
        ln = self.entry_last_name.get().strip()
        fn = self.entry_first_name.get().strip()
        ph = self.entry_phone.get().strip()

        if not ln or not fn or not ph:
            self.lbl_error.configure(text="Заполните Фамилию, Имя и Телефон!")
            return None

        # Проверка возраста
        birth_str = self.entry_birth_quick.get().strip()
        if birth_str:
            try:
                birth = datetime.datetime.strptime(birth_str, "%d.%m.%Y").date()
                age = (datetime.date.today() - birth).days // 365
                is_foreign = self.citizenship_quick_var.get() == "Иностранец"
                if age < 14:
                    self.lbl_error.configure(
                        text="Ребёнок до 14 лет может заселяться только с родителем!")
                    return None
                elif age < 18:
                    if is_foreign:
                        self.lbl_age_warning.configure(
                            text="🚫 Несовершеннолетний иностранец — заселение без родителей невозможно! "
                                 "Обратитесь к руководству.")
                        self.minor_consent_frame.grid_remove()
                        self.submit_button.configure(state="disabled")  # ← блокируем
                    else:
                        self.lbl_age_warning.configure(
                            text="⚠️ Подросток 14-17 лет — необходимо нотариальное согласие родителей!")
                        self.minor_consent_frame.grid()
                        # для РФ кнопку не блокируем — скан проверяется при сохранении
            except ValueError:
                self.lbl_error.configure(text="Неверный формат даты рождения! Используйте ДД.ММ.ГГГГ")
                return None

        # Определяем, иностранец ли
        is_foreign = (self.citizenship_quick_var.get() == "Иностранец")

        # Паспортные данные
        ps = self.quick_passport_series.get().strip() if self.quick_passport_series.winfo_ismapped() else None
        pn = self.quick_passport_number.get().strip()

        # Проверяем серию ТОЛЬКО если поле серии видимо (т.е. для документов, где она требуется)
        if self.quick_passport_series.winfo_ismapped() and not ps:
            series_label = "серию паспорта" if self.doc_type_quick.get() == "Паспорт гражданина РФ" else "серию документа"
            self.lbl_error.configure(text=f"Заполните {series_label}!")
            return None
        if not pn:
            series_label = "номер паспорта" if self.doc_type_quick.get() == "Паспорт гражданина РФ" else "номер документа"
            self.lbl_error.configure(text=f"Заполните {series_label}!")
            return None

        # --- Проверка миграционной карты для иностранцев ---
        if is_foreign:
            migr_num = self.entry_migration_quick.get().strip()
            migr_expiry = self.entry_migration_expiry.get().strip()
            if not migr_num:
                self.lbl_error.configure(text="Для иностранца обязательна миграционная карта!")
                return None
            if not migr_expiry:
                self.lbl_error.configure(text="Укажите срок действия миграционной карты!")
                return None
            try:
                migr_expiry_date = datetime.datetime.strptime(migr_expiry, "%d.%m.%Y").date()
            except ValueError:
                self.lbl_error.configure(text="Неверный формат даты миграционной карты! Используйте ДД.ММ.ГГГГ")
                return None

            # Проверка на просрочку
            if migr_expiry_date < datetime.date.today():
                self.lbl_error.configure(text="Срок действия миграционной карты истёк! Заселение невозможно.")
                return None

        # --- ПРОВЕРКА СРОКА ДЕЙСТВИЯ ДОКУМЕНТА (для всех типов, где show_expiry = True) ---
        doc_type = self.doc_type_quick.get()
        rules = self.document_rules.get(doc_type, {})
        if rules.get("show_expiry", False):
            expiry_str = self.entry_doc_expiry.get().strip()
            if not expiry_str:
                self.lbl_error.configure(text=f"Укажите срок действия для документа '{doc_type}'!")
                return None
            try:
                expiry_date = datetime.datetime.strptime(expiry_str, "%d.%m.%Y").date()
            except ValueError:
                self.lbl_error.configure(text="Неверный формат даты срока действия! Используйте ДД.ММ.ГГГГ")
                return None

            # Проверка на просрочку
            if expiry_date < datetime.date.today():
                self.lbl_error.configure(
                    text=f"Срок действия документа '{doc_type}' истёк! Укажите действительный документ.")
                return None

        # --- Парсим даты заезда/выезда ---
        try:
            check_in = datetime.datetime.strptime(self.entry_checkin.get().strip(), "%d.%m.%Y").date()
        except ValueError:
            self.lbl_error.configure(text="Неверный формат даты заезда! Используйте ДД.ММ.ГГГГ")
            return None

        try:
            check_out = datetime.datetime.strptime(self.entry_checkout.get().strip(), "%d.%m.%Y").date()
        except ValueError:
            self.lbl_error.configure(text="Неверный формат даты выезда! Используйте ДД.ММ.ГГГГ")
            return None

        if check_in >= check_out:
            self.lbl_error.configure(text="Дата выезда должна быть позже даты заезда!")
            return None

        if check_in < datetime.date.today():
            self.lbl_error.configure(text="Дата заезда не может быть в прошлом!")
            return None

        room_str = self.room_selection.get()
        if room_str == "Нет свободных номеров":
            self.lbl_error.configure(text="Нет свободных номеров!")
            return None

        room_num_str = room_str.split("-")[0].strip()
        room_data = self._free_rooms_data.get(room_num_str)
        if not room_data:
            self.lbl_error.configure(text="Ошибка выбора номера!")
            return None

        return check_in, check_out, room_data


    def submit_guest(self):
        # 1. Очищаем предыдущую зелёную надпись
        self.lbl_total.configure(text="")

        # 2. Блокируем кнопку, чтобы повторное нажатие не сработало
        self.submit_button.configure(state="disabled")
        self.update_idletasks()

        try:
            # 3. Проверка согласия
            if not self.agree_var.get():
                self.lbl_error.configure(text="Необходимо согласие на обработку персональных данных!")
                return

            # 4. Валидация формы
            result = self._parse_form()
            if result is None:
                return

            check_in, check_out, room_data = result

            ln = self.entry_last_name.get().strip()
            fn = self.entry_first_name.get().strip()
            pt = self.entry_patronymic.get().strip()
            ph = self.entry_phone.get().strip()
            ps = self.quick_passport_series.get().strip() if self.quick_passport_series.winfo_ismapped() else None
            pn = self.quick_passport_number.get().strip()
            doc_type = self.doc_type_quick.get()

            discount = self._get_discount()
            if discount is None:
                return

            extras_total = self._early_checkin_price + self._late_checkout_price

            # --- Дополнительные поля (миграция, срок действия) ---
            is_foreign = (self.citizenship_quick_var.get() == "Иностранец")
            migr_num = self.entry_migration_quick.get().strip() if is_foreign else None
            migr_expiry = self.entry_migration_expiry.get().strip() if is_foreign else None
            doc_expiry = self.entry_doc_expiry.get().strip() if self.doc_expiry_frame.winfo_ismapped() else None
            citizenship = self.citizenship_quick_var.get()

            # Получаем дату рождения
            birth_date_str = self.entry_birth_quick.get().strip()
            if not birth_date_str:
                birth_date_str = None

            # --- Поиск существующего гостя по документу ---
            existing = None
            if pn:
                if doc_type == "Паспорт гражданина РФ" and ps:
                    existing = find_guest_by_russian_passport(ps, pn)
                else:
                    existing = find_guest_by_doc(doc_type, pn)

            guest_id = None
            if existing:
                guest_id = existing[0]
                if ph != existing[4]:
                    update_guest_phone(guest_id, ph)
                # Обновляем миграционные данные если иностранец
                if is_foreign or doc_expiry:
                    update_guest_full_profile(guest_id, {
                        "doc_type":              doc_type,
                        "doc_series":            ps,
                        "doc_number":            pn,
                        "migration_card_number": migr_num,
                        "migration_card_expiry": migr_expiry,
                        "citizenship":           citizenship,
                        "doc_expiry_date":       doc_expiry,
                    })
            else:
                new_guest_dto = GuestDTO(
                    last_name  = ln,
                    first_name = fn,
                    patronymic = pt,
                    phone      = ph,
                    doc_type   = doc_type,
                    doc_series = ps,
                    doc_number = pn,
                )
                guest_id = save_guest_extended(
                    new_guest_dto,
                    extra={
                        "migration_card_number": migr_num,
                        "migration_card_expiry": migr_expiry,
                        "doc_expiry_date":       doc_expiry,
                        "citizenship":           citizenship,
                        "birth_date":            birth_date_str,
                    }
                )

            if guest_id is None:
                self.lbl_error.configure(text="Ошибка сохранения гостя!")
                return

            # Создаём доменные объекты → Booking → DTO
            from guest import Guest
            from room import create_room
            from booking import Booking

            try:
                domain_guest = Guest(ln, fn, pt, ph)
            except ValueError:
                # Телефон может быть в нестандартном формате — создаём без него
                domain_guest = Guest(ln, fn, pt)

            room_row   = self._free_rooms_data.get(str(room_data[0]))
            domain_room = create_room(room_data[0], room_data[1], room_data[2])
            domain_booking = Booking(domain_guest, domain_room, check_in, check_out, discount)

            if self._early_checkin_price:
                domain_booking.add_extra("Ранний заезд", self._early_checkin_price)
            if self._late_checkout_price:
                domain_booking.add_extra("Поздний выезд", self._late_checkout_price)

            booking_dto = BookingDTO.from_booking(domain_booking)
            booking_dto.guest.guest_id = guest_id

            add_booking(
                booking_dto,
                check_in_time  = self.checkin_time_var.get(),
                check_out_time = self.checkout_time_var.get(),
            )

            self.lbl_error.configure(text="")
            nights = (check_out - check_in).days
            self.lbl_total.configure(
                text=f"✓ Гость {ln} {fn} заселён! ID #{guest_id:05d} | {nights} ночей | {domain_booking.total_price} руб."
            )

            # Очистка формы
            for entry in [self.entry_last_name, self.entry_first_name,
                          self.entry_patronymic, self.entry_phone,
                          self.entry_birth_quick,
                          self.quick_passport_series, self.quick_passport_number,
                          self.discount_entry]:
                entry.delete(0, "end")

            self._reset_entry_placeholder(self.discount_entry, "0-100")
            self.discount_var.set("Без скидки")
            self.checkin_time_var.set("14:00")
            self.checkout_time_var.set("12:00")
            self._early_checkin_price = 0
            self._late_checkout_price = 0
            self.extras_frame.grid_remove()

            self._reset_entry_placeholder(self.entry_birth_quick, "ДД.ММ.ГГГГ")
            self.lbl_age_warning.configure(text="")
            self.minor_consent_frame.grid_remove()
            self.minor_consent_label.configure(text="Скан согласия не прикреплён", text_color="#888888")
            self.minor_consent_btn_remove.pack_forget()
            if hasattr(self, 'minor_consent_path'):
                del self.minor_consent_path

            if is_foreign:
                self.entry_migration_quick.delete(0, "end")
                self.entry_migration_expiry.delete(0, "end")
            if self.doc_expiry_frame.winfo_ismapped():
                self.entry_doc_expiry.delete(0, "end")

        finally:
            # 5. Разблокируем кнопку через 500 мс, учитывая чекбокс
            def enable():
                self.submit_button.configure(state="normal" if self.agree_var.get() else "disabled")

            self.after(500, enable)

    def _apply_theme(self, theme, settings_window):
        ctk.set_appearance_mode(theme)
        settings_window.destroy()

        def rebuild():
            self.clear_main_frame()
            current = getattr(self, 'current_screen', 'rooms')
            if current == 'rooms':
                self.show_rooms()
            elif current == 'guests':
                self.show_guests()
            elif current == 'booking':
                self.show_booking_form()
            else:
                self.show_rooms()

        self.after(100, rebuild)

    def open_room_details(self, room_number, event):
        # 1. Достаем актуальные данные из БД и ищем нужный номер
        room_data = get_rooms_with_status()
        current_room = next((r for r in room_data if r[0] == room_number), None)
        if not current_room: return

        # 2. Распаковываем кортеж в переменные
        num, r_type, price, is_busy, l_name, f_name, check_in, check_out, guest_id = current_room

        # 3. Закрываем предыдущее окно деталей если открыто
        if self._details_window is not None:
            try:
                self._details_window.destroy()
            except Exception:
                pass
            self._details_window = None

        # 4. Создаем всплывающее окно
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"Номер №{room_number}")
        details_window.resizable(False, False)
        details_window.transient(self)
        self._details_window = details_window
        details_window.protocol("WM_DELETE_WINDOW", lambda: self._close_details())

        # 4. Наполняем интерфейс окна
        ctk.CTkLabel(details_window, text=f"Номер №{num}", font=("Arial", 18)).pack(pady=(15, 5), padx=30)

        info_text = f"Тип: {r_type} | Цена: {price}₽"
        ctk.CTkLabel(details_window, text=info_text, font=("Arial", 12)).pack(pady=5)

        # Тонкая серая линия-разделитель
        ctk.CTkFrame(details_window, height=2, fg_color="gray").pack(fill="x", padx=20, pady=10)

        # Логика: что показывать в зависимости от статуса
        if is_busy:
            ctk.CTkLabel(details_window, text="ТЕКУЩИЙ ЖИЛЕЦ:", font=("Arial", 10), text_color="#e74c3c").pack()
            # Имя гостя (Фамилия И.)
            ctk.CTkLabel(details_window, text=f"{l_name} {f_name[0]}.", font=("Arial", 15)).pack(pady=5)

            ctk.CTkLabel(details_window, text=f"Заезд: {check_in}", font=("Arial", 11)).pack()
            ctk.CTkLabel(details_window, text=f"Выезд: {check_out}", font=("Arial", 11)).pack(pady=(0, 5))

            # --- СЕКЦИЯ ГОСТЕЙ В НОМЕРЕ ---
            ctk.CTkFrame(details_window, height=1, fg_color=("#444444")).pack(fill="x", padx=20, pady=(10, 5))
            ctk.CTkLabel(details_window, text="ГОСТИ В НОМЕРЕ:", font=("Arial", 10), text_color=("#1a1a1a", "#888888")).pack()

            booking_id = get_active_booking_id(num)

            # Фрейм со списком гостей (будем обновлять)
            guests_list_frame = ctk.CTkFrame(details_window, fg_color="transparent")
            guests_list_frame.pack(fill="x", padx=20, pady=5)

            def refresh_guests():
                for w in guests_list_frame.winfo_children():
                    w.destroy()
                if booking_id:
                    guests = get_booking_guests(booking_id)
                    if guests:
                        for g in guests:
                            g_id, g_last, g_first, g_pat, g_doc_type, g_doc_num, g_birth, g_primary = g
                            tag = " 👑" if g_primary else ""
                            text = f"{g_last} {g_first[0]}.{tag}  |  {g_doc_type}: {g_doc_num or '—'}"
                            ctk.CTkLabel(
                                guests_list_frame,
                                text=text,
                                font=("Arial", 11),
                                text_color=("#666666", "#cccccc")
                            ).pack(anchor="w", pady=1)
                    else:
                        ctk.CTkLabel(
                            guests_list_frame,
                            text="Список пуст",
                            font=("Arial", 11),
                            text_color="#666666"
                        ).pack()

            refresh_guests()

            # Кнопка добавить гостя
            if booking_id:
                ctk.CTkButton(
                    details_window,
                    text="+ Добавить гостя",
                    width=160,
                    height=28,
                    fg_color="#1f538d",
                    hover_color="#1a4a7a",
                    font=("Arial", 12),
                    command=lambda: self.open_add_guest_window(booking_id, details_window, refresh_guests, num)
                ).pack(pady=(5, 10))

            ctk.CTkFrame(details_window, height=1, fg_color="#444444").pack(fill="x", padx=20, pady=(0, 5))

            # Кнопка выселения
            btn_checkout = ctk.CTkButton(
                details_window,
                text="ВЫСЕЛИТЬ",
                fg_color="#c0392b",
                hover_color="#a93226",
                text_color="#D3D3D3",
                command=lambda: self.checkout_guest(num, details_window)
            )
            btn_checkout.pack(pady=15)
        else:
            ctk.CTkLabel(details_window, text="Номер свободен", text_color="#2ecc71", font=("Arial", 14)).pack(pady=20)

        # Кнопка закрытия
        ctk.CTkButton(
            details_window,
            text="Назад",
            command=details_window.destroy,
            fg_color="transparent",
            border_width=1,
            text_color=("black", "white")
        ).pack(pady=(0, 15))

        # 5. Позиционирование
        details_window.update()
        details_window.update_idletasks()

        win_w     = details_window.winfo_reqwidth()
        win_h     = details_window.winfo_reqheight()
        mouse_x   = event.x_root
        mouse_y   = event.y_root
        taskbar_h = 60

        # Границы главного окна
        app_x      = self.winfo_rootx()
        app_y      = self.winfo_rooty()
        app_w      = self.winfo_width()
        app_h      = self.winfo_height()
        app_right  = app_x + app_w
        app_bottom = min(app_y + app_h, self.winfo_screenheight() - taskbar_h)

        # По горизонтали — справа от курсора, если не влезает — слева
        if mouse_x + win_w + 20 > app_right:
            pos_x = mouse_x - win_w - 20
        else:
            pos_x = mouse_x + 20

        # По вертикали — ниже курсора, если не влезает — прижимаем вверх
        if mouse_y + win_h + 20 > app_bottom:
            pos_y = app_bottom - win_h - 10
        else:
            pos_y = mouse_y + 20

        # Защита от выхода за верхний и левый край
        pos_y = max(app_y + 10, pos_y)
        pos_x = max(app_x + 10, pos_x)

        details_window.geometry(f"+{pos_x}+{pos_y}")

    def open_add_guest_window(self, booking_id, parent_window, refresh_callback, room_number=None):
        """Окно добавления дополнительного гостя в бронь"""
        add_window = ctk.CTkToplevel(parent_window)
        title = f"Добавить гостя — Номер №{room_number}" if room_number else "Добавить гостя"
        add_window.title(title)
        add_window.resizable(False, True)
        add_window.transient(parent_window)
        add_window.grab_set()

        # Компактный и расширенный размер
        WIDTH       = 390
        HEIGHT_COMPACT  = 520
        HEIGHT_EXPANDED = 750
        add_window.geometry(f"{WIDTH}x{HEIGHT_COMPACT}")  # начальный размер без позиции

        _expanded = [False]  # список чтобы можно было менять внутри вложенной функции

        # Заголовок + кнопка разворота в одну строку
        header_frame = ctk.CTkFrame(add_window, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))
        header_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame, text="Новый гость",
            font=("Arial", 16, "bold")
        ).grid(row=0, column=0, sticky="w")

        expand_btn = ctk.CTkButton(
            header_frame,
            text="⛶ Развернуть",
            width=110, height=26,
            font=("Arial", 11),
            fg_color="transparent",
            border_width=1,
            text_color=("#333333", "#aaaaaa"),
            command=lambda: _toggle_size()
        )
        expand_btn.grid(row=0, column=1, sticky="e")

        def _toggle_size():
            screen_w  = add_window.winfo_screenwidth()
            screen_h  = add_window.winfo_screenheight()
            taskbar_h = 60
            work_h    = screen_h - taskbar_h

            if _expanded[0]:
                new_w = WIDTH
                new_h = min(HEIGHT_COMPACT, work_h)
                new_x = (screen_w - new_w) // 2
                new_y = (work_h - new_h) // 2
                expand_btn.configure(text="⛶ Развернуть")
                _expanded[0] = False
            else:
                new_w = WIDTH
                new_h = work_h
                new_x = 0
                new_y = 0
                expand_btn.configure(text="⛶ Свернуть")
                _expanded[0] = True

            add_window.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")

        ctk.CTkFrame(add_window, height=2, fg_color="gray").pack(fill="x", padx=20, pady=(5, 10))

        # Кнопки фиксируем внизу ДО скролла — иначе скролл их вытолкнет за панель
        btn_frame = ctk.CTkFrame(add_window, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=15, padx=25, fill="x")

        ctk.CTkFrame(add_window, height=1, fg_color="#333333").pack(side="bottom", fill="x", padx=20)

        # Скроллируемый контейнер для формы — занимает всё оставшееся место
        scroll = ctk.CTkScrollableFrame(add_window, fg_color="transparent", width=340)
        scroll.pack(fill="both", expand=True, padx=5, pady=0)

        form_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        form_frame.pack(padx=20, pady=5, fill="x", expand=True)

        # --- ФИО ---
        ctk.CTkLabel(form_frame, text="ФИО", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        entry_last = ctk.CTkEntry(form_frame, placeholder_text="Фамилия *", width=300)
        entry_last.grid(row=1, column=0, columnspan=2, pady=4, sticky="ew")

        entry_first = ctk.CTkEntry(form_frame, placeholder_text="Имя *", width=300)
        entry_first.grid(row=2, column=0, columnspan=2, pady=4, sticky="ew")

        entry_pat = ctk.CTkEntry(form_frame, placeholder_text="Отчество", width=300)
        entry_pat.grid(row=3, column=0, columnspan=2, pady=4, sticky="ew")

        # --- Дата рождения и гражданство ---
        ctk.CTkLabel(form_frame, text="Дата рождения:", font=("Arial", 12)).grid(
            row=4, column=0, sticky="w", pady=(10, 2))
        entry_birth = ctk.CTkEntry(form_frame, placeholder_text="ДД.ММ.ГГГГ", width=140)
        entry_birth.grid(row=5, column=0, sticky="w", pady=4)

        ctk.CTkLabel(form_frame, text="Гражданство:", font=("Arial", 12)).grid(
            row=4, column=1, sticky="w", padx=(15, 0), pady=(10, 2))
        citizenship_var = ctk.StringVar(value="РФ")
        ctk.CTkOptionMenu(
            form_frame,
            values=["РФ", "Иностранец"],
            variable=citizenship_var,
            width=140,
            command=lambda v: _on_citizenship(v)
        ).grid(row=5, column=1, sticky="w", padx=(15, 0), pady=4)

        # --- Тип документа ---
        ctk.CTkLabel(form_frame, text="Тип документа:", font=("Arial", 12)).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(10, 2))
        doc_type_var = ctk.StringVar(value="Паспорт гражданина РФ")
        doc_type_menu = ctk.CTkOptionMenu(
            form_frame,
            values=DOC_TYPES_ALL,
            variable=doc_type_var,
            width=280,
            command=lambda v: _on_doc_type(v)
        )
        doc_type_menu.grid(row=7, column=0, columnspan=2, pady=4, sticky="ew")

        # --- Серия + Номер документа ---
        doc_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        doc_frame.grid(row=8, column=0, columnspan=2, pady=4, sticky="ew")
        doc_frame.grid_columnconfigure(0, weight=1)
        doc_frame.grid_columnconfigure(1, weight=2)

        entry_series = ctk.CTkEntry(doc_frame, placeholder_text="Серия", width=90)
        entry_series.grid(row=0, column=0, padx=(0, 10), sticky="w")

        entry_number = ctk.CTkEntry(doc_frame, placeholder_text="Номер документа *", width=180)
        entry_number.grid(row=0, column=1, sticky="ew")

        # --- Миграционная карта (для иностранцев) ---
        migration_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        migration_frame.grid(row=9, column=0, columnspan=2, pady=4, sticky="ew")
        migration_frame.grid_remove()

        ctk.CTkLabel(migration_frame, text="Миграционная карта №:", font=("Arial", 11)).grid(
            row=0, column=0, sticky="w", padx=(0, 10))
        entry_migration = ctk.CTkEntry(migration_frame, width=160)
        entry_migration.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(migration_frame, text="Срок действия:", font=("Arial", 11)).grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
        entry_migration_expiry = ctk.CTkEntry(migration_frame, placeholder_text="ДД.ММ.ГГГГ", width=120)
        entry_migration_expiry.grid(row=1, column=1, sticky="w", pady=(5, 0))

        # --- Срок действия документа ---
        expiry_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        expiry_frame.grid(row=10, column=0, columnspan=2, pady=4, sticky="ew")
        expiry_frame.grid_remove()

        expiry_label = ctk.CTkLabel(
            expiry_frame, text="Срок действия:",
            font=("Arial", 11), wraplength=130, anchor="w", justify="left"
        )
        expiry_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        entry_expiry = ctk.CTkEntry(expiry_frame, placeholder_text="ДД.ММ.ГГГГ", width=120)
        entry_expiry.grid(row=0, column=1, sticky="w")

        # --- Предупреждение / ошибка ---
        lbl_warning = ctk.CTkLabel(form_frame, text="", font=("Arial", 11),
                                   text_color="#f39c12", wraplength=280)
        lbl_warning.grid(row=11, column=0, columnspan=2, pady=(8, 0), sticky="w")

        lbl_error = ctk.CTkLabel(form_frame, text="", font=("Arial", 11),
                                 text_color="#e74c3c", wraplength=280)
        lbl_error.grid(row=12, column=0, columnspan=2, sticky="w")

        # --- Обработчики смены типа документа и гражданства ---
        def _on_doc_type(value):
            rules = self.document_rules.get(value, {})
            if rules.get("show_series", True):
                entry_series.grid()
                self._reset_entry_placeholder(entry_series, rules.get("series_placeholder", "Серия"))
                # Восстанавливаем веса и ширину
                doc_frame.grid_columnconfigure(0, weight=1)
                doc_frame.grid_columnconfigure(1, weight=2)
                entry_number.configure(width=180)  # фиксированная ширина
                entry_number.grid(row=0, column=1, sticky="ew")
            else:
                entry_series.grid_remove()
                entry_series.delete(0, "end")
                # Серия скрыта — номер растягивается на всю ширину
                doc_frame.grid_columnconfigure(0, weight=0)
                doc_frame.grid_columnconfigure(1, weight=1)
                entry_number.configure(width=0)  # 0 означает растяжение
                entry_number.grid(row=0, column=1, sticky="ew")  # остаётся в колонке 1, но она одна видимая
            self._reset_entry_placeholder(entry_number, rules.get("number_placeholder", "Номер документа *"))
            if rules.get("show_expiry", False):
                expiry_frame.grid()
                expiry_label.configure(text=rules.get("expiry_label", "Срок действия:"))
                self._reset_entry_placeholder(entry_expiry, "ДД.ММ.ГГГГ")
            else:
                expiry_frame.grid_remove()

        def _on_citizenship(value):
            if value == "Иностранец":
                migration_frame.grid()
                self._reset_entry_placeholder(entry_migration, "Номер карты")
                self._reset_entry_placeholder(entry_migration_expiry, "ДД.ММ.ГГГГ")
                doc_type_menu.configure(values=["Загранпаспорт"])
                doc_type_var.set("Загранпаспорт")
                _on_doc_type("Загранпаспорт")
            else:
                migration_frame.grid_remove()
                doc_type_menu.configure(values=DOC_TYPES_ALL)
                doc_type_var.set("Паспорт гражданина РФ")
                _on_doc_type("Паспорт гражданина РФ")

        # --- Скан согласия родителей (скрыт по умолчанию, появляется для 14-17 лет) ---
        consent_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        consent_frame.grid(row=13, column=0, columnspan=2, pady=(5, 0), sticky="ew")
        consent_frame.grid_columnconfigure(0, weight=1)
        consent_frame.grid_remove()

        # Статус скана — строка 0
        consent_label = ctk.CTkLabel(
            consent_frame, text="Скан согласия не прикреплён",
            text_color="#888888", font=("Arial", 11),
            wraplength=280, anchor="w", justify="left"
        )
        consent_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # Кнопки — строка 1, не растягивают окно
        consent_btn_attach = ctk.CTkButton(
            consent_frame,
            text="📎 Согласие родителей",
            width=165,
            command=lambda: _attach_consent()
        )
        consent_btn_attach.grid(row=1, column=0, sticky="w")

        consent_btn_remove = ctk.CTkButton(
            consent_frame,
            text="✕",
            width=30,
            fg_color="#c0392b",
            hover_color="#a93226",
            command=lambda: _remove_consent()
        )
        consent_btn_remove.grid(row=1, column=1, padx=(8, 0), sticky="w")
        consent_btn_remove.grid_remove()

        def _attach_consent():
            self._attach_scan("_add_guest_consent_path", consent_label)
            if hasattr(self, "_add_guest_consent_path") and self._add_guest_consent_path:
                consent_btn_remove.grid()

        def _remove_consent():
            if hasattr(self, "_add_guest_consent_path"):
                del self._add_guest_consent_path
            consent_label.configure(text="Скан согласия не прикреплён", text_color="#888888")
            consent_btn_remove.grid_remove()

        def _check_age_warning():
            """Показывает предупреждение и кнопку скана если гостю 14-17 лет"""
            birth_str = entry_birth.get().strip()
            if not birth_str:
                lbl_warning.configure(text="")
                consent_frame.grid_remove()
                return
            try:
                birth = datetime.datetime.strptime(birth_str, "%d.%m.%Y").date()
                today = datetime.date.today()
                age   = (today - birth).days // 365
                if age < 14:
                    lbl_warning.configure(
                        text="⚠️ Ребёнок до 14 лет — нужно свидетельство о рождении и присутствие родителя!")
                    consent_frame.grid_remove()
                elif age < 18:
                    citizenship = citizenship_var.get()
                    if citizenship == "Иностранец":
                        lbl_warning.configure(
                            text="🚫 Несовершеннолетний иностранец — заселение без родителей невозможно!")
                        consent_frame.grid_remove()
                    else:
                        lbl_warning.configure(
                            text="⚠️ Подросток 14-17 лет — необходимо нотариальное согласие родителей!")
                        consent_frame.grid()
                else:
                    lbl_warning.configure(text="")
                    consent_frame.grid_remove()
            except ValueError:
                lbl_warning.configure(text="")
                consent_frame.grid_remove()

        entry_birth.bind("<FocusOut>", lambda e: _check_age_warning())

        def _save_guest():
            lbl_error.configure(text="")
            last = entry_last.get().strip()
            first = entry_first.get().strip()
            pat = entry_pat.get().strip()
            birth = entry_birth.get().strip()
            doc_type = doc_type_var.get()
            series = entry_series.get().strip()
            number = entry_number.get().strip()
            citizenship = citizenship_var.get()

            if not last or not first:
                lbl_error.configure(text="Заполните Фамилию и Имя!")
                return
            if not number:
                lbl_error.configure(text="Заполните номер документа!")
                return

            # --- Дата рождения ---
            birth_date_str = None
            if birth:
                try:
                    birth_date = datetime.datetime.strptime(birth, "%d.%m.%Y").date()
                    birth_date_str = birth
                    # Проверка скана согласия для 14-17 лет (граждане РФ)
                    age = (datetime.date.today() - birth_date).days // 365
                    if 14 <= age < 18 and citizenship_var.get() != "Иностранец":
                        if not hasattr(self, "_add_guest_consent_path") or not self._add_guest_consent_path:
                            lbl_error.configure(
                                text="Необходимо прикрепить скан нотариального согласия родителей!")
                            return
                except ValueError:
                    lbl_error.configure(text="Неверный формат даты рождения! Используйте ДД.ММ.ГГГГ")
                    return

            # --- Срок действия документа ---
            rules = self.document_rules.get(doc_type, {})
            doc_expiry_value = None
            if rules.get("show_expiry", False):
                expiry_str = entry_expiry.get().strip()
                if not expiry_str:
                    lbl_error.configure(text=f"Укажите срок действия для документа '{doc_type}'!")
                    return
                try:
                    expiry_date = datetime.datetime.strptime(expiry_str, "%d.%m.%Y").date()
                    if expiry_date < datetime.date.today():
                        lbl_error.configure(text=f"Срок действия документа '{doc_type}' истёк!")
                        return
                    doc_expiry_value = expiry_str
                except ValueError:
                    lbl_error.configure(text="Неверный формат даты срока действия (ДД.ММ.ГГГГ)!")
                    return

            # --- Миграционная карта ---
            migr_num_value = None
            migr_expiry_value = None
            if citizenship == "Иностранец":
                migr_num_value = entry_migration.get().strip()
                migr_expiry_value = entry_migration_expiry.get().strip()
                if not migr_num_value:
                    lbl_error.configure(text="Для иностранца обязательна миграционная карта!")
                    return
                if not migr_expiry_value:
                    lbl_error.configure(text="Укажите срок действия миграционной карты!")
                    return
                try:
                    migr_expiry_date = datetime.datetime.strptime(migr_expiry_value, "%d.%m.%Y").date()
                    if migr_expiry_date < datetime.date.today():
                        lbl_error.configure(text="Срок действия миграционной карты истёк!")
                        return
                except ValueError:
                    lbl_error.configure(text="Неверный формат даты миграционной карты (ДД.ММ.ГГГГ)!")
                    return

            new_guest_dto = GuestDTO(
                last_name  = last,
                first_name = first,
                patronymic = pat,
                doc_type   = doc_type,
                doc_series = series or None,
                doc_number = number,
            )

            guest_id = save_guest_extended(
                new_guest_dto,
                extra={
                    "migration_card_number": migr_num_value,
                    "migration_card_expiry": migr_expiry_value,
                    "doc_expiry_date":       doc_expiry_value,
                    "citizenship":           citizenship,
                    "birth_date":            birth_date_str,
                }
            )

            if guest_id:
                add_guest_to_booking(booking_id, guest_id, is_primary=0)
                if hasattr(self, "_add_guest_consent_path"):
                    del self._add_guest_consent_path
                refresh_callback()
                add_window.destroy()
            else:
                lbl_error.configure(text="Ошибка сохранения!")

        ctk.CTkButton(
            btn_frame,
            text="💾  Сохранить",
            fg_color="#27ae60",
            hover_color="#1e8449",
            command=_save_guest
        ).pack(side="left", expand=True, padx=(0, 5))

        ctk.CTkButton(
            btn_frame,
            text="Отмена",
            fg_color="transparent",
            border_width=1,
            command=add_window.destroy,
            text_color=("#1a1a1a", "#D3D3D3")
        ).pack(side="left", expand=True, padx=(5, 0))

        # Инициализация полей
        _on_doc_type("Паспорт гражданина РФ")

        # Позиционирование — по центру родительского окна, не вылезая за экран
        add_window.update_idletasks()
        screen_w  = add_window.winfo_screenwidth()
        screen_h  = add_window.winfo_screenheight()
        taskbar_h = 60  # резерв под панель задач Windows
        work_h    = screen_h - taskbar_h

        pw_x = parent_window.winfo_rootx()
        pw_y = parent_window.winfo_rooty()
        pw_w = parent_window.winfo_width()
        pw_h = parent_window.winfo_height()

        # Компактный размер не должен превышать рабочую область
        compact_h = min(HEIGHT_COMPACT, work_h)

        pos_x = pw_x + (pw_w - WIDTH) // 2
        pos_y = pw_y + (pw_h - compact_h) // 2

        # Не вылезаем за края рабочей области
        pos_x = max(0, min(pos_x, screen_w - WIDTH - 10))
        pos_y = max(0, min(pos_y, work_h - compact_h))

        add_window.geometry(f"{WIDTH}x{compact_h}+{pos_x}+{pos_y}")

    def _close_details(self):
        """Закрывает окно деталей номера и сбрасывает ссылку."""
        if self._details_window is not None:
            try:
                self._details_window.destroy()
            except Exception:
                pass
            self._details_window = None

    def checkout_guest(self, room_number, window):
        success = check_out_guest(room_number)
        if success:
            self._details_window = None
            window.destroy()
            self.show_rooms()
        else:
            import tkinter.messagebox as mb
            mb.showerror("Ошибка", f"Не удалось выселить гостя из номера {room_number}.", parent=window)

    def open_settings(self):
        """Создает окно настроек с вкладками"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Настройки системы")
        settings_window.geometry("400x400")
        settings_window.attributes("-topmost", True)
        settings_window.grab_set()

        tab_view = ctk.CTkTabview(
            settings_window,
            fg_color="transparent",
            segmented_button_fg_color="#2b2b2b",
            segmented_button_selected_color="#1f538d",
            segmented_button_unselected_color="#2b2b2b",
            segmented_button_selected_hover_color="#1a4a7a",
        )
        tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        tab_view.add("🎨  Интерфейс")
        tab_view.add("💰  Тарифы")

        # --- Вкладка Интерфейс ---
        tab_ui = tab_view.tab("🎨  Интерфейс")

        # 1. Делаем вкладку прокручиваемой
        ui_scroll = ctk.CTkScrollableFrame(tab_ui, fg_color="transparent")
        ui_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        ui_scroll.grid_columnconfigure(0, weight=1)

        # 2. Тема оформления
        ctk.CTkLabel(ui_scroll, text="Тема оформления:").grid(row=0, column=0, pady=(20, 0))
        theme_menu = ctk.CTkOptionMenu(ui_scroll, values=["Dark", "Light"],
                                       command=lambda v: self._apply_theme(v, settings_window))
        theme_menu.set(ctk.get_appearance_mode())
        theme_menu.grid(row=1, column=0, pady=10)

        # 3. Количество карточек в ряд
        ctk.CTkLabel(ui_scroll, text="Карточек в ряд:").grid(row=2, column=0, pady=(10, 0))
        grid_menu = ctk.CTkOptionMenu(ui_scroll, values=["3", "4", "5", "6", "8"], command=self.update_grid_view)
        grid_menu.set(str(self.columns_count))
        grid_menu.grid(row=3, column=0, pady=10)

        ctk.CTkLabel(
            ui_scroll,
            text="* При большом масштабе рекомендуется 3-4 карточки",
            font=("Arial", 10),
            text_color="#888888"
        ).grid(row=4, column=0, pady=(0, 10))

        # --- Масштаб интерфейса ---
        ctk.CTkLabel(ui_scroll, text="Масштаб интерфейса:", font=("Arial", 12)).grid(
            row=5, column=0, pady=(20, 5))

        current_scale = float(get_setting("ui_scale", "1.0") or "1.0")
        scale_var = ctk.DoubleVar(value=current_scale)

        scale_label = ctk.CTkLabel(ui_scroll, text=f"{current_scale:.1f}x", font=("Arial", 12))

        ctk.CTkSlider(
            ui_scroll,
            from_=0.8, to=2.5,
            number_of_steps=17,
            variable=scale_var,
            command=lambda v: scale_label.configure(text=f"{float(v):.1f}x")
        ).grid(row=6, column=0, pady=5)

        scale_label.grid(row=7, column=0, pady=0)

        ctk.CTkLabel(
            ui_scroll,
            text="⚠️ Применится после перезапуска",
            font=("Arial", 11),
            text_color="#f39c12"
        ).grid(row=8, column=0, pady=(0, 5))

        def save_scale():
            val = round(scale_var.get(), 1)
            import sys, os, subprocess
            script = os.path.abspath(sys.argv[0])

            save_setting("ui_scale", str(val))

            import tkinter.messagebox as mb
            answer = mb.askyesno(
                "Перезапуск",
                f"Масштаб {val}x сохранён.\nПерезапустить приложение сейчас?",
                parent=settings_window
            )
            if answer:
                subprocess.Popen(
                    [sys.executable, script],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.quit()
                self.destroy()

        ctk.CTkButton(
            ui_scroll,
            text="💾 Сохранить масштаб",
            fg_color="#1f538d",
            hover_color="#1a4a7a",
            command=save_scale
        ).grid(row=9, column=0, pady=5)

        lbl_scale_saved = ctk.CTkLabel(ui_scroll, text="", font=("Arial", 11))
        lbl_scale_saved.grid(row=10, column=0, pady=5)

        # --- Вкладка Тарифы ---
        tab_rates = tab_view.tab("💰  Тарифы")
        tab_rates.grid_columnconfigure(0, weight=1)
        tab_rates.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(tab_rates, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(1, weight=1)

        # Читаем текущие тарифы из БД через get_setting
        current_rates = {}
        early_hours = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"]
        late_hours  = ["13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05"]
        for h in early_hours:
            key = f"early_checkin_{h}"
            current_rates[key] = get_setting(key, "0")
        for h in late_hours:
            key = f"late_checkout_{h}"
            current_rates[key] = get_setting(key, "0")
        rate_entries = {}

        ctk.CTkLabel(scroll, text="Ранний заезд",
                     font=("Arial", 14, "bold"), text_color="#4a9eff").grid(
            row=0, column=0, columnspan=3, pady=(15, 5), padx=15, sticky="w")

        for i, hour in enumerate(early_hours):
            key = f"early_checkin_{hour}"
            ctk.CTkLabel(scroll, text=f"Заезд в {hour}:00").grid(
                row=i + 1, column=0, padx=(15, 10), pady=3, sticky="w")
            entry = ctk.CTkEntry(scroll, width=100)
            entry.insert(0, current_rates.get(key, "0"))
            entry.grid(row=i + 1, column=1, padx=5, pady=3, sticky="w")
            ctk.CTkLabel(scroll, text="руб").grid(row=i + 1, column=2, padx=(0, 15), sticky="w")
            rate_entries[key] = entry

        ctk.CTkLabel(scroll, text="Поздний выезд",
                     font=("Arial", 14, "bold"), text_color="#4a9eff").grid(
            row=len(early_hours) + 1, column=0, columnspan=3, pady=(15, 5), padx=15, sticky="w")

        late_hours = ["13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04",
                      "05"]
        for i, hour in enumerate(late_hours):
            key = f"late_checkout_{hour}"
            row = len(early_hours) + 2 + i
            ctk.CTkLabel(scroll, text=f"Выезд в {hour}:00").grid(
                row=row, column=0, padx=(15, 10), pady=3, sticky="w")
            entry = ctk.CTkEntry(scroll, width=100)
            entry.insert(0, current_rates.get(key, "0"))
            entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
            ctk.CTkLabel(scroll, text="руб").grid(row=row, column=2, padx=(0, 15), sticky="w")
            rate_entries[key] = entry

        def save_rates():
            for key, entry in rate_entries.items():
                val = entry.get().strip()
                if val.isdigit():
                    save_setting(key, val)
            lbl_saved.configure(text="✓ Сохранено!", text_color="#2ecc71")
            settings_window.after(2000, lambda: lbl_saved.configure(text=""))

        lbl_saved = ctk.CTkLabel(tab_rates, text="", font=("Arial", 12))
        lbl_saved.grid(row=1, column=0, pady=5)

        ctk.CTkButton(
            tab_rates,
            text="💾  Сохранить тарифы",
            command=save_rates,
            fg_color="#1f538d",
            hover_color="#1a4a7a"
        ).grid(row=2, column=0, pady=(5, 10))

        # Кнопка закрытия
        ctk.CTkButton(
            settings_window,
            text="Готово",
            command=settings_window.destroy,
            fg_color="transparent",
            text_color=("black", "white"),
            border_width=1
        ).pack(side="bottom", pady=10)

    def update_grid_view(self, value):
        """Меняет цифру и перерисовывает экран"""
        self.columns_count = int(value)
        self.show_rooms()

    def show_tooltip(self, event, text):
        # Отменяем таймер скрытия если есть
        if hasattr(self, '_hide_timer') and self._hide_timer:
            self.after_cancel(self._hide_timer)
            self._hide_timer = None

        # Отменяем предыдущий таймер если есть
        if self.tooltip_timer:
            self.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None

        # Сохраняем последние координаты и текст
        self._tooltip_text = text
        self._tooltip_x = event.x_root
        self._tooltip_y = event.y_root

        # Показываем с задержкой 250мс
        self.tooltip_timer = self.after(250, self._create_tooltip)

    def _create_tooltip(self):
        # Если окно уже есть - уничтожаем и создаём заново
        if self.tooltip_window is not None:
            try:
                self.tooltip_window.destroy()
            except:
                pass
            self.tooltip_window = None

        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.attributes("-topmost", True)

        lbl = tk.Label(
            self.tooltip_window,
            text=self._tooltip_text,
            background="#3d3d3d",
            foreground="white",
            relief="flat",
            padx=10,
            pady=6,
            wraplength=200,
            font=("Arial", 16),
            justify="left"
        )
        lbl.pack()
        self.tooltip_window.label = lbl
        self.tooltip_window.geometry(f"+{self._tooltip_x + 15}+{self._tooltip_y + 10}")

        self.tooltip_timer = self.after(3000, self.hide_tooltip)

    def hide_tooltip(self, event=None):
        if self.tooltip_timer:
            self.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None

        # Скрываем с небольшой задержкой
        self._hide_timer = self.after(100, self._do_hide_tooltip)

    def _do_hide_tooltip(self):
        self._hide_timer = None
        if self.tooltip_window is not None:
            try:
                self.tooltip_window.destroy()
            except:
                pass
            self.tooltip_window = None

    def move_tooltip(self, event):
        # Обновляем сохранённые координаты
        self._tooltip_x = event.x_root
        self._tooltip_y = event.y_root

        if self.tooltip_window is not None:
            try:
                self.tooltip_window.geometry(f"+{event.x_root + 15}+{event.y_root + 10}")
            except:
                self.tooltip_window = None

    def open_calendar(self, target_entry):
        cal_window = tk.Toplevel(self)
        cal_window.wm_overrideredirect(True)
        cal_window.title("Выберите дату")
        cal_window.attributes("-topmost", True)
        cal_window.resizable(False, False)
        cal_window.grab_set()

        # Парсим текущую дату из поля чтобы календарь открылся на ней
        try:
            current = datetime.datetime.strptime(target_entry.get(), "%d.%m.%Y").date()
        except ValueError:
            current = datetime.date.today()

        cal = Calendar(
            cal_window,
            selectmode="day",
            year=current.year,
            month=current.month,
            day=current.day,
            date_pattern="dd.mm.yyyy",
            background="#2b2b2b",
            foreground="white",
            headersbackground="#1f538d",
            headersforeground="white",
            selectbackground="#1f538d",
            normalbackground="#2b2b2b",
            normalforeground="white",
            weekendbackground="#2b2b2b",
            weekendforeground="#aaaaaa",
            othermonthbackground="#1a1a1a",
            othermonthforeground="#555555",
            bordercolor="#333333",
            font=("Arial", 16),  # было 11
            showweeknumbers=False,  # убираем лишний столбец с номерами недель
        )
        cal.pack(padx=10, pady=10, fill="both", expand=True)

        # Растягиваем окно
        cal_window.minsize(400, 320)

        def confirm():
            target_entry.delete(0, "end")
            target_entry.insert(0, cal.get_date())
            cal_window.destroy()

        ctk.CTkButton(cal_window, text="Выбрать", command=confirm).pack(pady=(0, 10))

        # Позиционируем рядом с кнопкой
        cal_window.update_idletasks()

        # Получаем координаты поля ввода
        entry_x = target_entry.winfo_rootx()
        entry_y = target_entry.winfo_rooty()
        entry_h = target_entry.winfo_height()
        cal_h = cal_window.winfo_reqheight()
        cal_w = cal_window.winfo_reqwidth()

        # Открываем под полем
        pos_x = entry_x
        pos_y = entry_y + entry_h + 5

        # Защита от выхода за края экрана
        app_bottom = self.winfo_rooty() + self.winfo_height()
        app_right = self.winfo_rootx() + self.winfo_width()

        if pos_y + cal_h > app_bottom:
            pos_y = entry_y - cal_h - 5
        if pos_x + cal_w > app_right:
            pos_x = app_right - cal_w - 10

        cal_window.geometry(f"+{pos_x}+{pos_y}")

if __name__ == '__main__':
    init_db()
    seed_rooms()

    # Читаем сохранённый масштаб до создания окна
    saved_scale = get_setting("ui_scale", None)
    if saved_scale:
        try:
            scale = float(saved_scale)
            ctk.set_widget_scaling(scale)
            ctk.set_window_scaling(scale)
        except:
            pass

    app = HotelApp()
    app.mainloop()