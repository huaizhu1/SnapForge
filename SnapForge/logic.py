import os
from PIL import Image
import logging
from typing import Optional, Callable

class ImageProcessor:
    def __init__(self):
        self.supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"}

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
            extension: 处理的文件扩展名
            convert_format: 目标格式（如 png）
            quality: 压缩质量（1-95）
            progress_callback: 进度回调函数
            
        Returns:
            处理成功的文件数量
        """
        # 参数验证
        extension = extension.lower()
        if extension not in self.supported_formats:
            logging.error(f"不支持的文件格式: {extension}")
            return 0

        if convert_format:
            convert_format = convert_format.lower()
            if f".{convert_format}" not in self.supported_formats:
                logging.error(f"不支持的转换格式: {convert_format}")
                return 0

        # 过滤文件
        files = [
            f for f in os.listdir(directory)
            if f.lower().endswith(extension)
        ]
        total_files = len(files)
        processed = 0

        for index, filename in enumerate(files):
            try:
                file_path = os.path.join(directory, filename)
                with Image.open(file_path) as image:
                    # 处理文件名
                    new_filename = self._generate_filename(
                        prefix, start_number + index, 
                        extension, convert_format
                    )
                    new_path = os.path.join(directory, new_filename)
                    
                    # 处理格式转换和保存
                    save_params = self._prepare_save_params(
                        image, convert_format, quality
                    )
                    
                    image.save(new_path, **save_params)
                    
                processed += 1
                self._update_progress(progress_callback, processed, total_files)
                
            except Exception as e:
                logging.error(f"处理文件 {filename} 失败: {str(e)}")
                continue

        self._finalize_progress(progress_callback)
        return processed

    def _generate_filename(
        self, prefix: Optional[str], number: int,
        original_ext: str, target_format: Optional[str]
    ) -> str:
        """生成新文件名"""
        extension = target_format or original_ext
        if not prefix:
            return f"{number:04d}{extension}"
        return f"{prefix}_{number:04d}{extension}"

    def _prepare_save_params(
        self, image: Image.Image,
        target_format: Optional[str], quality: Optional[int]
    ) -> dict:
        """准备保存参数"""
        params = {}
        if target_format:
            params['format'] = target_format
        
        # 仅对JPEG格式应用质量参数
        if quality and target_format in ('jpg', 'jpeg'):
            params['quality'] = quality
            params['optimize'] = True  # 启用优化
        
        return params

    def _update_progress(
        self, callback: Optional[Callable], 
        processed: int, total: int
    ) -> None:
        """更新进度"""
        if callback:
            progress = int(processed / total * 100)
            callback(progress)

    def _finalize_progress(
        self, callback: Optional[Callable]
    ) -> None:
        """完成进度"""
        if callback:
            callback(100)