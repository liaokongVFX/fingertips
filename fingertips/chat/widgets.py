import os
import json

from PySide2 import QtGui
from PySide2 import QtCore
from PySide2.QtWebChannel import QWebChannel
from PySide2.QtWebEngineWidgets import QWebEngineSettings
from qframelesswindow.webengine import FramelessWebEngineView

from fingertips.core.thread import AskAIThread


class BridgeObject(QtCore.QObject):
    add_chat_item = QtCore.Signal(str)
    set_ai_chat = QtCore.Signal(str)

    def set_ai_chat_content(self, message):
        self.set_ai_chat.emit(message)

    def add_chat_item_content(self, chat_item):
        self.add_chat_item.emit(json.dumps(chat_item))


class ChatHistoryWidget(FramelessWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.histories = []

        self.init_settings()

        self.channel = QWebChannel(self)
        self.bridge_object = BridgeObject()

        self.channel.registerObject('Bridge', self.bridge_object)
        self.page().setWebChannel(self.channel)
        self.load(QtCore.QUrl.fromLocalFile(os.path.abspath('chat.html')))

        QtCore.QTimer.singleShot(0, self.apply_rounded_corners)

    def set_user_content(self, text):
        message = {
            'role': 'user',
            'content': text.strip()
        }
        self.bridge_object.add_chat_item_content(message)
        self.bridge_object.add_chat_item_content({
            'role': 'ai',
            'content': ''
        })

        # todo 设置 model temperature 等
        thread = AskAIThread(
            text.strip(),
            convert_markdown=False,
            histories=self.histories,
            parent=self
        )
        thread.resulted.connect(lambda msg: self.bridge_object.set_ai_chat_content(msg))
        thread.finished.connect(lambda msg: self.histories.append({
            'role': 'ai',
            'content': msg
        }))
        thread.start()

        self.histories.append(message)

    def apply_rounded_corners(self):
        path = QtGui.QPainterPath()
        path.addRoundedRect(self.rect(), 6, 6)  # 设置圆角半径
        # 将路径转换为区域并设置为遮罩
        region = QtGui.QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    @staticmethod
    def init_settings():
        settings = QWebEngineSettings.globalSettings()
        settings.setDefaultTextEncoding('utf-8')
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.TouchIconsEnabled, True)