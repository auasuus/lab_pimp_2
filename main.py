"""
ЛР 2.1 — Разработка графического интерфейса приложения
Вариант 5: «Фоторедактор»

Окно содержит:
  - QLabel для отображения изображения;
  - QPushButton для загрузки изображения;
  - QComboBox для выбора фильтра;
  - QSlider для регулировки интенсивности фильтра;
  - QLabel для отображения информации об изображении.

Запуск:
    python main.py
"""

import os  # нужен, чтобы получить имя файла из полного пути
import sys  # sys.argv и sys.exit нужны для запуска и завершения приложения
from PyQt6.QtWidgets import (  # импортируем нужные виджеты из PyQt6
    QApplication,  # главный объект приложения (управляет event loop)
    QMainWindow,  # основное окно приложения
    QPushButton,  # кнопка
    QVBoxLayout,  # вертикальный макет (элементы друг под другом)
    QHBoxLayout,  # горизонтальный макет (элементы в ряд)
    QWidget,  # базовый виджет (будет центральным виджетом окна)
    QLabel,  # надпись / область для картинки
    QSlider,  # ползунок
    QComboBox,  # выпадающий список
    QFileDialog,  # стандартный диалог выбора файла
    QMessageBox,  # окно с сообщением (для ошибок)
    QSizePolicy,  # политика изменения размеров виджета
)
from PyQt6.QtCore import Qt  # константы Qt (ориентация слайдера, выравнивание)

import image_utils  # наш модуль: загрузка, фильтры, показ изображения


class MainWindow(QMainWindow):
    """Главное окно приложения «Фоторедактор»."""

    def __init__(self):
        super().__init__()  # вызываем конструктор родителя QMainWindow — без этого окно не заработает
        self.setWindowTitle("Фоторедактор")  # заголовок окна по заданию варианта 5
        self.setGeometry(100, 100, 900, 650)  # x, y, ширина, высота окна (в пикселях)

        self.original_image = None  # здесь будет храниться исходное изображение OpenCV (пока не загружено)
        self.current_file = ""  # путь к текущему загруженному файлу

        self.init_ui()  # строим интерфейс (виджеты, макеты, сигналы)

    def init_ui(self):
        """Инициализация пользовательского интерфейса."""
        central_widget = QWidget()  # создаём центральный виджет — «холст», на котором лежит всё содержимое
        self.setCentralWidget(central_widget)  # назначаем его центральным виджетом главного окна

        main_layout = QVBoxLayout()  # главный вертикальный макет: картинка сверху, панель управления снизу

        # ---------- Область отображения изображения ----------
        self.image_label = QLabel("Загрузите изображение")  # QLabel с подсказкой, пока картинки нет
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # выравниваем содержимое по центру
        self.image_label.setMinimumSize(400, 300)  # минимальный размер области вывода
        self.image_label.setSizePolicy(  # разрешаем QLabel быть меньше, чем загруженная картинка
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        self.image_label.setStyleSheet(  # оформление: рамка и тёмный фон, чтобы область была заметна
            "border: 1px solid gray; background-color: #2b2b2b; color: white;"
        )

        # ---------- Кнопка загрузки и выбор фильтра ----------
        self.load_button = QPushButton("Загрузить изображение")  # кнопка загрузки по заданию варианта
        self.filter_combo = QComboBox()  # выпадающий список фильтров
        self.filter_combo.addItems(image_utils.FILTER_NAMES)  # добавляем пункты: Исходное, Ч/б, Размытие, Яркость

        top_row = QHBoxLayout()  # горизонтальный макет для верхней строки управления
        top_row.addWidget(self.load_button)  # кнопка слева
        top_row.addWidget(QLabel("Фильтр:"))  # подпись к списку (создаётся прямо на месте)
        top_row.addWidget(self.filter_combo)  # выпадающий список справа от подписи

        # ---------- Слайдер интенсивности ----------
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)  # горизонтальный ползунок
        self.intensity_slider.setMinimum(0)  # минимальная интенсивность
        self.intensity_slider.setMaximum(100)  # максимальная интенсивность
        self.intensity_slider.setValue(50)  # стартовое значение — середина шкалы
        self.value_label = QLabel("50")  # надпись с текущим значением слайдера
        self.value_label.setMinimumWidth(30)  # фиксируем ширину, чтобы число «100» не обрезалось

        slider_row = QHBoxLayout()  # горизонтальный макет для строки со слайдером
        slider_row.addWidget(QLabel("Интенсивность:"))  # подпись слева
        slider_row.addWidget(self.intensity_slider, 1)  # слайдер; число 1 — растягивается на всю свободную ширину
        slider_row.addWidget(self.value_label)  # число справа от слайдера

        # ---------- Информационная надпись ----------
        self.info_label = QLabel("Информация: изображение не загружено")  # QLabel для вывода информации

        # ---------- Сборка главного макета ----------
        main_layout.addWidget(self.image_label, 1)  # картинка занимает всё свободное место (растяжение 1)
        main_layout.addLayout(top_row)  # под картинкой — строка с кнопкой и списком
        main_layout.addLayout(slider_row)  # ниже — строка со слайдером
        main_layout.addWidget(self.info_label)  # в самом низу — информация
        central_widget.setLayout(main_layout)  # устанавливаем главный макет на центральный виджет

        # ---------- Подключение сигналов к слотам ----------
        self.load_button.clicked.connect(self.on_button_click)  # клик по кнопке -> загрузка изображения
        self.filter_combo.currentIndexChanged.connect(self.on_combo_select)  # смена пункта списка -> смена фильтра
        self.intensity_slider.valueChanged.connect(self.on_slider_change)  # движение ползунка -> новая интенсивность

        # До загрузки картинки фильтры и слайдер бесполезны — блокируем их
        self.filter_combo.setEnabled(False)  # список фильтров недоступен
        self.intensity_slider.setEnabled(False)  # слайдер недоступен

    def on_button_click(self):
        """Обработчик нажатия кнопки: выбор и загрузка изображения."""
        file_path, _ = QFileDialog.getOpenFileName(  # открываем стандартный диалог выбора файла
            self,  # родительское окно диалога
            "Выбрать изображение",  # заголовок диалога
            "",  # начальная папка (пусто = по умолчанию)
            "Изображения (*.png *.jpg *.jpeg)",  # фильтр: показываем только картинки
        )
        if not file_path:  # пользователь закрыл диалог без выбора файла
            return  # ничего не делаем

        image = image_utils.load_image(file_path)  # пробуем загрузить выбранный файл через OpenCV
        if image is None:  # загрузка не удалась (файл битый или не изображение)
            QMessageBox.warning(  # показываем окно с предупреждением
                self,  # родительское окно
                "Ошибка",  # заголовок окна сообщения
                "Не удалось открыть файл. Возможно, он повреждён или не является изображением.",  # текст ошибки
            )
            return  # прекращаем обработку — старое изображение остаётся как было

        self.original_image = image  # запоминаем исходное изображение
        self.current_file = file_path  # запоминаем путь к файлу
        self.filter_combo.setEnabled(True)  # теперь можно выбирать фильтр
        self.intensity_slider.setEnabled(True)  # и двигать слайдер
        self.statusBar().showMessage("Изображение загружено", 3000)  # сообщение в статус-баре на 3 секунды
        self.update_view()  # перерисовываем картинку и информацию

    def on_slider_change(self, value):
        """Обработчик изменения слайдера."""
        self.value_label.setText(str(value))  # показываем текущее значение рядом со слайдером
        self.update_view()  # пересчитываем фильтр с новой интенсивностью

    def on_combo_select(self, index):
        """Обработчик выбора элемента из списка."""
        self.update_view()  # применяем выбранный фильтр (index нам не нужен — читаем текст из списка)

    def update_view(self):
        """Применяет текущий фильтр и интенсивность и показывает результат."""
        if self.original_image is None:  # если картинка ещё не загружена
            return  # обновлять нечего

        filter_name = self.filter_combo.currentText()  # название выбранного фильтра
        intensity = self.intensity_slider.value()  # текущая интенсивность 0..100
        result = image_utils.apply_filter(self.original_image, filter_name, intensity)  # обработанная копия
        image_utils.display_image(self.image_label, result)  # выводим результат в QLabel

        height, width = self.original_image.shape[:2]  # размеры исходной картинки
        self.info_label.setText(  # обновляем информационную надпись
            f"Файл: {os.path.basename(self.current_file)} | "  # имя файла без пути
            f"Размер: {width}x{height} | "  # ширина x высота
            f"Фильтр: {filter_name} | "  # выбранный фильтр
            f"Интенсивность: {intensity}"  # значение слайдера
        )

    def resizeEvent(self, event):
        """Вызывается Qt при изменении размера окна: перерисовываем картинку под новый размер."""
        super().resizeEvent(event)  # сначала стандартная обработка Qt
        self.update_view()  # затем масштабируем изображение под новый размер области


def main():
    app = QApplication(sys.argv)  # создаём приложение; sys.argv — аргументы командной строки
    window = MainWindow()  # создаём главное окно
    window.show()  # показываем окно на экране
    sys.exit(app.exec())  # запускаем event loop; при закрытии окна завершаем программу с кодом выхода


if __name__ == '__main__':  # выполняется только при запуске файла напрямую (python main.py)
    main()  # запускаем приложение
