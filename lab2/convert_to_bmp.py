"""
Допоміжний скрипт: конвертує будь-яке зображення (JPEG, PNG, або файл
з "неправильним" розширенням типу .bmp, що насправді є JPEG) у справжній
24-бітний BMP-файл, придатний для завантаження в основну програму.

Використання:
    python convert_to_bmp.py шлях/до/картинки.jpg шлях/до/результату.bmp

Якщо другий аргумент не вказано, результат зберігається поруч із вхідним
файлом, з тим самим іменем і розширенням .bmp (наприклад photo.jpg -> photo.bmp).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def convert_to_real_bmp(src_path: str, dst_path: str | None = None) -> str:
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(f"Файл не знайдено: {src}")

    img = Image.open(src)
    print(f"Вхідний файл: {src}")
    print(f"  Формат за вмістом: {img.format}, розмір: {img.size}, режим: {img.mode}")

    img = img.convert("RGB")

    if dst_path is None:
        dst = src.with_suffix(".bmp")
        if dst == src:
            dst = src.with_name(src.stem + "_real.bmp")
    else:
        dst = Path(dst_path)

    img.save(dst, format="BMP")
    print(f"Збережено справжній 24-бітний BMP: {dst}")
    return str(dst)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Використання: python convert_to_bmp.py шлях/до/картинки [шлях/до/результату.bmp]")
        sys.exit(1)

    src_arg = sys.argv[1]
    dst_arg = sys.argv[2] if len(sys.argv) > 2 else None
    convert_to_real_bmp(src_arg, dst_arg)