from rembg import remove
from PIL import Image
import warnings, os
warnings.filterwarnings('ignore')

os.chdir(r'C:\Users\Dell\Desktop\桌宠宠物')
print('正在去除背景...')
img = Image.open(r'C:\Users\Dell\Desktop\桌宠.jpg')
print(f'图片尺寸: {img.size}')
out = remove(img)
out.save('character.png', 'PNG')
print('完成! character.png 已保存')