import ctypes
from ctypes import wintypes as W
import os
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor, QPainter, QPixmap, QTransform
from PySide6.QtWidgets import QApplication, QLabel, QMenu

ASSETS = Path(__file__).resolve().parent / "assets"
SCALE = 3
SPEED = 110
FRAME_SECONDS = 0.10
ART_FACES_RIGHT = True
GRAVITY = 1100
JUMP_SPEED = 440
PAW_OFFSET = 0  # Scaled screen pixels of transparent padding below the paws.


class WindowPlatforms:
    def __init__(self):
        self.items = []
        self.u = ctypes.WinDLL("user32", use_last_error=True)
        self.d = ctypes.WinDLL("dwmapi", use_last_error=True)
        self.callback_type = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
        self.u.EnumWindows.argtypes = [self.callback_type, W.LPARAM]
        self.u.EnumWindows.restype = W.BOOL
        for name in ("IsWindowVisible", "IsIconic", "IsZoomed"):
            f = getattr(self.u, name)
            f.argtypes = [W.HWND]
            f.restype = W.BOOL
        self.u.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
        self.u.GetWindowThreadProcessId.restype = W.DWORD
        self.u.GetClassNameW.argtypes = [W.HWND, W.LPWSTR, ctypes.c_int]
        self.u.GetClassNameW.restype = ctypes.c_int
        self.u.GetWindowRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
        self.u.GetWindowRect.restype = W.BOOL
        self.u.MonitorFromWindow.argtypes = [W.HWND, W.DWORD]
        self.u.MonitorFromWindow.restype = W.HANDLE
        self.u.GetMonitorInfoW.argtypes = [W.HANDLE, ctypes.c_void_p]
        self.u.GetMonitorInfoW.restype = W.BOOL
        self.d.DwmGetWindowAttribute.argtypes = [W.HWND, W.DWORD, ctypes.c_void_p, W.DWORD]
        self.d.DwmGetWindowAttribute.restype = ctypes.c_long

    def refresh(self):
        class MonitorInfo(ctypes.Structure):
            _fields_ = [("cbSize", W.DWORD), ("rcMonitor", W.RECT),
                        ("rcWork", W.RECT), ("dwFlags", W.DWORD),
                        ("szDevice", W.WCHAR * 32)]
        screens = {s.name().lower(): s for s in QApplication.screens()}
        items = []

        def visit(hwnd, _):
            u = self.u
            if not u.IsWindowVisible(hwnd) or u.IsIconic(hwnd):
                return True
            pid = W.DWORD()
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == os.getpid():
                return True
            name = ctypes.create_unicode_buffer(256)
            u.GetClassNameW(hwnd, name, 256)
            if name.value in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
                return True
            cloaked = W.DWORD()
            if (self.d.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked),
                    ctypes.sizeof(cloaked)) == 0 and cloaked.value):
                return True
            rect = W.RECT()
            if self.d.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)) != 0:
                if not u.GetWindowRect(hwnd, ctypes.byref(rect)):
                    return True
            if rect.right <= rect.left or rect.bottom <= rect.top:
                return True
            info = MonitorInfo()
            info.cbSize = ctypes.sizeof(info)
            if not u.GetMonitorInfoW(u.MonitorFromWindow(hwnd, 2), ctypes.byref(info)):
                return True
            screen = screens.get(info.szDevice.lower())
            if screen is None:
                return True
            g, ratio = screen.geometry(), screen.devicePixelRatio()
            items.append({
                "id": int(hwnd),
                "left": g.x() + (rect.left - info.rcMonitor.left) / ratio,
                "right": g.x() + (rect.right - info.rcMonitor.left) / ratio,
                "top": g.y() + (rect.top - info.rcMonitor.top) / ratio,
                "bottom": g.y() + (rect.bottom - info.rcMonitor.top) / ratio,
                "perch": not bool(u.IsZoomed(hwnd)),
            })
            return True

        callback = self.callback_type(visit)
        self.u.EnumWindows(callback, 0)
        self.items = items

    def exposed(self, window, x):
        y = window["top"] + 2
        for item in self.items:
            if item["id"] == window["id"]:
                return True
            if item["left"] <= x < item["right"] and item["top"] <= y < item["bottom"]:
                return False
        return False


class DesktopCat(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sidekick")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        raw = {name: self.load_frames(filename, count) for name, filename, count in (
            ("idle", "1_Cat_Idle-Sheet.png", 8),
            ("run", "2_Cat_Run-Sheet.png", 10),
            ("jump", "3_Cat_Jump-Sheet.png", 4),
            ("fall", "4_Cat_Fall-Sheet.png", 4))}
        width = max(f.width() for frames in raw.values() for f in frames)
        height = max(f.height() for frames in raw.values() for f in frames)
        self.frames = {}
        for state, frames in raw.items():
            normal = []
            for frame in frames:
                canvas = QPixmap(width, height)
                canvas.fill(Qt.GlobalColor.transparent)
                painter = QPainter(canvas)
                painter.drawPixmap((width - frame.width()) // 2, height - frame.height(), frame)
                painter.end()
                normal.append(canvas)
            mirrored = [f.transformed(QTransform().scale(-1, 1)) for f in normal]
            self.frames[state] = {1: normal if ART_FACES_RIGHT else mirrored,
                                  -1: mirrored if ART_FACES_RIGHT else normal}
        self.setFixedSize(width, height)
        self.state, self.direction, self.frame_index = "idle", 1, 0
        self.frame_elapsed = 0.0
        self.drag_offset = None
        self.wandering = True
        self.follow_cursor = False
        self.auto_hops = True
        self.window_perching = True
        self.menu_open = False
        self.airborne = False
        self.velocity_y = 0.0
        self.support = None
        self.platforms = WindowPlatforms()
        self.platforms.refresh()
        self.next_scan = 0.0
        b = QApplication.primaryScreen().availableGeometry()
        self.float_x = float(b.x() + (b.width() - width) // 2)
        self.float_y = float(b.bottom() + 1 - self.foot_height())
        self.target_x = self.float_x
        self.move(round(self.float_x), round(self.float_y))
        now = time.monotonic()
        self.next_action, self.next_hop, self.last_tick = now + 2, now + random.uniform(8, 16), now
        self.draw_frame()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def foot_height(self):
        return self.height() - PAW_OFFSET

    def load_frames(self, filename, count):
        path = ASSETS / filename
        sheet = QPixmap(str(path))
        if sheet.isNull():
            raise FileNotFoundError(f"Couldn't load: {path}")
        if sheet.width() % count:
            raise ValueError(f"{filename}: width must divide into {count} frames")
        width, height = sheet.width() // count, sheet.height()
        return [sheet.copy(i * width, 0, width, height).scaled(
            width * SCALE, height * SCALE, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation) for i in range(count)]

    def set_state(self, state):
        if self.state != state:
            self.state, self.frame_index, self.frame_elapsed = state, 0, 0.0
        self.draw_frame()

    def draw_frame(self):
        self.setPixmap(self.frames[self.state][self.direction][self.frame_index])

    def animate(self, dt):
        self.frame_elapsed += dt
        while self.frame_elapsed >= FRAME_SECONDS:
            self.frame_elapsed -= FRAME_SECONDS
            frames = self.frames[self.state][self.direction]
            if self.state in ("jump", "fall") and self.drag_offset is None:
                self.frame_index = min(self.frame_index + 1, len(frames) - 1)
            else:
                self.frame_index = (self.frame_index + 1) % len(frames)
        self.draw_frame()

    def screen_bounds(self):
        screen = QApplication.screenAt(self.frameGeometry().center())
        return (screen or QApplication.primaryScreen()).availableGeometry()

    def floor_y(self):
        b = self.screen_bounds()
        return max(b.top(), b.bottom() + 1 - self.foot_height())

    def begin_run(self):
        b = self.screen_bounds()
        left, right = b.left(), max(b.left(), b.right() + 1 - self.width())
        if self.follow_cursor:
            target = QCursor.pos().x() - self.width() / 2
        else:
            distance = random.randint(120, 350) * random.choice([-1, 1])
            target = self.float_x + distance
            if not left <= target <= right:
                target = self.float_x - distance
        target = max(left, min(right, target))
        if abs(target - self.float_x) < 15:
            self.next_action = time.monotonic() + 0.3
            return
        self.target_x = float(target)
        self.direction = 1 if target > self.float_x else -1
        self.set_state("run")

    def jump(self):
        if self.airborne or self.drag_offset is not None:
            return
        self.support = None
        self.airborne, self.velocity_y = True, -JUMP_SPEED
        self.set_state("jump")

    def start_fall(self):
        self.support = None
        self.airborne, self.velocity_y = True, 0.0
        self.set_state("fall")

    def land(self, top, support, now):
        self.float_y = top - self.foot_height()
        self.support = dict(support) if support else None
        self.airborne, self.velocity_y = False, 0.0
        self.set_state("idle")
        self.next_action = now + (0.3 if self.follow_cursor else 1.5)
        self.next_hop = now + random.uniform(8, 16)

    def follow_support(self):
        if self.support is None:
            return
        current = next((w for w in self.platforms.items if w["id"] == self.support["id"]), None)
        # Check maximization BEFORE applying the new window position.
        # The cat must fall from the old perch, not teleport to the screen top.
        if not self.window_perching or current is None or not current["perch"]:
            self.start_fall()
            return
        dx = current["left"] - self.support["left"]
        new_y = current["top"] - self.foot_height()
        if new_y < self.screen_bounds().top():
            self.start_fall()
            return
        self.float_x += dx
        self.target_x += dx
        self.float_y = new_y
        self.support = dict(current)
        center = self.float_x + self.width() / 2
        if not (current["left"] <= center < current["right"]
                and self.platforms.exposed(current, center)):
            self.start_fall()

    def falling_step(self, dt, now):
        previous_feet = self.float_y + self.foot_height()
        self.velocity_y += GRAVITY * dt
        new_y = self.float_y + self.velocity_y * dt
        new_feet = new_y + self.foot_height()
        hits = []
        if self.velocity_y >= 0:
            floor = self.floor_y() + self.foot_height()
            if new_feet >= floor:
                hits.append((floor, None))
            if self.window_perching:
                center = self.float_x + self.width() / 2
                screen_top = self.screen_bounds().top()
                for w in self.platforms.items:
                    if (w["perch"] and w["top"] - self.foot_height() >= screen_top
                            and w["left"] <= center < w["right"]
                            and previous_feet <= w["top"] + 0.5 and new_feet >= w["top"]
                            and self.platforms.exposed(w, center)):
                        hits.append((w["top"], w))
            if self.state != "fall":
                self.set_state("fall")
        if hits:
            top, support = min(hits, key=lambda item: item[0])
            self.land(top, support, now)
        else:
            self.float_y = new_y

    def tick(self):
        now = time.monotonic()
        dt = min(now - self.last_tick, 0.05)
        self.last_tick = now
        if self.menu_open:
            return
        if self.drag_offset is not None:
            self.animate(dt)
            return
        if now >= self.next_scan:
            self.platforms.refresh()
            self.next_scan = now + 0.10
        if not self.airborne:
            self.follow_support()
        if self.airborne:
            self.falling_step(dt, now)
        elif self.wandering:
            if self.auto_hops and now >= self.next_hop:
                self.jump()
            elif self.state == "idle" and now >= self.next_action:
                self.begin_run()
            elif self.state == "run":
                remaining, step = self.target_x - self.float_x, SPEED * dt
                if abs(remaining) <= step:
                    self.float_x = self.target_x
                    self.set_state("idle")
                    self.next_action = now + (0.25 if self.follow_cursor else random.uniform(2, 5))
                else:
                    self.float_x += self.direction * step
                if self.support:
                    center = self.float_x + self.width() / 2
                    if not self.support["left"] <= center < self.support["right"]:
                        self.start_fall()
        self.move(round(self.float_x), round(self.float_y))
        self.animate(dt)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.support = None
            self.airborne, self.velocity_y = False, 0.0
            self.frame_index, self.frame_elapsed = 0, 0.0
            self.set_state("fall")
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def release_to_floor(self):
        b = self.screen_bounds()
        right = max(b.left(), b.right() + 1 - self.width())
        self.float_x = float(max(b.left(), min(right, self.x())))
        self.float_y = float(max(b.top(), min(self.floor_y(), self.y())))
        self.platforms.refresh()
        self.start_fall()
        self.move(round(self.float_x), round(self.float_y))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drag_offset is not None:
                self.drag_offset = None
                self.release_to_floor()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.follow_cursor = not self.follow_cursor
            self.wandering = True
            self.drag_offset = None
            self.release_to_floor()
            self.next_action = time.monotonic()
            print("Cursor chase ON" if self.follow_cursor else "Wandering", flush=True)
            event.accept()

    def contextMenuEvent(self, event):
        self.menu_open = True
        menu = QMenu(self)
        hop = menu.addAction("Jump!")
        checks = {}
        for label, attr in (("Chase cursor", "follow_cursor"),
                            ("Occasional automatic hops", "auto_hops"),
                            ("Perch on windows", "window_perching")):
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(getattr(self, attr))
            checks[action] = attr
        toggle = menu.addAction("Pause wandering" if self.wandering else "Resume wandering")
        menu.addSeparator()
        quit_action = menu.addAction("Quit Sidekick")
        try:
            selected = menu.exec(event.globalPos())
        finally:
            self.menu_open = False
            self.last_tick = time.monotonic()
        if selected == quit_action:
            QApplication.instance().quit()
        elif selected == hop:
            self.jump()
        elif selected in checks:
            attr = checks[selected]
            setattr(self, attr, selected.isChecked())
            if attr == "follow_cursor":
                self.wandering = True
                if not self.airborne:
                    self.set_state("idle")
                self.next_action = time.monotonic()
            elif attr == "auto_hops":
                self.next_hop = time.monotonic() + random.uniform(8, 16)
            elif not self.window_perching and self.support:
                self.start_fall()
        elif selected == toggle:
            self.wandering = not self.wandering
            if not self.airborne:
                self.set_state("idle")
            self.next_action = time.monotonic() + 2


if __name__ == "__main__":
    if sys.platform != "win32":
        raise SystemExit("This Sidekick version requires Windows.")
    app = QApplication(sys.argv)
    cat = DesktopCat()
    cat.show()
    sys.exit(app.exec())
