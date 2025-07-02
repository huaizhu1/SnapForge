import os
import sys
import cv2
import shutil
import tempfile
import numpy as np
from PyQt6.QtGui import QIcon, QFont, QIntValidator  # 添加 QIntValidator
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QCheckBox, QProgressBar, QGridLayout, QVBoxLayout, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt  # 保留 Qt 用于对齐标志
import logging

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

class ImageProcessor:
    def __init__(self):
        # 支持的格式映射到OpenCV参数
        self.supported_formats = {
            '.jpg': {'writer': cv2.IMWRITE_JPEG_QUALITY, 'default_quality': 95},
            '.jpeg': {'writer': cv2.IMWRITE_JPEG_QUALITY, 'default_quality': 95},
            '.png': {'writer': cv2.IMWRITE_PNG_COMPRESSION, 'default_quality': 3},
            '.bmp': {'writer': None, 'default_quality': None},
            '.tiff': {'writer': cv2.IMWRITE_TIFF_COMPRESSION, 'default_quality': 5},
            '.webp': {'writer': cv2.IMWRITE_WEBP_QUALITY, 'default_quality': 80}
        }
        
        # 格式别名映射
        self.format_aliases = {
            'jpg': '.jpg',
            'jpeg': '.jpeg',
            'png': '.png',
            'bmp': '.bmp',
            'tif': '.tiff',
            'tiff': '.tiff',
            'webp': '.webp'
        }

    def normalize_extension(self, ext: str) -> str:
        """规范化扩展名格式"""
        ext = ext.strip().lower()
        if not ext.startswith('.'):
            ext = '.' + ext
            
        # 处理别名
        if ext in self.format_aliases:
            return self.format_aliases[ext]
            
        return ext

    def batch_process(self, directory: str, prefix: str, start_number: int, 
                     source_ext: str, target_ext: str, quality: int,
                     progress_callback: callable) -> int:
        """批量处理图片文件"""
        # 规范化扩展名
        source_ext = self.normalize_extension(source_ext)
        target_ext = self.normalize_extension(target_ext) if target_ext else source_ext
        
        # 验证扩展名
        if source_ext not in self.supported_formats:
            logger.error(f"不支持的源文件格式: {source_ext}")
            return 0
            
        if target_ext not in self.supported_formats:
            logger.error(f"不支持的目标文件格式: {target_ext}")
            return 0
        
        # 获取文件列表
        files = [
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and 
            self.normalize_extension(os.path.splitext(f)[1]) == source_ext
        ]
        
        if not files:
            logger.warning(f"目录中没有找到匹配 {source_ext} 的文件: {directory}")
            return 0

        total = len(files)
        processed = 0
        created_files = set()  # 跟踪已创建的文件名

        # 创建临时目录
        with tempfile.TemporaryDirectory(prefix="imgproc_", dir=directory) as temp_dir:
            for i, filename in enumerate(files):
                try:
                    file_path = os.path.join(directory, filename)
                    
                    # 生成唯一文件名
                    new_filename = self.generate_unique_filename(
                        prefix, start_number + i, target_ext, created_files
                    )
                    created_files.add(new_filename.lower())
                    
                    # 临时保存路径
                    temp_path = os.path.join(temp_dir, new_filename)
                    
                    # 处理单个文件
                    if self.process_single_file(file_path, temp_path, target_ext, quality):
                        # 移动回原目录
                        final_path = os.path.join(directory, new_filename)
                        shutil.move(temp_path, final_path)
                        processed += 1
                    
                    # 更新进度
                    if progress_callback:
                        progress = int((i + 1) / total * 100)
                        progress_callback(progress)
                        
                except Exception as e:
                    logger.error(f"处理文件 {filename} 失败: {str(e)}", exc_info=True)
        
        return processed

    def generate_unique_filename(self, prefix: str, number: int, 
                               extension: str, existing: set) -> str:
        """生成唯一的文件名"""
        base_name = f"{prefix}_{number:04d}" if prefix else f"{number:04d}"
        new_name = f"{base_name}{extension}"
        
        # 检查并避免重名
        counter = 1
        while new_name.lower() in existing:
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1
            
        return new_name

def process_single_file(self, src_path: str, dest_path: str, 
                      target_ext: str, quality: int) -> bool:
    """处理单个文件"""
    if not os.path.exists(src_path):
        logger.warning(f"文件不存在: {src_path}")
        return False

    # 使用二进制模式读取文件（解决中文路径问题）
    try:
        with open(src_path, 'rb') as f:
            img_bytes = np.frombuffer(f.read(), dtype=np.uint8)
    except Exception as e:
        logger.error(f"读取文件失败: {src_path} - {str(e)}")
        return False

    # 解码图像
    image = cv2.imdecode(img_bytes, cv2.IMREAD_UNCHANGED)
    if image is None:
        logger.error(f"无法解码文件: {src_path}")
        return False

    # 处理透明通道
    if len(image.shape) == 3 and image.shape[2] == 4 and target_ext in ['.jpg', '.jpeg', '.bmp']:
        # 创建白色背景
        bg = np.ones_like(image[:, :, :3]) * 255
        # 分离alpha通道
        alpha = image[:, :, 3] / 255.0
        # 合成图像
        for c in range(3):
            bg[:, :, c] = (1 - alpha) * bg[:, :, c] + alpha * image[:, :, c]
        image = bg.astype(np.uint8)

    # 准备保存参数
    save_params = []
    format_info = self.supported_formats[target_ext]
    
    if format_info['writer'] is not None:
        if quality is None:
            quality = format_info['default_quality']
        save_params = [format_info['writer'], quality]

    # 编码并保存图像（解决中文路径问题）
    ext = target_ext.lstrip('.')
    if ext.lower() == 'jpg':
        ext = 'jpeg'  # OpenCV使用jpeg而不是jpg
    
    # 编码图像
    ret, buf = cv2.imencode(f'.{ext}', image, save_params)
    if not ret:
        logger.error(f"编码图像失败: {dest_path}")
        return False
    
    # 写入文件
    try:
        with open(dest_path, 'wb') as f:
            f.write(buf.tobytes())
    except Exception as e:
        logger.error(f"写入文件失败: {dest_path} - {str(e)}")
        return False
        
    return True


class WorkerThread(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(int, int)  # 成功数, 总数
    error = pyqtSignal(str)

    def __init__(self, directory: str, prefix: str, start_num: int, 
                 source_ext: str, target_ext: str, quality: int):
        super().__init__()
        self.directory = directory
        self.prefix = prefix
        self.start_num = start_num
        self.source_ext = source_ext
        self.target_ext = target_ext
        self.quality = quality
        self.processor = ImageProcessor()

    def run(self):
        try:
            count = self.processor.batch_process(
                self.directory,
                self.prefix,
                self.start_num,
                self.source_ext,
                self.target_ext,
                self.quality,
                self.progress.emit
            )
            # 获取文件总数
            total_files = len([
                f for f in os.listdir(self.directory)
                if os.path.isfile(os.path.join(self.directory, f)) and 
                self.processor.normalize_extension(os.path.splitext(f)[1]) == 
                self.processor.normalize_extension(self.source_ext)
            ])
            self.completed.emit(count, total_files)
        except Exception as e:
            logger.error(f"处理过程中发生错误: {str(e)}", exc_info=True)
            self.error.emit(str(e))


class BatchRenameApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片批量处理工具")
        self.setGeometry(300, 300, 500, 500)
        # 设置图标（如果存在）
        try:
            self.setWindowIcon(QIcon("resources/icon.png"))
        except:
            pass
        
        self._init_ui()
        self._connect_signals()
        
        # 设置样式
        self._set_styles()

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
        # 使用 QIntValidator 而不是 Qt.QIntValidator
        self.start_number_input.setValidator(QIntValidator(1, 9999))
        layout.addWidget(self.start_number_input, 2, 1, 1, 4)
        
        self.extension_label = QLabel("源文件扩展名:")
        layout.addWidget(self.extension_label, 3, 0)
        
        self.extension_input = QLineEdit(".jpg")
        self.extension_input.setPlaceholderText("例如: .jpg, .png")
        layout.addWidget(self.extension_input, 3, 1, 1, 4)

    def _create_format_section(self, layout: QGridLayout):
        """创建格式转换部分"""
        self.convert_checkbox = QCheckBox("启用格式转换")
        layout.addWidget(self.convert_checkbox, 0, 0, 1, 2)
        
        self.format_label = QLabel("目标格式:")
        self.format_label.setEnabled(False)
        layout.addWidget(self.format_label, 1, 0)
        
        self.format_input = QLineEdit()
        self.format_input.setEnabled(False)
        self.format_input.setPlaceholderText("例如: png, webp")
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
        # 使用 QIntValidator 而不是 Qt.QIntValidator
        self.quality_input.setValidator(QIntValidator(1, 100))
        layout.addWidget(self.quality_input, 1, 1, 1, 4)

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
        self.process_button.clicked.connect(self.start_processing)
        self.rename_checkbox.stateChanged.connect(self._toggle_rename_inputs)

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
            }
            
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
            
            QLabel {
                font-size: 12px;
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

            ext = self.extension_input.text().strip()
            if not ext:
                QMessageBox.critical(self, "错误", "请输入源文件扩展名")
                return False

        # 检查格式转换设置
        if self.convert_checkbox.isChecked():
            fmt = self.format_input.text().strip()
            if not fmt:
                QMessageBox.critical(self, "错误", "请输入目标格式")
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
            'directory': self.directory_input.text(),
            'prefix': self.prefix_input.text() if self.rename_checkbox.isChecked() else '',
            'start_num': int(self.start_number_input.text()) if self.rename_checkbox.isChecked() else 1,
            'source_ext': self.extension_input.text().strip(),
            'target_ext': self.format_input.text().strip() if self.convert_checkbox.isChecked() else '',
            'quality': int(self.quality_input.text()) if self.compress_checkbox.isChecked() else None
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
