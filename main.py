import tkinter as tk
import keyboard
import time
from tkinter import ttk
import winreg
import os
import sys
from spotify_api import fetch_data, search_and_play, play_track, sp

def add_to_startup(exe_path=None):
    if exe_path is None:
        exe_path = os.path.abspath(sys.argv[0])
    key = winreg.HKEY_CURRENT_USER
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "SpotifyQuickSearch"
    try:
        with winreg.OpenKey(key, reg_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, exe_path)
    except Exception as e:
        print(f"Ошибка добавления в автозагрузку: {e}")

add_to_startup()

def create_gui(root, on_search, on_play, on_close):
    # Основные цвета
    BG_COLOR = "#121212"  # Основной фон
    FG_COLOR = "#FFFFFF"  # Основной текст
    ACCENT_COLOR = "#1DB954"  # Акцентный цвет (Spotify green)
    ENTRY_BG = "#282828"  # Фон поля ввода
    LISTBOX_BG = "#181818"  # Фон списка
    HIGHLIGHT_COLOR = "#535353"  # Цвет выделения

    # Стиль для ttk виджетов
    style = ttk.Style()
    style.theme_use('clam')

    # Настройка стилей
    style.configure("TFrame", background=BG_COLOR)
    style.configure("TEntry",
                    fieldbackground=ENTRY_BG,
                    foreground=FG_COLOR,
                    insertcolor=FG_COLOR,
                    borderwidth=0,
                    relief="flat",
                    padding=5,
                    font=("Segoe UI", 10))
    style.map("TEntry",
              fieldbackground=[("focus", ENTRY_BG)],
              foreground=[("focus", FG_COLOR)])

    # Главный контейнер
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Поле поиска
    search_frame = ttk.Frame(main_frame)
    search_frame.pack(fill=tk.X, pady=(0, 10))

    search_entry = ttk.Entry(search_frame, style="TEntry")
    search_entry.pack(fill=tk.X, ipady=5)
    search_entry.bind("<Return>", lambda e: on_search(search_entry.get()))

    # Список треков
    list_frame = ttk.Frame(main_frame)
    list_frame.pack(fill=tk.BOTH, expand=True)

    # Скроллбар
    scrollbar = tk.Scrollbar(list_frame, bg=BG_COLOR, troughcolor=BG_COLOR)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Список с треками
    liked_box = tk.Listbox(
        list_frame,
        bg=LISTBOX_BG,
        fg=FG_COLOR,
        selectbackground=HIGHLIGHT_COLOR,
        selectforeground=FG_COLOR,
        yscrollcommand=scrollbar.set,
        borderwidth=0,
        highlightthickness=0,
        activestyle="none",
        font=("Segoe UI", 10)
    )
    liked_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=liked_box.yview)

    # Привязка двойного клика
    liked_box.bind("<Double-Button-1>", lambda e: on_play(liked_box))

    # Привязка закрытия по Escape
    root.bind("<Escape>", on_close)

    return search_entry, liked_box

def main():
    root = tk.Tk()
    root.title("Spotify Quick Search")
    root.geometry("400x300")
    root.configure(bg="#121212")
    root.attributes('-alpha', 0.95)
    root.withdraw()

    # Инициализация данных
    liked_list, playlist_list = fetch_data()
    playlists = ["Liked"]

    # GUI callbacks
    def on_search(query):
        # Очищаем список перед поиском
        liked_box.delete(0, tk.END)

        # Обновляем данные перед каждым поиском
        try:
            current_liked, current_playlists = fetch_data()
        except Exception as e:
            print(f"Ошибка обновления данных: {e}")
            current_liked, current_playlists = liked_list, playlist_list

        # Фильтруем результаты
        filtered = search_and_play(query, current_liked, current_playlists, "Liked")

        # Если ровно один результат, воспроизводим его и скрываем окно
        if len(filtered) == 1:
            play_track(filtered[0][1])
            root.withdraw()
            window_visible[0] = False
        # Если больше одного результата, показываем в списке
        elif len(filtered) > 1:
            for name, _ in filtered:
                liked_box.insert(tk.END, name)

    def on_play(box):
        selection = box.curselection()
        if selection:
            index = selection[0]
            item = box.get(index)

            # Обновляем данные перед воспроизведением
            try:
                current_liked, current_playlists = fetch_data()
            except Exception as e:
                print(f"Ошибка обновления данных: {e}")
                current_liked, current_playlists = liked_list, playlist_list

            # Ищем трек в актуальных данных
            for name, uri in current_liked:
                if name == item:
                    play_track(uri)
                    root.withdraw()
                    window_visible[0] = False
                    return

    def on_close(event):
        root.withdraw()
        window_visible[0] = False

    # Создание GUI
    search_entry, liked_box = create_gui(
        root,
        lambda: on_search(search_entry.get()),
        on_play,
        on_close
    )

    # Автоматический поиск при вводе
    def on_key_release(event):
        query = search_entry.get()
        if query:  # Поиск только если есть запрос
            on_search(query)
        else:  # Очищаем список, если запрос пустой
            liked_box.delete(0, tk.END)
            # Заполняем начальными данными при пустом запросе
            for name, _ in liked_list:
                liked_box.insert(tk.END, name)

    search_entry.bind("<KeyRelease>", on_key_release)

    # Горячие клавиши (двойное нажатие Shift)
    window_visible = [False]
    shift_press_times = []
    shift_pressed = [False]

    def on_shift_press(e):
        if shift_pressed[0]:
            return
        shift_pressed[0] = True

        current_time = time.time()
        if shift_press_times and current_time - shift_press_times[-1] < 0.05:
            return

        shift_press_times.append(current_time)
        shift_press_times[:] = shift_press_times[-2:]

        if len(shift_press_times) == 2 and shift_press_times[1] - shift_press_times[0] < 0.3:
            if not window_visible[0]:
                # Обновляем данные при открытии окна
                try:
                    liked_list, playlist_list = fetch_data()
                except Exception as e:
                    print(f"Ошибка обновления данных: {e}")

                root.deiconify()
                window_visible[0] = True
                search_entry.delete(0, tk.END)
                search_entry.focus_set()
                liked_box.delete(0, tk.END)  # Очищаем список
                # Заполняем начальными данными
                for name, _ in liked_list:
                    liked_box.insert(tk.END, name)
            else:
                root.withdraw()
                window_visible[0] = False
            shift_press_times.clear()

    def on_shift_release(e):
        shift_pressed[0] = False

    # Регистрируем нажатие и отпускание
    keyboard.on_press_key("shift", on_shift_press, suppress=False)
    keyboard.on_release_key("shift", on_shift_release, suppress=False)

    # Запуск основного цикла
    root.mainloop()

if __name__ == "__main__":
    main()