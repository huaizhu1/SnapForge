import os
import sys
import cv2
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QCheckBox, QProgressBar, QGridLayout
)
from PyQt6.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor
import logging

class ImageProcessor:
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}

    def batch_process(self, directory: str, prefix: str, start_number: int, 
                     extension: str, convert_format: str, compress_quality: int,
                     progress_callback: callable) -> int:
        """批量处理图片文件"""
        files = [f for f in os.listdir(directory) if f.lower().endswith(extension)]
        total = len(files)
        processed = 0

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self._process_single_file,
                    os.path.join(directory, file),
                    f"{prefix}{start_number + i}{extension}",
                    directory,
                    convert_format,
                    compress_quality
                ) for i, file in enumerate(files)
            ]

            for future in futures:
                if future.result():
                    processed += 1
                    progress_callback(int(processed/total*100))

        return processed

    def _process_single_file(self, file_path: str, new_name: str, directory: str,
                           convert_format: str, compress_quality: int) -> bool:
        """处理单个文件"""
        try:
            if not os.path.exists(file_path):
                logging.warning(f"文件不存在: {file_path}")
                return False

            image = cv2.imread(file_path)
            if image is None:
                logging.error(f"无法读取文件: {file_path}")
                return False

            # 格式转换处理
            if convert_format:
                new_name = new_name.replace(
                    os.path.splitext(new_name)[1],
                    f".{convert_format.lower()}"
                )

            # 保存参数处理
            save_params = []
            if compress_quality and convert_format in ['jpg', 'jpeg']:
                save_params = [cv2.IMWRITE_JPEG_QUALITY, compress_quality]

            cv2.imwrite(
                os.path.join(directory, new_name),
                image,
                save_params
            )
            return True

        except Exception as e:
            logging.error(f"处理文件 {file_path} 失败: {str(e)}")
            return False


class WorkerThread(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, directory: str, prefix: str, start_num: int, 
                 ext: str, conv_fmt: str, quality: int):
        super().__init__()
        self.directory = directory
        self.prefix = prefix
        self.start_num = start_num
        self.ext = ext
        self.conv_fmt = conv_fmt
        self.quality = quality
        self.processor = ImageProcessor()

    def run(self):
        try:
            count = self.processor.batch_process(
                self.directory,
                self.prefix,
                self.start_num,
                self.ext,
                self.conv_fmt,
                self.quality,
                self.progress.emit
            )
            self.completed.emit(count)
        except Exception as e:
            self.error.emit(str(e))


class BatchRenameApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片批量处理工具")
        self.setGeometry(300, 300, 500, 450)
        self.setWindowIcon(QIcon("resources/icon.png"))
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化界面组件"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)
        
        self._create_directory_section(0)
        self._create_rename_section(1)
        self._create_format_section(5)
        self._create_compress_section(7)
        self._create_action_section(9)
        self._create_status_section(10)

    def _create_directory_section(self, row: int):
        """创建目录选择部分"""
        self.directory_label = QLabel("选择目录:")
        self.layout.addWidget(self.directory_label, row, 0)
        
        self.directory_input = QLineEdit()
        self.layout.addWidget(self.directory_input, row, 1, 1, 3)
        
        self.directory_button = QPushButton("浏览")
        self.layout.addWidget(self.directory_button, row, 4)

    def _create_rename_section(self, row: int):
        """创建重命名设置部分"""
        self.rename_checkbox = QCheckBox("启用重命名")
        self.layout.addWidget(self.rename_checkbox, row, 0, 1, 2)
        
        self.prefix_label = QLabel("文件名前缀:")
        self.layout.addWidget(self.prefix_label, row+1, 0)
        
        self.prefix_input = QLineEdit()
        self.layout.addWidget(self.prefix_input, row+1, 1, 1, 4)
        
        self.start_number_label = QLabel("起始编号:")
        self.layout.addWidget(self.start_number_label, row+2, 0)
        
        self.start_number_input = QLineEdit("1")
        self.layout.addWidget(self.start_number_input, row+2, 1, 1, 4)
        
        self.extension_label = QLabel("文件扩展名:")
        self.layout.addWidget(self.extension_label, row+3, 0)
        
        self.extension_input = QLineEdit(".jpg")
        self.layout.addWidget(self.extension_input, row+3, 1, 1, 4)

    def _create_format_section(self, row: int):
        """创建格式转换部分"""
        self.convert_checkbox = QCheckBox("启用格式转换")
        self.layout.addWidget(self.convert_checkbox, row, 0, 1, 2)
        
        self.format_label = QLabel("目标格式:")
        self.format_label.setEnabled(False)
        self.layout.addWidget(self.format_label, row+1, 0)
        
        self.format_input = QLineEdit()
        self.format_input.setEnabled(False)
        self.layout.addWidget(self.format_input, row+1, 1, 1, 4)

    def _create_compress_section(self, row: int):
        """创建压缩设置部分"""
        self.compress_checkbox = QCheckBox("启用质量压缩")
        self.layout.addWidget(self.compress_checkbox, row, 0, 1, 2)
        
        self.quality_label = QLabel("压缩质量 (0-100):")
        self.quality_label.setEnabled(False)
        self.layout.addWidget(self.quality_label, row+1, 0)
        
        self.quality_input = QLineEdit("85")
        self.quality_input.setEnabled(False)
        self.layout.addWidget(self.quality_input, row+1, 1, 1, 4)

    def _create_action_section(self, row: int):
        """创建操作按钮部分"""
        self.process_button = QPushButton("开始处理")
        self.layout.addWidget(self.process_button, row, 0, 1, 5)

    def _create_status_section(self, row: int):
        """创建状态显示部分"""
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar, row, 0, 1, 5)
        
        self.result_label = QLabel()
        self.layout.addWidget(self.result_label, row+1, 0, 1, 5)

    def _connect_signals(self):
        """连接信号与槽"""
        self.directory_button.clicked.connect(self.browse_directory)
        self.convert_checkbox.stateChanged.connect(self._toggle_format_input)
        self.compress_checkbox.stateChanged.connect(self._toggle_quality_input)
        self.process_button.clicked.connect(self.start_processing)

    def browse_directory(self):
        """目录选择对话框"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self.directory_input.setText(directory)

    def _toggle_format_input(self):
        """切换格式转换输入状态"""
        enabled = self.convert_checkbox.isChecked()
        self.format_label.setEnabled(enabled)
        self.format_input.setEnabled(enabled)

    def _toggle_quality_input(self):
        """切换压缩质量输入状态"""
        enabled = self.compress_checkbox.isChecked()
        self.quality_label.setEnabled(enabled)
        self.quality_input.setEnabled(enabled)

    def _validate_inputs(self) -> bool:
        """输入验证"""
        directory = self.directory_input.text()
        if not os.path.isdir(directory):
            QMessageBox.critical(self, "错误", "目录路径无效")
            return False

        if self.rename_checkbox.isChecked():
            try:
                start_num = int(self.start_number_input.text())
                if start_num <= 0:
                    raise ValueError("起始编号必须大于0")
            except ValueError:
                QMessageBox.critical(self, "错误", "起始编号必须为正整数")
                return False

            ext = self.extension_input.text().strip()
            if not ext.startswith('.'):
                QMessageBox.critical(self, "错误", "扩展名必须以.开头")
                return False

        if self.convert_checkbox.isChecked():
            fmt = self.format_input.text().strip().lower()
            if fmt not in ['jpg', 'png', 'bmp', 'tiff']:
                QMessageBox.critical(self, "错误", "不支持的转换格式")
                return False

        if self.compress_checkbox.isChecked():
            try:
                quality = int(self.quality_input.text())
                if not 0 <= quality <= 100:
                    raise ValueError("压缩质量超出范围")
            except ValueError:
                QMessageBox.critical(self, "错误", "压缩质量必须为0-100的整数")
                return False

        return True

    def start_processing(self):
        """开始处理操作"""
        if not self._validate_inputs():
            return

        args = {
            'directory': self.directory_input.text(),
            'prefix': self.prefix_input.text() if self.rename_checkbox.isChecked() else '',
            'start_num': int(self.start_number_input.text()),
            'ext': self.extension_input.text().strip(),
            'conv_fmt': self.format_input.text().strip() if self.convert_checkbox.isChecked() else '',
            'quality': int(self.quality_input.text()) if self.compress_checkbox.isChecked() else None
        }

        self.thread = WorkerThread(**args)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.completed.connect(lambda c: self.result_label.setText(f"处理完成: {c} 个文件"))
        self.thread.error.connect(lambda e: QMessageBox.critical(self, "错误", e))
        self.thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BatchRenameApp()
    window.show()
    sys.exit(app.exec())