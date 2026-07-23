#!/usr/bin/env python3
"""
Windows 桌面宠物 (桌宠)
一个可爱的交互式桌面伙伴，支持拖动、点击互动、对话气泡、缩放等功能。
"""

import sys
import json
import random
import os
import math
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QMenu, QAction,
                              QFileDialog, QInputDialog, QMessageBox)
from PyQt5.QtCore import (Qt, QPropertyAnimation, QPoint, QEasingCurve,
                          QTimer, QRect, QRectF, QSize)
from PyQt5.QtGui import (QPixmap, QPainter, QColor, QFont, QPainterPath,
                         QBrush, QPen, QFontMetrics)


# ============================================================
# 资源路径工具
# ============================================================
def get_base_dir():
    """获取程序所在目录（兼容开发环境和PyInstaller打包后的EXE）"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.resolve()


def resource_path(relative_path):
    """获取资源文件的绝对路径（兼容PyInstaller打包）"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = str(get_base_dir())
    return os.path.join(base_path, relative_path)


# ============================================================
# 常量
# ============================================================
BASE_DIR = get_base_dir()
CONFIG_FILE = str(BASE_DIR / "pet_config.json")
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')


def find_images_in_dir(directory):
    """扫描目录下所有图片文件，返回按文件名排序的路径列表"""
    images = []
    try:
        for f in os.listdir(directory):
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                images.append(os.path.join(directory, f))
    except OSError:
        pass
    return sorted(images)


def _save_image_to_config(image_path):
    """将图片路径写入配置文件（保留已有字段）"""
    cfg = {}
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
    except Exception:
        pass
    cfg['image_path'] = image_path
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def resolve_character_image():
    """
    多级优先级解析角色图片路径：
      1. 命令行参数（拖拽图片到 EXE）
      2. 配置文件记录的 image_path
      3. 自动扫描 EXE 同目录下的图片
      4. 弹出文件选择对话框
    返回图片路径，或 None（用户取消）
    """
    # 1. 命令行参数（拖拽图片到 EXE 上）
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if os.path.isfile(arg_path) and arg_path.lower().endswith(SUPPORTED_EXTENSIONS):
            return arg_path

    # 2. 配置文件中记录的图片路径
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            saved = cfg.get('image_path', '')
            if saved and os.path.isfile(saved):
                return saved
        except Exception:
            pass

    # 3. 自动扫描 EXE 同目录下的图片文件
    images = find_images_in_dir(str(BASE_DIR))
    if len(images) == 1:
        return images[0]
    elif len(images) > 1:
        # 多张图片 → 弹出选择列表
        names = [os.path.basename(p) for p in images]
        item, ok = QInputDialog.getItem(
            None, "选择宠物图片",
            "检测到同目录下有多张图片，请选择一张作为宠物：",
            names, 0, False
        )
        if ok and item:
            return images[names.index(item)]
        # 用户取消了 → 继续走文件选择对话框

    # 4. 弹出文件选择对话框
    path, _ = QFileDialog.getOpenFileName(
        None, "选择宠物图片", str(BASE_DIR),
        "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;所有文件 (*.*)"
    )
    if path and os.path.isfile(path):
        return path

    return None

# 中文互动短语
PHRASES = [
    "别戳我~",
    "嘻嘻！",
    "好痒呀！",
    "哎呀！",
    "干嘛啦~",
    "哼！",
    "哇！",
    "嘿嘿~",
    "再来一次！",
    "好开心！",
    "你好呀！",
    "今天真好~",
    "吃饭了吗？",
    "陪我玩嘛！",
    "略略略~",
    "好困呀...",
    "加油！",
    "最喜欢你啦！",
    "诶嘿~",
    "你真好！",
    "呜哇！",
    "不要嘛~",
    "好舒服~",
    "嘿嘿嘿！",
]


# ============================================================
# 对话气泡
# ============================================================
class SpeechBubble(QWidget):
    """浮在角色上方的对话气泡"""

    BUBBLE_COLOR = QColor(255, 255, 255, 245)
    BORDER_COLOR = QColor(180, 180, 180, 220)
    TEXT_COLOR = QColor(70, 70, 70)
    TRIANGLE_H = 10
    PAD_H = 18
    PAD_V = 10
    RADIUS = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._text = ""
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._on_hide)
        self._on_hide_callback = None

        self._font = QFont("Microsoft YaHei", 13)
        self._font.setBold(True)

    def set_hide_callback(self, callback):
        """设置气泡隐藏时的回调（用于停止追踪定时器）"""
        self._on_hide_callback = callback

    def _on_hide(self):
        """气泡隐藏，同时通知外部停止追踪"""
        self.hide()
        if self._on_hide_callback:
            self._on_hide_callback()

    def show_text(self, text, target_global_pos, pet_width, pet_height):
        """显示气泡，定位在目标上方"""
        is_new_text = (text != self._text)
        self._text = text
        self._calc_size()

        # 气泡位置：底部中心对准角色顶部中心
        bx = target_global_pos.x() + pet_width // 2 - self.width() // 2
        # 偏移量根据宠物大小动态调整
        offset = max(3, int(pet_height * 0.06))
        by = target_global_pos.y() - self.height() - offset

        # 确保不超出屏幕
        screen = QApplication.primaryScreen().availableGeometry()
        if bx + self.width() > screen.right():
            bx = screen.right() - self.width() - 2
        if bx < screen.left():
            bx = screen.left() + 2
        if by < screen.top():
            # 如果上方空间不够，放到宠物下方
            by = target_global_pos.y() + pet_height + offset

        self.move(bx, by)
        self.show()
        # 只在文字变化或定时器未激活时重启倒计时，避免追踪更新刷掉定时器
        if is_new_text or not self._hide_timer.isActive():
            self._hide_timer.start(5000)

    def _calc_size(self):
        fm = QFontMetrics(self._font)
        tw = fm.horizontalAdvance(self._text) + self.PAD_H * 2
        th = fm.height() + self.PAD_V * 2 + self.TRIANGLE_H
        self.setFixedSize(max(tw, 70), th)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height() - self.TRIANGLE_H
        r = self.RADIUS

        # 气泡主体
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)

        # 底部三角
        cx = w // 2
        path.moveTo(cx - 8, h)
        path.lineTo(cx, h + self.TRIANGLE_H)
        path.lineTo(cx + 8, h)
        path.closeSubpath()

        painter.setBrush(QBrush(self.BUBBLE_COLOR))
        painter.setPen(QPen(self.BORDER_COLOR, 1.5))
        painter.drawPath(path)

        painter.setFont(self._font)
        painter.setPen(self.TEXT_COLOR)
        painter.drawText(QRectF(self.PAD_H, self.PAD_V,
                                w - self.PAD_H * 2, h - self.PAD_V * 2),
                         Qt.AlignCenter, self._text)
        painter.end()


# ============================================================
# 桌面宠物主体
# ============================================================
class PetWidget(QLabel):
    """桌面宠物主窗口"""

    def __init__(self, image_path):
        super().__init__()

        self._image_path = image_path
        # 加载图片
        self._base_pixmap = QPixmap(image_path)
        if self._base_pixmap.isNull():
            raise FileNotFoundError(
                f"无法加载图片:\n{image_path}\n\n"
                "请确认图片文件未被损坏"
            )

        self._scale = 1.0
        self._always_on_top = True
        self._drag_offset = None
        self._press_pos = None
        self._is_dragging = False
        self._is_animating = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_config)

        # 对话气泡
        self._bubble = SpeechBubble()
        self._bubble.set_hide_callback(self._stop_bubble_track)

        # 悬浮状态
        self._is_floating = False
        self._float_base_y = 0
        self._float_phase = 0.0

        # 初始化窗口
        self._setup_window()
        self._apply_scale()

        # 加载配置
        self._load_config()

        self.show()

    # ---- 窗口设置 ----
    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setScaledContents(True)

    def _apply_scale(self):
        """应用缩放"""
        new_size = self._base_pixmap.size() * self._scale
        self.setPixmap(self._base_pixmap.scaled(
            new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.resize(new_size)
        self._update_mask()

    def _update_mask(self):
        """更新窗口遮罩，让透明区域可穿透鼠标"""
        if self.pixmap() and not self.pixmap().isNull():
            self.setMask(self.pixmap().mask())

    # ---- 缩放控制 ----
    def set_scale(self, scale):
        self._scale = max(0.05, min(3.0, scale))
        self._apply_scale()
        self._save_config()

    def scale_by(self, delta):
        self.set_scale(self._scale * (1.0 + delta))

    # ---- 鼠标事件 ----
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPos()
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self._is_dragging = False
            # 停止浮动，避免与动画冲突
            self._stop_floating()
            # 隐藏正在显示的气泡
            self._bubble.hide()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_offset is not None:
            dist = (event.globalPos() - self._press_pos).manhattanLength()
            if dist > 5:
                self._is_dragging = True
            if self._is_dragging:
                new_pos = event.globalPos() - self._drag_offset
                self.move(new_pos)
                # 拖动时始终更新浮动基准，防止后续跳回原位
                self._float_base_y = new_pos.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self._is_dragging and not self._is_animating:
                self._interact()
            self._is_dragging = False
            self._drag_offset = None
            self._press_pos = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.scale_by(0.06 if delta > 0 else -0.06)

    def enterEvent(self, event):
        """鼠标进入宠物区域：弹出气泡 + 开始浮动"""
        self._show_bubble(random.choice(PHRASES))
        self._start_floating()

    def leaveEvent(self, event):
        """鼠标离开宠物区域：停止浮动"""
        self._stop_floating()

    # ---- 悬浮动画 ----
    def _start_floating(self):
        if self._is_floating:
            return
        self._is_floating = True
        self._float_base_y = self.y()
        self._float_phase = 0.0
        if not hasattr(self, '_float_timer'):
            self._float_timer = QTimer(self)
            self._float_timer.timeout.connect(self._float_tick)
        self._float_timer.start(33)  # ~30fps

    def _float_tick(self):
        self._float_phase += 0.12
        offset = int(math.sin(self._float_phase) * 12)
        self.move(self.x(), self._float_base_y + offset)

    def _stop_floating(self):
        self._is_floating = False
        if hasattr(self, '_float_timer'):
            self._float_timer.stop()
        # 回到原位
        if hasattr(self, '_float_base_y'):
            self.move(self.x(), self._float_base_y)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #fff;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 4px;
                font-family: "Microsoft YaHei";
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 28px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #e8e8e8;
            }
        """)

        # 调整大小子菜单
        size_menu = QMenu("调整大小", menu)
        for pct in [50, 75, 100, 125, 150, 200]:
            act = size_menu.addAction(f"{pct}%")
            act.triggered.connect(lambda checked, p=pct: self.set_scale(p / 100.0))
        menu.addMenu(size_menu)

        menu.addSeparator()

        # 置顶开关
        top_act = QAction("窗口置顶", menu)
        top_act.setCheckable(True)
        top_act.setChecked(self._always_on_top)
        top_act.triggered.connect(self._toggle_top)
        menu.addAction(top_act)

        menu.addSeparator()

        # 更换图片
        change_act = QAction("更换图片", menu)
        change_act.triggered.connect(self._change_image)
        menu.addAction(change_act)

        menu.addSeparator()

        # 退出
        exit_act = QAction("退出程序", menu)
        exit_act.triggered.connect(QApplication.quit)
        menu.addAction(exit_act)

        menu.exec_(event.globalPos())

    # ---- 互动 ----
    def _interact(self):
        self._stop_floating()
        actions = [self._anim_jump, self._anim_squash, self._anim_shake]
        random.choice(actions)()
        QTimer.singleShot(120, lambda: self._show_bubble(random.choice(PHRASES)))

    def _show_bubble(self, text):
        self._bubble_text = text
        self._update_bubble_pos()
        # 动画期间持续跟踪位置
        if not hasattr(self, '_bubble_track_timer'):
            self._bubble_track_timer = QTimer(self)
            self._bubble_track_timer.timeout.connect(self._update_bubble_pos)
        self._bubble_track_timer.start(25)

    def _update_bubble_pos(self):
        if not self._bubble.isVisible() and not hasattr(self, '_bubble_text'):
            return
        top_center = self.mapToGlobal(QPoint(self.width() // 2, 0))
        self._bubble.show_text(getattr(self, '_bubble_text', ''), top_center, self.width(), self.height())

    def _stop_bubble_track(self):
        if hasattr(self, '_bubble_track_timer'):
            self._bubble_track_timer.stop()

    # ---- 动画 ----
    def _on_anim_done(self):
        """动画结束后的统一收尾"""
        self._is_animating = False
        self._stop_bubble_track()
        # 如果鼠标仍在宠物上，恢复浮动
        if self.underMouse():
            self._start_floating()

    def _anim_jump(self):
        """跳跃动画"""
        self._is_animating = True
        orig = self.pos()
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(520)
        anim.setStartValue(orig)
        anim.setKeyValueAt(0.0, orig)
        anim.setKeyValueAt(0.18, orig + QPoint(0, -110))
        anim.setKeyValueAt(0.36, orig + QPoint(0, -130))
        anim.setKeyValueAt(0.54, orig + QPoint(0, -110))
        anim.setKeyValueAt(0.72, orig + QPoint(0, -25))
        anim.setEndValue(orig)
        anim.setEasingCurve(QEasingCurve.OutBounce)
        anim.finished.connect(self._on_anim_done)
        anim.start()
        self._current_anim = anim

    def _anim_squash(self):
        """压扁回弹动画"""
        self._is_animating = True
        geo = self.geometry()
        bw, bh = geo.width(), geo.height()

        # 压扁状态：更宽更矮
        s_w = int(bw * 1.25)
        s_h = int(bh * 0.6)
        s_x = geo.x() - (s_w - bw) // 2
        s_y = geo.y() + bh - s_h
        squashed = QRect(s_x, s_y, s_w, s_h)

        # 拉伸状态：更窄更高
        t_w = int(bw * 0.8)
        t_h = int(bh * 1.15)
        t_x = geo.x() - (t_w - bw) // 2
        t_y = geo.y() - (t_h - bh)
        stretched = QRect(t_x, t_y, t_w, t_h)

        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(550)
        anim.setStartValue(geo)
        anim.setKeyValueAt(0.0, geo)
        anim.setKeyValueAt(0.25, squashed)
        anim.setKeyValueAt(0.5, stretched)
        anim.setKeyValueAt(0.75, squashed)
        anim.setEndValue(geo)
        anim.setEasingCurve(QEasingCurve.OutElastic)
        anim.finished.connect(self._on_anim_done)
        anim.start()
        self._current_anim = anim

    def _anim_shake(self):
        """左右抖动动画"""
        self._is_animating = True
        orig = self.pos()
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(420)
        anim.setStartValue(orig)
        # 振幅从大到小衰减
        keyframes = [
            (0.0, 0), (0.08, -18), (0.16, 18), (0.24, -14),
            (0.32, 14), (0.40, -10), (0.48, 10), (0.56, -6),
            (0.64, 6), (0.72, -3), (0.80, 3), (0.88, -1), (1.0, 0)
        ]
        for t, dx in keyframes:
            anim.setKeyValueAt(t, orig + QPoint(dx, 0))
        anim.setEndValue(orig)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(self._on_anim_done)
        anim.start()
        self._current_anim = anim

    # ---- 置顶切换 ----
    def _toggle_top(self, checked):
        self._always_on_top = checked
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self._update_mask()
        self.show()
        self._save_config()

    # ---- 更换图片 ----
    def _change_image(self):
        """弹出文件对话框，让用户选择一张新图片"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择宠物图片", os.path.dirname(self._image_path),
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;所有文件 (*.*)"
        )
        if not path or not os.path.isfile(path):
            return

        new_pixmap = QPixmap(path)
        if new_pixmap.isNull():
            QMessageBox.warning(self, "加载失败", f"无法加载该图片:\n{path}")
            return

        self._image_path = path
        self._base_pixmap = new_pixmap
        self._apply_scale()
        self._save_config()

    # ---- 配置持久化 ----
    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self._scale = cfg.get('scale', 1.0)
                self._apply_scale()
                if 'x' in cfg and 'y' in cfg:
                    self.move(cfg['x'], cfg['y'])
                else:
                    self._default_position()
                if not cfg.get('always_on_top', True):
                    self._toggle_top(False)
            else:
                self._default_position()
        except Exception:
            self._default_position()

    def _default_position(self):
        """默认位置：屏幕右下角"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 40
        y = screen.bottom() - self.height() - 40
        self.move(x, y)

    def _save_config(self):
        try:
            cfg = {
                'x': self.x(),
                'y': self.y(),
                'scale': self._scale,
                'always_on_top': self._always_on_top,
                'image_path': self._image_path,
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def moveEvent(self, event):
        super().moveEvent(event)
        self._save_timer.start(500)  # 防抖


# ============================================================
# 入口
# ============================================================
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 多级优先级解析图片路径
    image_path = resolve_character_image()
    if not image_path:
        # 用户取消了所有选择，静默退出
        sys.exit(0)

    # 记住本次选择的图片路径
    _save_image_to_config(image_path)

    try:
        pet = PetWidget(image_path)
    except FileNotFoundError as e:
        QMessageBox.critical(None, "加载失败", str(e))
        sys.exit(1)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()