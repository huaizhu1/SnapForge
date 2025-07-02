# ui.py
import os
import sys
import logging
from PyQt6.QtGui import QIcon, QFont, QIntValidator
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QCheckBox, QProgressBar, QGridLayout, 
    QVBoxLayout, QGroupBox, QComboBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from logic import ImageProcessor  # 导入优化后的逻辑模块

# 配置日志
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
    completed = pyqtSignal(int, int)  # 成功数, 总数
    error = pyqtSignal(str)

    def __init__(self, processor: ImageProcessor, directory: str, prefix: str, start_num: int, 
                 source_ext: str, target_ext: str, quality: int, 
                 preserve_metadata: bool, original_file_action: str):
        super().__init__()
        self.directory = directory
        self.prefix = prefix
        self.start_num = start_num
        self.source_ext = source_ext
        self.target_ext = target_ext
        self.quality = quality
        self.processor = processor
        self.preserve_metadata = preserve_metadata
        self.original_file_action = original_file_action

    def run(self):
        try:
            processed, total_files = self.processor.batch_process(
                directory=self.directory,
                prefix=self.prefix if self.prefix else None,
                start_number=self.start_num,
                extension=self.source_ext,
                convert_format=self.target_ext,
                quality=self.quality,
                progress_callback=self.progress.emit,
                preserve_metadata=self.preserve_metadata,
                original_file_action=self.original_file_action
            )
            self.completed.emit(processed, total_files)
        except Exception as e:
            logger.error(f"处理过程中发生错误: {str(e)}", exc_info=True)
            self.error.emit(str(e))


class BatchRenameApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片批量处理工具")
        self.setGeometry(300, 300, 500, 600)  # 增加高度以适应新控件
        
        # 设置应用程序图标
        self.set_application_icon()
        
        # 创建图像处理器实例
        self.processor = ImageProcessor()
        
        self._init_ui()
        self._connect_signals()
        self._set_styles()

    def set_application_icon(self):
        """设置应用程序图标"""
        icon_paths = [
            "resources/icon.png",  # 首选路径
            "icon.png",             # 备用路径
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
        """初始化界面组件"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 目录选择部分
        dir_group = QGroupBox("目录设置")
        dir_layout = QGridLayout()
        self._create_directory_section(dir_layout)
        dir_group.setLayout(dir_layout)
        self.main_layout.addWidget(dir_group)
        
        # 重命名设置部分
        rename_group = QGroupBox("重命名设置")
        rename_layout = QGridLayout()
        self._create_rename_section(rename_layout)
        rename_group.setLayout(rename_layout)
        self.main_layout.addWidget(rename_group)
        
        # 格式转换部分
        format_group = QGroupBox("格式转换")
        format_layout = QGridLayout()
        self._create_format_section(format_layout)
        format_group.setLayout(format_layout)
        self.main_layout.addWidget(format_group)
        
        # 压缩设置部分
        compress_group = QGroupBox("压缩设置")
        compress_layout = QGridLayout()
        self._create_compress_section(compress_layout)
        compress_group.setLayout(compress_layout)
        self.main_layout.addWidget(compress_group)
        
        # 高级选项部分
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QGridLayout()
        self._create_advanced_section(advanced_layout)
        advanced_group.setLayout(advanced_layout)
        self.main_layout.addWidget(advanced_group)
        
        # 操作按钮
        self.process_button = QPushButton("开始处理")
        self.process_button.setMinimumHeight(40)
        self.main_layout.addWidget(self.process_button)
        
        # 进度和状态
        status_group = QGroupBox("处理状态")
        status_layout = QVBoxLayout()
        self._create_status_section(status_layout)
        status_group.setLayout(status_layout)
        self.main_layout.addWidget(status_group)

    def _create_directory_section(self, layout: QGridLayout):
        """创建目录选择部分"""
        self.directory_label = QLabel("选择目录:")
        layout.addWidget(self.directory_label, 0, 0)
        
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("请选择图片目录")
        layout.addWidget(self.directory_input, 0, 1, 1, 3)
        
        self.directory_button = QPushButton("浏览")
        layout.addWidget(self.directory_button, 0, 4)

    def _create_rename_section(self, layout: QGridLayout):
        """创建重命名设置部分"""
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
        
        self.extension_label = QLabel("源文件扩展名:")
        layout.addWidget(self.extension_label, 3, 0)
        
        self.extension_input = QComboBox()
        self.extension_input.addItems([".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"])
        self.extension_input.setCurrentText(".jpg")
        layout.addWidget(self.extension_input, 3, 1, 1, 4)

    def _create_format_section(self, layout: QGridLayout):
        """创建格式转换部分"""
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
        """创建压缩设置部分"""
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

    def _create_advanced_section(self, layout: QGridLayout):
        """创建高级选项部分"""
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
        """创建状态显示部分"""
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        self.result_label = QLabel("就绪")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)

    def _connect_signals(self):
        """连接信号与槽"""
        self.directory_button.clicked.connect(self.browse_directory)
        self.convert_checkbox.stateChanged.connect(self._toggle_format_input)
        self.compress_checkbox.stateChanged.connect(self._toggle_quality_input)
        self.rename_checkbox.stateChanged.connect(self._toggle_rename_inputs)
        self.process_button.clicked.connect(self.start_processing)

    def _set_styles(self):
        """设置界面样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #aaa;
                border-radius: 5px;
                margin-top: 1ex;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #45a049;
            }
            
            QProgressBar {
                border: 1px solid #aaa;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
            
            QLabel {
                font-size: 12px;
            }
            
            QComboBox, QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        
        # 设置标题字体
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.result_label.setFont(title_font)

    def _toggle_rename_inputs(self, state):
        """切换重命名输入状态"""
        enabled = state == 2  # Qt.Checked = 2
        self.prefix_label.setEnabled(enabled)
        self.prefix_input.setEnabled(enabled)
        self.start_number_label.setEnabled(enabled)
        self.start_number_input.setEnabled(enabled)
        self.extension_label.setEnabled(enabled)
        self.extension_input.setEnabled(enabled)

    def _toggle_format_input(self, state):
        """切换格式转换输入状态"""
        enabled = state == 2  # Qt.Checked = 2
        self.format_label.setEnabled(enabled)
        self.format_input.setEnabled(enabled)

    def _toggle_quality_input(self, state):
        """切换压缩质量输入状态"""
        enabled = state == 2  # Qt.Checked = 2
        self.quality_label.setEnabled(enabled)
        self.quality_input.setEnabled(enabled)
        self.quality_info.setEnabled(enabled)

    def browse_directory(self):
        """目录选择对话框"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "选择图片目录",
            options=QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if directory:
            self.directory_input.setText(directory)

    def _validate_inputs(self) -> bool:
        """输入验证"""
        # 检查目录
        directory = self.directory_input.text()
        if not directory or not os.path.isdir(directory):
            QMessageBox.critical(self, "错误", "请选择有效的目录")
            return False

        # 检查重命名设置
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

        # 检查压缩设置
        if self.compress_checkbox.isChecked():
            try:
                quality = int(self.quality_input.text())
                if not 1 <= quality <= 100:
                    raise ValueError("压缩质量超出范围")
            except ValueError:
                QMessageBox.critical(self, "错误", "压缩质量必须为1-100的整数")
                return False

        return True

    def start_processing(self):
        """开始处理操作"""
        if not self._validate_inputs():
            return

        # 准备参数
        args = {
            'processor': self.processor,
            'directory': self.directory_input.text(),
            'prefix': self.prefix_input.text() if self.rename_checkbox.isChecked() else '',
            'start_num': int(self.start_number_input.text()) if self.rename_checkbox.isChecked() else 1,
            'source_ext': self.extension_input.currentText(),
            'target_ext': self.format_input.currentText() if self.convert_checkbox.isChecked() else '',
            'quality': int(self.quality_input.text()) if self.compress_checkbox.isChecked() else None,
            'preserve_metadata': self.metadata_checkbox.isChecked(),
            'original_file_action': self.file_action_combo.currentData()
        }

        # 更新UI状态
        self.process_button.setEnabled(False)
        self.result_label.setText("处理中...")
        self.progress_bar.setValue(0)

        # 创建并启动工作线程
        self.thread = WorkerThread(**args)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.completed.connect(self.on_processing_completed)
        self.thread.error.connect(self.on_processing_error)
        self.thread.finished.connect(lambda: self.process_button.setEnabled(True))
        self.thread.start()

    def on_processing_completed(self, success_count, total_files):
        """处理完成时的处理"""
        self.result_label.setText(f"处理完成: {success_count}/{total_files} 个文件")
        self.progress_bar.setValue(100)
        self.process_button.setEnabled(True)
        
        # 显示完成消息
        QMessageBox.information(
            self,
            "处理完成",
            f"成功处理 {success_count} 个文件（共 {total_files} 个）"
        )

    def on_processing_error(self, error_msg):
        """处理出错时的处理"""
        self.result_label.setText("处理出错")
        self.process_button.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "处理错误",
            f"处理过程中发生错误:\n{error_msg}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 设置应用字体
    font = QFont()
    font.setFamily("Arial")
    font.setPointSize(10)
    app.setFont(font)
    
    window = BatchRenameApp()
    window.show()
    sys.exit(app.exec())
