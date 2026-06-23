# HotelAdmin Pro

> 🇷🇺 [Русский](#ru) | 🇬🇧 [English](#en)

---

<a name="ru"></a>
## 🇷🇺 Русский

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-5C85D6?style=flat)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Статус-В%20разработке-orange?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

**HotelAdmin Pro** — десктопное приложение для автоматизации управления гостиницей, разработанное на Python. Проект создан как учебный/портфолио, однако основан на реальном опыте работы в гостиничной индустрии и соответствует требованиям российского законодательства (Постановление Правительства РФ №1912 от 2025 г.).

### ✨ Функциональность

- **Управление номерами** — карточки статусов номеров в реальном времени (свободен / занят / уборка)
- **Бронирование** — две формы регистрации: быстрая и полная, с поддержкой раннего заезда и позднего выезда
- **Гости** — список гостей с живым поиском, динамическая обработка типов документов для граждан РФ и иностранцев, валидация возраста с обработкой несовершеннолетних
- **Тарифный редактор** — настройка тарифов, надбавок за ранний/поздний выезд, управление дополнительными услугами
- **Настройки интерфейса** — переключение тем (светлая/тёмная), масштабирование UI, подсказки (tooltips)
- **База данных** — локальное хранилище SQLite: гости, бронирования, доп. услуги, настройки

### 🛠️ Стек технологий

| Компонент | Технология                                  |
|-----------|---------------------------------------------|
| Язык | Python 3.10+                                |
| GUI | CustomTkinter                               |
| База данных | SQLite3                                     |
| Архитектура | Слоистая (database.py, dto.py, defaults.py) |

### 🚀 Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Tati-And/hoteladmin-pro.git
cd hoteladmin-pro

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить приложение
python main.py
```

### 📋 Требования

- Python 3.10 или выше
- Windows 10 / macOS 11+ / Linux (Ubuntu 20.04+)
- Зависимости из `requirements.txt`

### 📁 Структура проекта

```
hoteladmin-pro/
├── main.py              # Точка входа
├── database.py          # Слой работы с БД (SQLite)
├── dto.py               # Data Transfer Objects
├── config.py            # Конфигурация и константы
├── ui/                  # Компоненты интерфейса
│   ├── rooms.py         # Карточки номеров
│   ├── booking.py       # Формы бронирования
│   ├── guests.py        # Список гостей
│   └── settings.py      # Настройки
├── requirements.txt
└── README.md
```

### 🗺️ Планы развития

- [ ] Отчёты и экспорт в Excel/PDF
- [ ] Статистика загруженности по периодам
- [ ] Печать регистрационных карт (по форме)
- [ ] Резервное копирование базы данных
- [ ] Уведомления о выезде

### 👩‍💻 Об авторе

Разработано **Татьяной** — студенткой направления «Информатика и вычислительная техника» (09.03.01) ТУСУРа (Томский государственный университет систем управления и радиоэлектроники), факультет дистанционного обучения.

Проект сочетает академическую работу с реальным опытом в гостиничной индустрии (специалист по работе с гостями).

📬 [GitHub](https://github.com/Tati-And) 

---

<a name="en"></a>
## 🇬🇧 English

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-5C85D6?style=flat)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

**HotelAdmin Pro** is a desktop application for hotel management automation, built with Python. Developed as an academic/portfolio project, it draws on real-world hospitality industry experience and aligns with Russian hotel regulations (Government Decree No. 1912, 2025).

### ✨ Features

- **Room Management** — real-time room status cards (available / occupied / cleaning)
- **Bookings** — quick and full registration forms with early check-in and late check-out support
- **Guests** — searchable guest list with live filtering, dynamic document type handling for Russian and foreign nationals, age validation with minor handling
- **Tariff Editor** — configure rates, early/late surcharges, and additional services
- **UI Settings** — light/dark theme toggle, UI scaling, tooltips
- **Database** — local SQLite storage: guests, bookings, extras, settings

### 🛠️ Tech Stack

| Component | Technology                                 |
|-----------|--------------------------------------------|
| Language | Python 3.10+                               |
| GUI | CustomTkinter                              |
| Database | SQLite3                                    |
| Architecture | Layered (database.py, dto.py, defaults.py) |

### 🚀 Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/Tati-And/hoteladmin-pro.git
cd hoteladmin-pro

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

### 📋 Requirements

- Python 3.10 or higher
- Windows 10 / macOS 11+ / Linux (Ubuntu 20.04+)
- Dependencies listed in `requirements.txt`

### 📁 Project Structure

```
hoteladmin-pro/
├── main.py              # Entry point
├── database.py          # Database layer (SQLite)
├── dto.py               # Data Transfer Objects
├── config.py            # Configuration and constants
├── ui/                  # UI components
│   ├── rooms.py         # Room status cards
│   ├── booking.py       # Booking forms
│   ├── guests.py        # Guest list
│   └── settings.py      # Settings panel
├── requirements.txt
└── README.md
```

### 🗺️ Roadmap

- [ ] Reports and Excel/PDF export
- [ ] Occupancy statistics by period
- [ ] Registration card printing
- [ ] Database backup
- [ ] Check-out notifications

### 👩‍💻 About the Author

Developed by **Tatiana** — a Computer Science and Computer Engineering student (09.03.01) at TUSUR (Tomsk State University of Control Systems and Radioelectronics), Faculty of Distance Learning.

This project combines academic work with real-world hotel industry experience as a Guest Relations Specialist.

📬 [GitHub](https://github.com/Tati-And)

---

*README last updated: June 2026*
