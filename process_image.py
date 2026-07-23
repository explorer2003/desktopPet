#!/usr/bin/env python3
"""
图片背景去除工具
将桌宠.jpg的背景去除，输出带透明通道的character.png
"""

import sys
from pathlib import Path

try:
    from rembg import remove
    from PIL import Image
except ImportError:
    print("请先安装依赖: pip install rembg Pillow")
    sys.exit(1)

# 路径配置
SCRIPT_DIR = Path(__file__).parent.resolve()
INPUT_PATH = SCRIPT_DIR.parent / "桌宠.jpg"  # 桌面的原图
OUTPUT_PATH = SCRIPT_DIR / "character.png"

# 备选：也在当前目录和桌面上找
if not INPUT_PATH.exists():
    INPUT_PATH = SCRIPT_DIR / "桌宠.jpg"
if not INPUT_PATH.exists():
    INPUT_PATH = Path("C:/Users/Dell/Desktop/桌宠.jpg")

if not INPUT_PATH.exists():
    print(f"错误: 找不到源图片")
    print(f"  尝试过: {SCRIPT_DIR.parent / '桌宠.jpg'}")
    print(f"  尝试过: {SCRIPT_DIR / '桌宠.jpg'}")
    print(f"  尝试过: {Path('C:/Users/Dell/Desktop/桌宠.jpg')}")
    print("请将 桌宠.jpg 放到桌面上或本程序同目录下")
    sys.exit(1)

print(f"找到源图片: {INPUT_PATH}")
print("正在去除背景，请稍候...")

try:
    input_img = Image.open(INPUT_PATH)
    output_img = remove(input_img)
    output_img.save(str(OUTPUT_PATH), "PNG")
    print(f"✓ 完成! 已保存到: {OUTPUT_PATH}")
except Exception as e:
    print(f"错误: {e}")
    sys.exit(1)