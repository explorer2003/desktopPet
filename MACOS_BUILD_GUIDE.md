# 🍎 macOS 打包完整教程

## 概述

用 GitHub Actions（免费）在云端 macOS 上自动构建 `.dmg` 安装包，发给朋友直接安装使用。

---

## 第一步：把代码推送到 GitHub

### 1.1 在项目目录初始化 Git

打开终端（或 Git Bash），进入项目目录，执行：

```bash
cd "C:\Users\Dell\Desktop\桌宠宠物"
git init
```

### 1.2 创建 `.gitignore` 文件

（避免把构建产物、临时文件推上去）

```bash
echo "build/" >> .gitignore
echo "dist/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "*.spec" >> .gitignore
echo "pet_config.json" >> .gitignore
```

### 1.3 提交并推送

```bash
git add .
git commit -m "桌宠 - 桌面宠物应用"
git branch -M main
git remote add origin https://github.com/你的用户名/桌宠.git
git push -u origin main
```

> 还没 GitHub 账号？去 [github.com](https://github.com) 免费注册一个，然后创建新仓库。

---

## 第二步：配置 GitHub Actions 自动打包

在项目根目录创建 `.github/workflows/build-macos.yml`，内容如下：

```yaml
name: 打包 macOS 版本

on:
  push:
    branches: [main]
  workflow_dispatch:  # 允许手动触发

jobs:
  build-macos:
    runs-on: macos-latest

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 安装 Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 安装依赖
        run: |
          pip install pyinstaller PyQt5

      - name: PyInstaller 打包
        run: |
          pyinstaller \
            --onefile \
            --windowed \
            --name "桌宠" \
            --hidden-import PyQt5.QtCore \
            --hidden-import PyQt5.QtGui \
            --hidden-import PyQt5.QtWidgets \
            --osx-bundle-identifier com.zhuochong.pet \
            pet.py

      - name: 创建 DMG 安装包
        run: |
          # 准备 DMG 目录结构
          mkdir -p dmg_contents
          cp -R dist/桌宠.app dmg_contents/
          # 创建 Applications 快捷方式
          ln -s /Applications dmg_contents/Applications
          # 打包为 DMG
          hdiutil create \
            -volname "桌宠" \
            -srcfolder dmg_contents \
            -ov \
            -format UDZO \
            桌宠-macOS.dmg

      - name: 上传构建产物
        uses: actions/upload-artifact@v4
        with:
          name: 桌宠-macOS
          path: 桌宠-macOS.dmg
          retention-days: 90
```

---

## 第三步：下载 DMG

1. 推送代码后，打开 GitHub 仓库页面
2. 点击顶部 **Actions** 标签
3. 看到 `打包 macOS 版本` 工作流运行（黄色圆点 → 绿色勾）
4. 点进去，拉到页面底部 **Artifacts** 区域
5. 点击 `桌宠-macOS.dmg` 下载

把 `.dmg` 发给朋友即可。

---

## 第四步：朋友如何安装

1. 双击 `.dmg` 打开
2. 把 `桌宠.app` 拖到 `Applications` 文件夹
3. 首次打开时按住 **Control** 点击 → 选「打开」（因为未签名）
4. 把喜欢的图片和 `桌宠.app` 放一起，或拖拽到图标上

---

## 补充：让 macOS 版体验更好（可选）

在 `pet.py` 的 `_setup_window` 方法中加一行，让宠物不抢焦点：

```python
def _setup_window(self):
    self.setWindowFlags(
        Qt.FramelessWindowHint |
        Qt.WindowStaysOnTopHint |
        Qt.Tool |
        Qt.WindowDoesNotAcceptFocus   # ← 加这行
    )
    self.setAttribute(Qt.WA_TranslucentBackground)
    self.setAttribute(Qt.WA_ShowWithoutActivating)  # ← 加这行
    self.setScaledContents(True)
```

---

## 文件结构确认

推送前你的项目目录应该长这样：

```
桌宠宠物/
├── pet.py
├── requirements.txt
├── process_image.py      (可选)
├── setup.bat             (可选)
├── build.bat             (可选)
├── .gitignore
└── .github/
    └── workflows/
        └── build-macos.yml
```