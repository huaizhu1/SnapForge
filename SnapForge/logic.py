import os
import shutil
import tempfile
from PIL import Image
import logging
from typing import Optional, Callable, Tuple, List

class ProcessLog:
    def __init__(self):
        self.entries = []
    def add(self, msg: str):
        self.entries.append(msg)
    def get_text(self):
        return '\n'.join(self.entries)

class ImageProcessor:
    def __init__(self):
        self.supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
        self.format_mapping = {
            ".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG",
            ".bmp": "BMP", ".gif": "GIF", ".tiff": "TIFF", ".webp": "WEBP"
        }
        self.animated_formats = {".gif", ".tiff"}

    def batch_process(
        self,
        files: List[str],
        prefix: Optional[str] = None,
        start_number: int = 1,
        extension: Optional[str] = None,
        convert_format: Optional[str] = None,
        quality: Optional[int] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        preserve_metadata: bool = True,
        original_file_action: str = "keep",
        resize_enabled: bool = False,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
        resize_mode: str = "fit",
        resize_only_shrink: bool = True,
        process_log: Optional[ProcessLog] = None
    ) -> Tuple[int, int]:
        if extension:
            extension = self._normalize_extension(extension)
        if convert_format:
            convert_format = self._normalize_extension(convert_format)
        processed = 0
        total_files = len(files)
        backup_dir = None
        if total_files == 0:
            if progress_callback:
                progress_callback(100)
            return (0, 0)
        if original_file_action == "move_to_backup":
            backup_dir = os.path.join(os.path.dirname(files[0]), "original_files_backup")
            os.makedirs(backup_dir, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="imgproc_", dir=os.path.dirname(files[0])) as temp_dir:
            for index, file_path in enumerate(files):
                try:
                    file_ext = self._normalize_extension(os.path.splitext(file_path)[1])
                    if extension and file_ext != extension:
                        if process_log: process_log.add(f"跳过: {file_path}（类型不符）")
                        continue
                    try:
                        with Image.open(file_path) as test_img:
                            test_img.verify()
                    except Exception:
                        if process_log: process_log.add(f"跳过: {file_path}（不是有效图片）")
                        continue
                    # 备份或删除原文件
                    if original_file_action == "move_to_backup" and backup_dir:
                        filename = os.path.basename(file_path)
                        backup_target = os.path.join(backup_dir, filename)
                        if os.path.exists(backup_target):
                            os.remove(backup_target)
                        shutil.move(file_path, backup_target)
                        file_path = backup_target
                    elif original_file_action == "delete":
                        temp_original = os.path.join(temp_dir, f"original_{os.path.basename(file_path)}")
                        shutil.move(file_path, temp_original)
                        file_path = temp_original
                    # 生成新文件名，防止覆盖
                    new_filename = self._generate_filename(
                        prefix, start_number + processed,
                        convert_format or file_ext, os.path.dirname(file_path)
                    )
                    temp_path = os.path.join(temp_dir, new_filename)
                    self._process_image(
                        file_path, temp_path,
                        convert_format, quality, preserve_metadata,
                        resize_enabled, resize_width, resize_height, resize_mode, resize_only_shrink
                    )
                    final_path = os.path.join(os.path.dirname(file_path), new_filename)
                    if os.path.abspath(file_path) == os.path.abspath(final_path):
                        # 直接覆盖（如仅压缩/尺寸调整），用临时文件替换
                        shutil.move(temp_path, final_path)
                    elif os.path.exists(final_path):
                        # 避免覆盖
                        os.remove(final_path)
                        shutil.move(temp_path, final_path)
                    else:
                        shutil.move(temp_path, final_path)
                    if original_file_action == "delete":
                        os.remove(file_path)
                    processed += 1
                    if process_log: process_log.add(f"成功: {os.path.basename(file_path)} → {new_filename}")
                except Exception as e:
                    if process_log: process_log.add(f"失败: {os.path.basename(file_path)}，原因: {str(e)}")
                finally:
                    self._update_progress(progress_callback, index + 1, total_files)
        return (processed, total_files)

    def _normalize_extension(self, ext: str) -> Optional[str]:
        if not ext:
            return None
        if not ext.startswith("."):
            ext = "." + ext
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
        base_name = f"{prefix}_{number:04d}" if prefix else f"{number:04d}"
        new_name = f"{base_name}{extension}"
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
        preserve_metadata: bool,
        resize_enabled: bool = False,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
        resize_mode: str = "fit",
        resize_only_shrink: bool = True,
    ) -> None:
        file_ext = self._normalize_extension(os.path.splitext(src_path)[1])
        if file_ext in self.animated_formats:
            self._process_animated_image(src_path, dest_path, target_ext, quality, preserve_metadata,
                                         resize_enabled, resize_width, resize_height, resize_mode, resize_only_shrink)
        else:
            self._process_single_frame_image(src_path, dest_path, target_ext, quality, preserve_metadata,
                                             resize_enabled, resize_width, resize_height, resize_mode, resize_only_shrink)

    def _process_single_frame_image(
        self,
        src_path: str,
        dest_path: str,
        target_ext: Optional[str],
        quality: Optional[int],
        preserve_metadata: bool,
        resize_enabled: bool = False,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
        resize_mode: str = "fit",
        resize_only_shrink: bool = True,
    ) -> None:
        with Image.open(src_path) as img:
            exif_data = img.info.get("exif") if preserve_metadata else None
            img = self._convert_image_mode(img, target_ext)
            if resize_enabled and resize_width and resize_height:
                img = self._resize_image(img, resize_width, resize_height, resize_mode, resize_only_shrink)
            save_params = {}
            if target_ext:
                pil_format = self.format_mapping.get(target_ext)
                if pil_format:
                    save_params["format"] = pil_format
            if quality is not None:
                if target_ext in (".jpg", ".jpeg", ".webp"):
                    save_params["quality"] = max(1, min(100, quality))
                elif target_ext == ".png":
                    save_params["compress_level"] = min(9, max(0, 9 - quality // 11))
            if exif_data:
                save_params["exif"] = exif_data
            img.save(dest_path, **save_params)

    def _process_animated_image(
        self,
        src_path: str,
        dest_path: str,
        target_ext: Optional[str],
        quality: Optional[int],
        preserve_metadata: bool,
        resize_enabled: bool = False,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
        resize_mode: str = "fit",
        resize_only_shrink: bool = True,
    ) -> None:
        with Image.open(src_path) as img:
            img.seek(0)
            exif_data = img.info.get("exif") if preserve_metadata else None
            img = self._convert_image_mode(img, target_ext)
            if resize_enabled and resize_width and resize_height:
                img = self._resize_image(img, resize_width, resize_height, resize_mode, resize_only_shrink)
            save_params = {}
            if target_ext:
                pil_format = self.format_mapping.get(target_ext)
                if pil_format:
                    save_params["format"] = pil_format
            if quality is not None:
                if target_ext in (".jpg", ".jpeg", ".webp"):
                    save_params["quality"] = max(1, min(100, quality))
                elif target_ext == ".png":
                    save_params["compress_level"] = min(9, max(0, 9 - quality // 11))
            if exif_data:
                save_params["exif"] = exif_data
            img.save(dest_path, **save_params)
            # 不处理所有帧，提示用户
            logging.warning(f"多帧图像 {os.path.basename(src_path)} 只处理了第一帧。")

    def _convert_image_mode(self, img: Image.Image, target_ext: Optional[str]) -> Image.Image:
        if not target_ext:
            return img
        if target_ext in (".jpg", ".jpeg"):
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1])
                return background
            if img.mode == "CMYK":
                return img.convert("RGB")
        return img

    def _resize_image(
        self, 
        img: Image.Image, 
        width: int, 
        height: int, 
        mode: str = "fit", 
        only_shrink: bool = True
    ) -> Image.Image:
        orig_w, orig_h = img.size
        if only_shrink and orig_w <= width and orig_h <= height:
            return img
        if mode == "fit":
            img_copy = img.copy()
            img_copy.thumbnail((width, height), Image.LANCZOS)
            return img_copy
        elif mode == "fill":
            ratio = max(width / orig_w, height / orig_h)
            new_size = (int(orig_w * ratio), int(orig_h * ratio))
            img2 = img.resize(new_size, Image.LANCZOS)
            left = (img2.width - width) // 2
            top = (img2.height - height) // 2
            return img2.crop((left, top, left + width, top + height))
        elif mode == "pad":
            img_copy = img.copy()
            img_copy.thumbnail((width, height), Image.LANCZOS)
            new_img = Image.new("RGB", (width, height), (255, 255, 255))
            offset_x = (width - img_copy.width) // 2
            offset_y = (height - img_copy.height) // 2
            new_img.paste(img_copy, (offset_x, offset_y))
            return new_img
        elif mode == "crop":
            left = max(0, (orig_w - width) // 2)
            top = max(0, (orig_h - height) // 2)
            return img.crop((left, top, left + width, top + height))
        else:
            return img

    def _update_progress(
        self, callback: Optional[Callable], 
        processed: int, total: int
    ) -> None:
        if callback:
            progress = int(processed / total * 100)
            callback(progress)
