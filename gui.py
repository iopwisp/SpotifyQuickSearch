import tkinter as tk
import asyncio
from spotify_api import fetch_data, search_and_play, play_track, sp
import keyboard
import time
from tkinter import ttk


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
                    padding=5)
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
    scrollbar = tk.Scrollbar(list_frame)
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
    liked_box.bind("<Double-Button-1>", lambda e: on_play(liked_box, "Liked"))

    # Привязка закрытия по Escape
    root.bind("<Escape>", on_close)

    return search_entry, liked_box


def main():
    root = tk.Tk()
    root.title("Spotify Search")
    root.geometry("400x300")  # Немного больше для удобства
    root.configure(bg="#121212")  # Темный фон
    root.attributes('-alpha', 0.95)  # Легкая прозрачность
    root.withdraw()

    # Загрузка данных
    liked_list, playlist_list = asyncio.run(fetch_data())
    playlists = ["Liked"]

    # GUI callbacks
    def on_search(query):
        liked_box.delete(0, tk.END)
        filtered = search_and_play(query, liked_list, playlist_list, "Liked")

        # Если ровно один результат, воспроизводим его и скрываем окно
        if len(filtered) == 1:
            play_track(filtered[0][1])
            root.withdraw()
            window_visible[0] = False
        # Если больше одного результата, показываем в списке
        elif len(filtered) > 1:
            for name, _ in filtered:
                liked_box.insert(tk.END, name)

    def on_play(box, playlist):
        selection = box.curselection()
        if selection:
            index = selection[0]
            item = box.get(index)
            flat_list = liked_list
            for name, uri in flat_list:
                if name == item:
                    play_track(uri)
                    root.withdraw()
                    window_visible[0] = False
                    break

    def on_close(event):
        root.withdraw()
        window_visible[0] = False

    # Создание GUI
    search_entry, liked_box = create_gui(
        root, lambda: on_search(search_entry.get()), on_play, on_close
    )

    # Автоматический поиск при вводе
    def on_key_release(event):
        on_search(search_entry.get())

    search_entry.bind("<KeyRelease>", on_key_release)

    # Горячие клавиши (двойное нажатие Shift)
    window_visible = [False]
    shift_press_times = []

    def on_shift_press(e):
        current_time = time.time()
        if shift_press_times and current_time - shift_press_times[-1] < 0.05:
            return
        shift_press_times.append(current_time)
        shift_press_times[:] = shift_press_times[-2:]
        if len(shift_press_times) == 2 and shift_press_times[1] - shift_press_times[0] < 0.3:
            if not window_visible[0]:
                root.deiconify()
                window_visible[0] = True
                search_entry.delete(0, tk.END)
                search_entry.focus_set()
            else:
                root.withdraw()
                window_visible[0] = False
            shift_press_times.clear()

    keyboard.on_press_key("shift", on_shift_press, suppress=False)

    # Запуск основного цикла
    root.mainloop()


if __name__ == "__main__":
    main()