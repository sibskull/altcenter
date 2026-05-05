from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication


def point_size_to_pixels(point_size):
    app = QApplication.instance()
    created_app = None

    if app is None:
        created_app = QApplication([])
        app = created_app

    screen = app.primaryScreen()
    if screen is None:
        return 0

    dpi = screen.logicalDotsPerInch()

    # Формула перевода: pixels = (points * dpi) / 72
    return int((point_size * dpi) / 72)


if __name__ == '__main__':
    app = QApplication.instance()
    created_app = None

    if app is None:
        created_app = QApplication([])
        app = created_app

    font = QFont("Arial", 12)
    point_size = font.pointSize()
    pixel_size = point_size_to_pixels(point_size)

    print(f"Размер шрифта: {point_size} поинтов = {pixel_size} пикселей")
