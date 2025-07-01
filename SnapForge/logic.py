import os
import shutil
import tempfile
from PIL import Image
import logging
from typing import Optional, Callable, Dict, Set

class ImageProcessor:
    def __init__(self):
        # 扩展名统一使用小写带点格式
        self.supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
        
        # 格式到PIL格式名称的映射
        self.format_mapping = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".bmp": "BMP",
            ".gif": "GIF",
            ".tiff": "TIFF",
            ".webp": "WEBP"
        }

    def batch_process(
        self,
        directory: str,
        prefix: Optional[str] = None,
        start_number: int = 1,
        extension: str = ".jpg",
        convert_format: Optional[str] = None,
        quality: Optional[int] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> int:
        """批量处理图片文件
        
        Args:
            directory: 处理目录
            prefix: 文件名前缀
            start_number: 起始编号
            extension: 处理的文件扩展名（带点）
            convert_format: 目标格式（如 "jpg" 或 ".jpg"）
            quality: 压缩质量（1-100）
            progress_callback: 进度回调函数
            
        Returns:
            处理成功的文件数量
        """
        # 规范化扩展名
        extension = self._normalize_extension(extension)
        if not extension:
            logging.error(f"无效的文件扩展名: {extension}")
            return 0
            
        # 验证目标格式
        target_ext = None
        if convert_format:
            target_ext = self._normalize_extension(convert_format)
            if not target_ext:
                logging.error(f"无效的转换格式: {convert_format}")
                return 0

        # 过滤文件
        files = [
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and 
            self._normalize_extension(os.path.splitext(f)[1]) == extension
        ]
        
        if not files:
            logging.warning(f"目录中没有找到匹配 {extension} 的文件: {directory}")
            if progress_callback:
                progress_callback(100)
            return 0

        total_files = len(files)
        processed = 0
        created_files = set()  # 跟踪已创建的文件名，避免重名覆盖

        # 创建临时目录用于安全处理
        with tempfile.TemporaryDirectory(prefix="imgproc_", dir=directory) as temp_dir:
            for index, filename in enumerate(files):
                try:
                    file_path = os.path.join(directory, filename)
                    
                    # 处理文件名
                    new_filename = self._generate_filename(
                        prefix, start_number + index, 
                        target_ext or extension, created_files
                    )
                    created_files.add(new_filename.lower())
                    
                    # 临时保存路径
                    temp_path = os.path.join(temp_dir, new_filename)
                    
                    # 处理并保存图像
                    self._process_image(
                        file_path, temp_path, 
                        target_ext, quality
                    )
                    
                    # 移动回原目录
                    final_path = os.path.join(directory, new_filename)
                    shutil.move(temp_path, final_path)
                    
                    processed += 1
                    
                except Exception as e:
                    logging.error(f"处理文件 {filename} 失败: {str(e)}", exc_info=True)
                finally:
                    # 无论成功失败都更新进度
                    self._update_progress(progress_callback, index + 1, total_files)

        return processed

    def _normalize_extension(self, ext: str) -> Optional[str]:
        """规范化扩展名格式：小写带点"""
        if not ext:
            return None
            
        # 确保以点开头
        if not ext.startswith("."):
            ext = "." + ext
            
        # 特殊处理jpeg
        if ext.lower() == ".jpeg":
            return ".jpg"
            
        return ext.lower()

    def _generate_filename(
        self, 
        prefix: Optional[str], 
        number: int,
        extension: str,
        existing_files: Set[str]
    ) -> str:
        """生成唯一的新文件名"""
        base_name = f"{prefix}_{number:04d}" if prefix else f"{number:04d}"
        new_name = f"{base_name}{extension}"
        
        # 检查并避免重名
        counter = 1
        while new_name.lower() in existing_files:
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1
            
        return new_name

    def _process_image(
        self,
        src_path: str,
        dest_path: str,
        target_ext: Optional[str],
        quality: Optional[int]
    ) -> None:
        """处理并保存单张图片"""
        with Image.open(src_path) as img:
            # 转换图像模式（如果需要）
            img = self._convert_image_mode(img, target_ext)
            
            # 准备保存参数
            save_params = {}
            if target_ext:
                pil_format = self.format_mapping.get(target_ext)
                if pil_format:
                    save_params["format"] = pil_format
            
            # 设置质量参数
            if quality is not None:
                # 对所有支持质量的格式设置质量参数
                if target_ext in (".jpg", ".jpeg", ".webp"):
                    save_params["quality"] = max(1, min(100, quality))
                elif target_ext == ".png":
                    # PNG使用优化压缩
                    save_params["compress_level"] = max(0, min(9, 9 - (quality // 11)))
            
            img.save(dest_path, **save_params)

    def _convert_image_mode(self, img: Image.Image, target_ext: Optional[str]) -> Image.Image:
        """根据目标格式转换图像模式"""
        if not target_ext:
            return img
            
        # 转换为JPEG需要RGB模式
        if target_ext in (".jpg", ".jpeg"):
            if img.mode in ("RGBA", "P", "LA"):
                return img.convert("RGB")
            if img.mode == "CMYK":
                return img.convert("RGB")
                
        # 其他格式保持原样
        return img

    def _update_progress(
        self, callback: Optional[Callable], 
        processed: int, total: int
    ) -> None:
        """更新进度"""
        if callback:
            progress = int(processed / total * 100)
            callback(progress)
