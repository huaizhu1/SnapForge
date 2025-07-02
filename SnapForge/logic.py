# logic.py
import os
import shutil
import tempfile
from PIL import Image
import logging
from typing import Optional, Callable, Dict, Set, List, Tuple

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
        
        # 多帧图像格式
        self.animated_formats = {".gif", ".tiff"}

    def batch_process(
        self,
        directory: str,
        prefix: Optional[str] = None,
        start_number: int = 1,
        extension: str = ".jpg",
        convert_format: Optional[str] = None,
        quality: Optional[int] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        preserve_metadata: bool = True,
        original_file_action: str = "keep"  # "keep", "delete", "move_to_backup"
    ) -> Tuple[int, int]:
        """批量处理图片文件
        
        Args:
            directory: 处理目录
            prefix: 文件名前缀
            start_number: 起始编号
            extension: 处理的文件扩展名（带点）
            convert_format: 目标格式（如 "jpg" 或 ".jpg"）
            quality: 压缩质量（1-100）
            progress_callback: 进度回调函数
            preserve_metadata: 是否保留元数据
            original_file_action: 原始文件处理方式 ("keep"保留, "delete"删除, "move_to_backup"移动到备份目录)
            
        Returns:
            (处理成功的文件数量, 总文件数量)
        """
        # 规范化扩展名
        extension = self._normalize_extension(extension)
        if not extension or extension not in self.supported_formats:
            logging.error(f"无效或不支持的文件扩展名: {extension}")
            if progress_callback:
                progress_callback(100)
            return (0, 0)
            
        # 验证目标格式
        target_ext = None
        if convert_format:
            target_ext = self._normalize_extension(convert_format)
            if not target_ext or target_ext not in self.supported_formats:
                logging.error(f"无效或不支持的转换格式: {convert_format}")
                if progress_callback:
                    progress_callback(100)
                return (0, 0)

        # 创建备份目录（如果需要）
        backup_dir = None
        if original_file_action == "move_to_backup":
            backup_dir = os.path.join(directory, "original_files_backup")
            os.makedirs(backup_dir, exist_ok=True)

        # 过滤文件（不区分大小写）
        files = []
        for f in os.listdir(directory):
            full_path = os.path.join(directory, f)
            if os.path.isfile(full_path):
                file_ext = self._normalize_extension(os.path.splitext(f)[1])
                if file_ext == extension:
                    files.append(f)
        
        total_files = len(files)
        if not files:
            logging.warning(f"目录中没有找到匹配 {extension} 的文件: {directory}")
            if progress_callback:
                progress_callback(100)
            return (0, 0)

        processed = 0
        created_files = set()  # 跟踪已创建的文件名，避免重名覆盖

        # 创建临时目录用于安全处理
        with tempfile.TemporaryDirectory(prefix="imgproc_", dir=directory) as temp_dir:
            for index, filename in enumerate(files):
                try:
                    file_path = os.path.join(directory, filename)
                    
                    # 处理原始文件（备份或删除）
                    if original_file_action == "move_to_backup" and backup_dir:
                        shutil.move(file_path, os.path.join(backup_dir, filename))
                        file_path = os.path.join(backup_dir, filename)
                    elif original_file_action == "delete":
                        # 先移动到临时目录，处理后再删除
                        temp_original = os.path.join(temp_dir, f"original_{filename}")
                        shutil.move(file_path, temp_original)
                        file_path = temp_original
                    
                    # 处理文件名
                    new_filename = self._generate_filename(
                        prefix, start_number + index, 
                        target_ext or extension, directory
                    )
                    
                    # 临时保存路径
                    temp_path = os.path.join(temp_dir, new_filename)
                    
                    # 处理并保存图像
                    self._process_image(
                        file_path, temp_path, 
                        target_ext, quality, preserve_metadata
                    )
                    
                    # 移动回原目录
                    final_path = os.path.join(directory, new_filename)
                    shutil.move(temp_path, final_path)
                    
                    # 删除原始文件（如果选择删除）
                    if original_file_action == "delete":
                        os.remove(file_path)
                    
                    processed += 1
                    
                except (IOError, OSError) as e:
                    logging.error(f"文件I/O错误: {filename} - {str(e)}")
                except Image.DecompressionBombError:
                    logging.error(f"图像解压错误: {filename} 可能过大或损坏")
                except Exception as e:
                    logging.error(f"处理文件 {filename} 失败: {str(e)}", exc_info=True)
                finally:
                    # 更新进度
                    self._update_progress(progress_callback, index + 1, total_files)

        return (processed, total_files)

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
        target_dir: str
    ) -> str:
        """生成唯一的新文件名"""
        base_name = f"{prefix}_{number:04d}" if prefix else f"{number:04d}"
        new_name = f"{base_name}{extension}"
        
        # 检查目标目录中是否已存在同名文件
        counter = 1
        while os.path.exists(os.path.join(target_dir, new_name)):
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1
            
        return new_name

    def _process_image(
        self,
        src_path: str,
        dest_path: str,
        target_ext: Optional[str],
        quality: Optional[int],
        preserve_metadata: bool
    ) -> None:
        """处理并保存单张图片"""
        file_ext = self._normalize_extension(os.path.splitext(src_path)[1])
        
        # 处理多帧图像（GIF/TIFF）
        if file_ext in self.animated_formats:
            self._process_animated_image(src_path, dest_path, target_ext, quality, preserve_metadata)
        else:
            self._process_single_frame_image(src_path, dest_path, target_ext, quality, preserve_metadata)

    def _process_single_frame_image(
        self,
        src_path: str,
        dest_path: str,
        target_ext: Optional[str],
        quality: Optional[int],
        preserve_metadata: bool
    ) -> None:
        """处理单帧图片"""
        with Image.open(src_path) as img:
            # 保存元数据
            exif_data = img.info.get("exif") if preserve_metadata else None
            
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
                if target_ext in (".jpg", ".jpeg", ".webp"):
                    save_params["quality"] = max(1, min(100, quality))
                elif target_ext == ".png":
                    # 将0-100质量转换为0-9压缩级别（反向关系）
                    # 质量100 -> 压缩级别0（无压缩）
                    # 质量0 -> 压缩级别9（最高压缩）
                    save_params["compress_level"] = min(9, max(0, 9 - quality // 11))
            
            # 添加元数据
            if exif_data:
                save_params["exif"] = exif_data
            
            img.save(dest_path, **save_params)

    def _process_animated_image(
        self,
        src_path: str,
        dest_path: str,
        target_ext: Optional[str],
        quality: Optional[int],
        preserve_metadata: bool
    ) -> None:
        """处理多帧图片（GIF/TIFF）"""
        # 对于多帧图像，我们只处理第一帧作为简化实现
        # 实际应用中可能需要更复杂的处理
        with Image.open(src_path) as img:
            # 获取第一帧
            img.seek(0)
            
            # 保存元数据
            exif_data = img.info.get("exif") if preserve_metadata else None
            
            # 转换图像模式
            img = self._convert_image_mode(img, target_ext)
            
            # 准备保存参数
            save_params = {}
            if target_ext:
                pil_format = self.format_mapping.get(target_ext)
                if pil_format:
                    save_params["format"] = pil_format
            
            # 设置质量参数
            if quality is not None:
                if target_ext in (".jpg", ".jpeg", ".webp"):
                    save_params["quality"] = max(1, min(100, quality))
                elif target_ext == ".png":
                    save_params["compress_level"] = min(9, max(0, 9 - quality // 11))
            
            # 添加元数据
            if exif_data:
                save_params["exif"] = exif_data
            
            img.save(dest_path, **save_params)
            
            # 记录警告，因为多帧图像没有被完整处理
            logging.warning(f"多帧图像 {os.path.basename(src_path)} 只处理了第一帧。完整处理需要更复杂的实现。")

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
