"""
ЛР 2.1 — Разработка графического интерфейса приложения
Вариант 5: «Фоторедактор»

Модуль image_utils.py — вспомогательные функции для работы с изображениями:
  - загрузка файла в формат OpenCV;
  - применение фильтров (Ч/б, Размытие, Яркость) с регулируемой интенсивностью;
  - преобразование OpenCV (BGR) -> QPixmap (RGB) для показа в окне;
  - отображение картинки в QLabel с сохранением пропорций.
"""

import os  # модуль для проверки существования файла на диске
import cv2  # OpenCV: чтение и обработка изображений
import numpy as np  # NumPy: OpenCV хранит картинки как массивы NumPy
from PyQt6.QtGui import QPixmap, QImage  # QImage — картинка в памяти, QPixmap — для показа на экране
from PyQt6.QtCore import Qt  # Qt содержит константы (режимы масштабирования и т.п.)


# Список фильтров. Порядок здесь = порядок пунктов в выпадающем списке (QComboBox)
FILTER_NAMES = ["Исходное", "Ч/б", "Размытие", "Яркость"]


def load_image(file_path):
    """
    Загружает изображение из файла.

    :param file_path: путь к файлу изображения
    :return: изображение в формате OpenCV (NumPy array) или None, если не удалось
    """
    if not file_path or not os.path.isfile(file_path):  # путь пустой или файла нет на диске?
        return None  # сообщаем вызывающему коду, что загрузка не удалась
    try:  # оборачиваем чтение в try, чтобы повреждённый файл не "ронял" программу
        # cv2.imread не умеет читать пути с кириллицей на Windows (например, C:\Users\Иван\...),
        # поэтому читаем байты файла через NumPy и декодируем их сами через cv2.imdecode
        data = np.fromfile(file_path, dtype=np.uint8)  # читаем весь файл как массив байтов
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)  # декодируем байты в цветную картинку BGR
    except Exception:  # любая ошибка чтения (нет прав, файл битый и т.д.)
        return None  # считаем, что изображение загрузить нельзя
    return image  # вернётся массив, либо None, если imdecode не смог разобрать файл


def apply_filter(image, filter_name, intensity):
    """
    Применяет выбранный фильтр к изображению.

    :param image: исходное изображение OpenCV (BGR)
    :param filter_name: название фильтра из FILTER_NAMES
    :param intensity: интенсивность 0..100 (значение слайдера)
    :return: новое обработанное изображение (исходное не изменяется)
    """
    if filter_name == "Ч/б":  # фильтр «чёрно-белое»
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # переводим картинку в оттенки серого (1 канал)
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)  # возвращаем 3 канала, чтобы можно было смешать с оригиналом
        alpha = intensity / 100.0  # доля серого в итоге: 0.0 — оригинал, 1.0 — полностью ч/б
        # addWeighted считает: image*(1-alpha) + gray_bgr*alpha — плавный переход цвет -> ч/б
        return cv2.addWeighted(image, 1.0 - alpha, gray_bgr, alpha, 0)  # возвращаем смешанное изображение

    if filter_name == "Размытие":  # фильтр «размытие по Гауссу»
        kernel = 1 + 2 * (intensity // 5)  # размер ядра должен быть НЕЧЁТНЫМ: 1, 3, 5, ... до 41
        return cv2.GaussianBlur(image, (kernel, kernel), 0)  # чем больше ядро, тем сильнее размытие

    if filter_name == "Яркость":  # фильтр «яркость»
        beta = (intensity - 50) * 2  # слайдер 50 = без изменений; 0 -> -100 (темнее); 100 -> +100 (светлее)
        # convertScaleAbs считает image*alpha + beta и ограничивает результат диапазоном 0..255
        return cv2.convertScaleAbs(image, alpha=1.0, beta=beta)  # возвращаем изменённую по яркости картинку

    return image.copy()  # «Исходное» (или неизвестный фильтр): возвращаем копию без изменений


def opencv_to_qt_image(cv_image):
    """
    Преобразует изображение из OpenCV в QPixmap.

    :param cv_image: изображение в формате OpenCV (NumPy array)
    :return: QPixmap для отображения в Qt
    """
    rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)  # OpenCV хранит BGR, а Qt ждёт RGB — меняем порядок каналов
    h, w, channels = rgb_image.shape  # высота, ширина и число каналов массива
    bytes_per_line = channels * w  # байт в одной строке пикселей (3 канала * ширина)
    qimage = QImage(  # создаём QImage прямо поверх данных массива
        rgb_image.data,  # указатель на байты пикселей
        w,  # ширина изображения
        h,  # высота изображения
        bytes_per_line,  # длина строки в байтах (нужна Qt для правильного чтения)
        QImage.Format.Format_RGB888,  # формат: 8 бит на канал, порядок R, G, B
    )
    return QPixmap.fromImage(qimage)  # QPixmap.fromImage копирует данные, поэтому массив можно безопасно освободить


def display_image(label, cv_image):
    """
    Отображает изображение в QLabel с сохранением пропорций.

    :param label: QLabel для отображения
    :param cv_image: изображение в формате OpenCV
    """
    pixmap = opencv_to_qt_image(cv_image)  # конвертируем OpenCV-картинку в QPixmap
    scaled = pixmap.scaled(  # масштабируем под размер области вывода
        label.width(),  # доступная ширина QLabel
        label.height(),  # доступная высота QLabel
        Qt.AspectRatioMode.KeepAspectRatio,  # сохраняем пропорции (картинка не искажается)
        Qt.TransformationMode.SmoothTransformation,  # сглаживание при масштабировании — качество лучше
    )
    label.setPixmap(scaled)  # показываем готовую картинку в QLabel
