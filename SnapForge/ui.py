import os
import sys
import logging
from PyQt6.QtGui import QIcon, QFont, QIntValidator, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QCheckBox, QProgressBar, QGridLayout, 
    QVBoxLayout, QGroupBox, QComboBox, QSpinBox, QRadioButton, QHBoxLayout,
    QButtonGroup, QTextEdit, QSizePolicy
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from logic import ImageProcessor, ProcessLog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("image_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WorkerThread(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(int, int, str)
    error = pyqtSignal(str)

    def __init__(self, processor: ImageProcessor, files, prefix, start_num,
                 source_ext, target_ext, quality, preserve_metadata, original_file_action,
                 resize_enabled, resize_width, resize_height, resize_mode, resize_only_shrink):
        super().__init__()
        self.processor = processor
        self.files = files
        self.prefix = prefix
        self.start_num = start_num
        self.source_ext = source_ext
        self.target_ext = target_ext
        self.quality = quality
        self.preserve_metadata = preserve_metadata
        self.original_file_action = original_file_action
        self.resize_enabled = resize_enabled
        self.resize_width = resize_width
        self.resize_height = resize_height
        self.resize_mode = resize_mode
        self.resize_only_shrink = resize_only_shrink
        self.log = ProcessLog()

    def run(self):
        try:
            processed, total_files = self.processor.batch_process(
                files=self.files,
                prefix=self.prefix if self.prefix else None,
                start_number=self.start_num,
                extension=self.source_ext,
                convert_format=self.target_ext,
                quality=self.quality,
                progress_callback=self.progress.emit,
                preserve_metadata=self.preserve_metadata,
                original_file_action=self.original_file_action,
                resize_enabled=self.resize_enabled,
                resize_width=self.resize_width,
                resize_height=self.resize_height,
                resize_mode=self.resize_mode,
                resize_only_shrink=self.resize_only_shrink,
                process_log=self.log
            )
            self.completed.emit(processed, total_files, self.log.get_text())
        except Exception as e:
            logger.error(f"处理过程中发生错误: {str(e)}", exc_info=True)
            self.error.emit(str(e))

class BatchImageApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片批量/单文件处理工具")
        self.resize(900, 1000)  # 初始尺寸，允许任意缩放
        self.set_application_icon()
        self.processor = ImageProcessor()
        self._init_ui()
        self._connect_signals()
        self._set_styles()

    def set_application_icon(self):
        icon_paths = [
            "resources/icon.png",
            "icon.png",
            os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        ]
        for path in icon_paths:
            if os.path.exists(path):
                try:
                    self.setWindowIcon(QIcon(path))
                    logger.info(f"已加载应用程序图标: {path}")
                    return
                except Exception as e:
                    logger.warning(f"加载图标失败: {path} - {str(e)}")
        logger.warning("未找到应用程序图标文件")

    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 处理模式选择
        mode_group = QGroupBox("处理模式")
        mode_layout = QHBoxLayout()
        self.dir_radio = QRadioButton("批量处理目录")
        self.dir_radio.setChecked(True)
        self.file_radio = QRadioButton("处理单个文件")
        self.mode_btn_group = QButtonGroup()
        self.mode_btn_group.addButton(self.dir_radio)
        self.mode_btn_group.addButton(self.file_radio)
        mode_layout.addWidget(self.dir_radio)
        mode_layout.addWidget(self.file_radio)
        mode_layout.addStretch(1)
        mode_group.setLayout(mode_layout)
        mode_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(mode_group)

        # 路径选择
        self.path_group = QGroupBox("目标路径")
        self.path_layout = QHBoxLayout()
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("选择目录（批量）或文件（单个）")
        self.path_button = QPushButton("浏览")
        self.path_layout.addWidget(self.directory_input)
        self.path_layout.addWidget(self.path_button)
        self.path_group.setLayout(self.path_layout)
        self.path_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(self.path_group)

        # 文件类型（仅目录模式可选）
        type_group = QGroupBox("源文件类型")
        type_layout = QHBoxLayout()
        self.extension_label = QLabel("处理图片类型:")
        self.extension_input = QComboBox()
        self.extension_input.addItems([".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"])
        type_layout.addWidget(self.extension_label)
        type_layout.addWidget(self.extension_input)
        type_group.setLayout(type_layout)
        type_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(type_group)

        # 重命名设置
        rename_group = QGroupBox("重命名设置")
        rename_layout = QGridLayout()
        self._create_rename_section(rename_layout)
        rename_group.setLayout(rename_layout)
        rename_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(rename_group)

        # 格式转换
        format_group = QGroupBox("格式转换")
        format_layout = QGridLayout()
        self._create_format_section(format_layout)
        format_group.setLayout(format_layout)
        format_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(format_group)

        # 压缩设置
        compress_group = QGroupBox("压缩设置")
        compress_layout = QGridLayout()
        self._create_compress_section(compress_layout)
        compress_group.setLayout(compress_layout)
        compress_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(compress_group)

        # 尺寸调整
        resize_group = QGroupBox("尺寸调整")
        resize_layout = QGridLayout()
        self._create_resize_section(resize_layout)
        resize_group.setLayout(resize_layout)
        resize_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(resize_group)

        # 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QGridLayout()
        self._create_advanced_section(advanced_layout)
        advanced_group.setLayout(advanced_layout)
        advanced_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(advanced_group)

        # 操作按钮
        self.process_button = QPushButton("开始处理")
        self.process_button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.main_layout.addWidget(self.process_button)

        # 状态栏/日志区
        status_group = QGroupBox("处理状态与日志")
        status_layout = QVBoxLayout()
        self._create_status_section(status_layout)
        status_group.setLayout(status_layout)
        status_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout.addWidget(status_group)

        # 主布局最后加stretch，确保日志区可以撑满剩余空间
        self.main_layout.addStretch()

    def _create_rename_section(self, layout: QGridLayout):
        self.rename_checkbox = QCheckBox("启用重命名")
        self.rename_checkbox.setChecked(True)
        layout.addWidget(self.rename_checkbox, 0, 0, 1, 2)
        self.prefix_label = QLabel("文件名前缀:")
        layout.addWidget(self.prefix_label, 1, 0)
        self.prefix_input = QLineEdit("image")
        self.prefix_input.setPlaceholderText("例如: vacation")
        layout.addWidget(self.prefix_input, 1, 1, 1, 4)
        self.start_number_label = QLabel("起始编号:")
        layout.addWidget(self.start_number_label, 2, 0)
        self.start_number_input = QLineEdit("1")
        self.start_number_input.setValidator(QIntValidator(1, 9999))
        layout.addWidget(self.start_number_input, 2, 1, 1, 4)

    def _create_format_section(self, layout: QGridLayout):
        self.convert_checkbox = QCheckBox("启用格式转换")
        layout.addWidget(self.convert_checkbox, 0, 0, 1, 2)
        self.format_label = QLabel("目标格式:")
        self.format_label.setEnabled(False)
        layout.addWidget(self.format_label, 1, 0)
        self.format_input = QComboBox()
        self.format_input.setEnabled(False)
        self.format_input.addItems([".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"])
        self.format_input.setCurrentText(".png")
        layout.addWidget(self.format_input, 1, 1, 1, 4)

    def _create_compress_section(self, layout: QGridLayout):
        self.compress_checkbox = QCheckBox("启用质量压缩")
        layout.addWidget(self.compress_checkbox, 0, 0, 1, 2)
        self.quality_label = QLabel("压缩质量 (1-100):")
        self.quality_label.setEnabled(False)
        layout.addWidget(self.quality_label, 1, 0)
        self.quality_input = QLineEdit("85")
        self.quality_input.setEnabled(False)
        self.quality_input.setValidator(QIntValidator(1, 100))
        layout.addWidget(self.quality_input, 1, 1, 1, 4)
        self.quality_info = QLabel("提示: JPEG/WEBP使用质量参数，PNG使用压缩级别")
        self.quality_info.setEnabled(False)
        self.quality_info.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.quality_info, 2, 0, 1, 5)

    def _create_resize_section(self, layout: QGridLayout):
        self.resize_checkbox = QCheckBox("启用尺寸调整")
        layout.addWidget(self.resize_checkbox, 0, 0, 1, 2)
        self.resize_width_label = QLabel("目标宽度:")
        self.resize_width_label.setEnabled(False)
        layout.addWidget(self.resize_width_label, 1, 0)
        self.resize_width_input = QSpinBox()
        self.resize_width_input.setRange(1, 9999)
        self.resize_width_input.setValue(800)
        self.resize_width_input.setEnabled(False)
        layout.addWidget(self.resize_width_input, 1, 1, 1, 2)
        self.resize_height_label = QLabel("目标高度:")
        self.resize_height_label.setEnabled(False)
        layout.addWidget(self.resize_height_label, 1, 3)
        self.resize_height_input = QSpinBox()
        self.resize_height_input.setRange(1, 9999)
        self.resize_height_input.setValue(600)
        self.resize_height_input.setEnabled(False)
        layout.addWidget(self.resize_height_input, 1, 4, 1, 2)
        self.resize_mode_label = QLabel("缩放模式:")
        self.resize_mode_label.setEnabled(False)
        layout.addWidget(self.resize_mode_label, 2, 0)
        self.resize_mode_input = QComboBox()
        self.resize_mode_input.setEnabled(False)
        self.resize_mode_input.addItems([
            "等比缩放（fit）", "拉伸填充（fill）", "填充白边（pad）", "中心裁剪（crop）"
        ])
        layout.addWidget(self.resize_mode_input, 2, 1, 1, 2)
        self.resize_only_shrink_checkbox = QCheckBox("仅缩小不放大")
        self.resize_only_shrink_checkbox.setChecked(True)
        self.resize_only_shrink_checkbox.setEnabled(False)
        layout.addWidget(self.resize_only_shrink_checkbox, 2, 3, 1, 2)

    def _create_advanced_section(self, layout: QGridLayout):
        self.metadata_label = QLabel("元数据处理:")
        layout.addWidget(self.metadata_label, 0, 0)
        self.metadata_checkbox = QCheckBox("保留元数据 (EXIF)")
        self.metadata_checkbox.setChecked(True)
        layout.addWidget(self.metadata_checkbox, 0, 1, 1, 4)
        self.file_action_label = QLabel("原始文件处理:")
        layout.addWidget(self.file_action_label, 1, 0)
        self.file_action_combo = QComboBox()
        self.file_action_combo.addItem("保留原始文件", "keep")
        self.file_action_combo.addItem("删除原始文件", "delete")
        self.file_action_combo.addItem("移动到备份目录", "move_to_backup")
        layout.addWidget(self.file_action_combo, 1, 1, 1, 4)

    def _create_status_section(self, layout: QVBoxLayout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)
        self.result_label = QLabel("就绪")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.log_view)
        layout.addStretch()

    def _connect_signals(self):
        self.path_button.clicked.connect(self.browse_path)
        self.dir_radio.toggled.connect(self._toggle_mode_ui)
        self.file_radio.toggled.connect(self._toggle_mode_ui)
        self.convert_checkbox.stateChanged.connect(self._toggle_format_input)
        self.compress_checkbox.stateChanged.connect(self._toggle_quality_input)
        self.rename_checkbox.stateChanged.connect(self._toggle_rename_inputs)
        self.resize_checkbox.stateChanged.connect(self._toggle_resize_inputs)
        self.process_button.clicked.connect(self.start_processing)

    def _set_styles(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1.5px solid #7e7e7e;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: #f9f9fc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4086f4;
                color: white;
                border: none;
                padding: 10px 24px;
                font-size: 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2a6cdb;
            }
            QProgressBar {
                border: 1px solid #aaa;
                border-radius: 4px;
                text-align: center;
                height: 22px;
                font-size: 14px;
            }
            QProgressBar::chunk {
                background-color: #4086f4;
                width: 10px;
            }
            QLabel {
                font-size: 13px;
            }
            QComboBox, QLineEdit, QSpinBox {
                padding: 6px;
                border: 1.2px solid #bbb;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.result_label.setFont(title_font)

    def _toggle_mode_ui(self):
        if self.dir_radio.isChecked():
            self.directory_input.setPlaceholderText("请选择包含图片的目录")
            self.extension_input.setEnabled(True)
            self.extension_label.setEnabled(True)
            self.prefix_label.setText("文件名前缀:")
        else:
            self.directory_input.setPlaceholderText("请选择图片文件")
            self.extension_input.setEnabled(False)
            self.extension_label.setEnabled(False)
            self.prefix_label.setText("新文件名前缀:")

    def _toggle_rename_inputs(self, state):
        enabled = state == 2
        self.prefix_label.setEnabled(enabled)
        self.prefix_input.setEnabled(enabled)
        self.start_number_label.setEnabled(enabled)
        self.start_number_input.setEnabled(enabled)

    def _toggle_format_input(self, state):
        enabled = state == 2
        self.format_label.setEnabled(enabled)
        self.format_input.setEnabled(enabled)

    def _toggle_quality_input(self, state):
        enabled = state == 2
        self.quality_label.setEnabled(enabled)
        self.quality_input.setEnabled(enabled)
        self.quality_info.setEnabled(enabled)

    def _toggle_resize_inputs(self, state):
        enabled = state == 2
        self.resize_width_label.setEnabled(enabled)
        self.resize_width_input.setEnabled(enabled)
        self.resize_height_label.setEnabled(enabled)
        self.resize_height_input.setEnabled(enabled)
        self.resize_mode_label.setEnabled(enabled)
        self.resize_mode_input.setEnabled(enabled)
        self.resize_only_shrink_checkbox.setEnabled(enabled)

    def browse_path(self):
        if self.dir_radio.isChecked():
            directory = QFileDialog.getExistingDirectory(
                self, "选择图片目录",
                options=QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
            )
            if directory:
                self.directory_input.setText(directory)
        else:
            file, _ = QFileDialog.getOpenFileName(
                self, "选择图片文件", "",
                "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp)"
            )
            if file:
                self.directory_input.setText(file)
                ext = os.path.splitext(file)[1].lower()
                idx = self.extension_input.findText(ext)
                if idx >= 0:
                    self.extension_input.setCurrentIndex(idx)

    def _validate_inputs(self) -> bool:
        path = self.directory_input.text().strip()
        if self.dir_radio.isChecked():
            if not path or not os.path.isdir(path):
                QMessageBox.critical(self, "错误", "请选择有效的目录。")
                return False
        else:
            if not path or not os.path.isfile(path):
                QMessageBox.critical(self, "错误", "请选择有效的图片文件。")
                return False
        if self.dir_radio.isChecked() and not self.extension_input.currentText():
            QMessageBox.critical(self, "错误", "请选择要处理的图片类型。")
            return False
        if self.rename_checkbox.isChecked():
            try:
                start_num = int(self.start_number_input.text())
                if start_num <= 0:
                    raise ValueError("起始编号必须大于0")
            except ValueError:
                QMessageBox.critical(self, "错误", "起始编号必须为正整数")
                return False
            if self.prefix_input.text().strip() == "":
                QMessageBox.critical(self, "错误", "文件名前缀不能为空")
                return False
        if self.compress_checkbox.isChecked():
            try:
                quality = int(self.quality_input.text())
                if not 1 <= quality <= 100:
                    raise ValueError("压缩质量超出范围")
            except ValueError:
                QMessageBox.critical(self, "错误", "压缩质量必须为1-100的整数")
                return False
        if self.resize_checkbox.isChecked():
            if self.resize_width_input.value() <= 0 or self.resize_height_input.value() <= 0:
                QMessageBox.critical(self, "错误", "目标宽/高必须为正整数")
                return False
        return True

    def start_processing(self):
        if not self._validate_inputs():
            return
        files = []
        path = self.directory_input.text().strip()
        self.log_view.clear()
        # 获取待处理文件列表
        if self.dir_radio.isChecked():
            ext = self.extension_input.currentText().lower()
            files = [
                os.path.join(path, f) for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f)) and os.path.splitext(f)[1].lower() == ext
            ]
            source_ext = ext
        else:
            files = [path]
            source_ext = os.path.splitext(path)[1].lower()
        if not files:
            QMessageBox.warning(self, "未找到文件", "未找到符合条件的图片文件。")
            return
        resize_modes = {
            0: "fit",
            1: "fill",
            2: "pad",
            3: "crop"
        }
        args = {
            'processor': self.processor,
            'files': files,
            'prefix': self.prefix_input.text() if self.rename_checkbox.isChecked() else '',
            'start_num': int(self.start_number_input.text()) if self.rename_checkbox.isChecked() else 1,
            'source_ext': source_ext,
            'target_ext': self.format_input.currentText() if self.convert_checkbox.isChecked() else '',
            'quality': int(self.quality_input.text()) if self.compress_checkbox.isChecked() else None,
            'preserve_metadata': self.metadata_checkbox.isChecked(),
            'original_file_action': self.file_action_combo.currentData(),
            'resize_enabled': self.resize_checkbox.isChecked(),
            'resize_width': self.resize_width_input.value() if self.resize_checkbox.isChecked() else None,
            'resize_height': self.resize_height_input.value() if self.resize_checkbox.isChecked() else None,
            'resize_mode': resize_modes[self.resize_mode_input.currentIndex()] if self.resize_checkbox.isChecked() else "fit",
            'resize_only_shrink': self.resize_only_shrink_checkbox.isChecked() if self.resize_checkbox.isChecked() else True,
        }
        self.process_button.setEnabled(False)
        self.result_label.setText("处理中...")
        self.progress_bar.setValue(0)
        self.thread = WorkerThread(**args)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.completed.connect(self.on_processing_completed)
        self.thread.error.connect(self.on_processing_error)
        self.thread.finished.connect(lambda: self.process_button.setEnabled(True))
        self.thread.start()

    def on_processing_completed(self, success_count, total_files, log_text):
        self.result_label.setText(f"处理完成: {success_count}/{total_files} 个文件")
        self.progress_bar.setValue(100)
        self.process_button.setEnabled(True)
        self.log_view.setPlainText(log_text)
        # 修复：PyQt6 应该用 QTextCursor.MoveOperation.End
        self.log_view.moveCursor(QTextCursor.MoveOperation.End)
        if success_count == 0:
            QMessageBox.warning(
                self, "全部失败", "未成功处理任何图片，请检查日志与参数。"
            )
        elif success_count < total_files:
            QMessageBox.warning(
                self, "部分处理失败", "有部分图片未处理成功，请查看下方日志详情。"
            )
        else:
            QMessageBox.information(
                self, "处理完成", f"成功处理 {success_count} 个文件（共 {total_files} 个）"
            )

    def on_processing_error(self, error_msg):
        self.result_label.setText("处理出错")
        self.process_button.setEnabled(True)
        self.log_view.append(f"\n异常：{error_msg}")
        QMessageBox.critical(
            self,
            "处理错误",
            f"处理过程中发生错误:\n{error_msg}"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont()
    font.setFamily("Arial")
    font.setPointSize(12)
    app.setFont(font)
    window = BatchImageApp()
    window.show()
    sys.exit(app.exec())
