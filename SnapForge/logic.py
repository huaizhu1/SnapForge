import os
import shutil
import tempfile
from PIL import Image
import logging
from typing import Optional, Callable, Tuple, List, Dict

import imagehash  # pip install ImageHash
from collections import defaultdict

import piexif
from colorthief import ColorThief
import matplotlib.pyplot as plt
import io

class ProcessLog:
    def __init__(self):
        self.entries = []
    def add(self, msg: str, level: str = "info"):
        prefix = {"info": "✅", "warn": "⚠️", "error": "❌", "skip": "⏩"}.get(level, "")
        self.entries.append(f"{prefix} {msg}")
    def get_text(self) -> str:
        return "\n".join(self.entries)

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
        progress_callback: Optional[Callable[[int, str], None]] = None,
        preserve_metadata: bool = True,
        resize_enabled: bool = False,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
        resize_mode: str = "fit",
        resize_only_shrink: bool = True,
        process_log: Optional[ProcessLog] = None
    ) -> Tuple[int, int, List[str]]:
        # ======= 移除无意义的“原文件处理”参数和逻辑 =======
        if extension:
            extension = self._normalize_extension(extension)
        if convert_format:
            convert_format = self._normalize_extension(convert_format)
        processed = 0
        total_files = len(files)
        result_paths = []
        if total_files == 0:
            if progress_callback:
                progress_callback(100, "")
            return (0, 0, [])
        with tempfile.TemporaryDirectory(prefix="imgproc_", dir=os.path.dirname(files[0])) as temp_dir:
            for index, file_path in enumerate(files):
                filename = os.path.basename(file_path)
                filename = "".join(x for x in filename if x.isalnum() or x in "._-")
                try:
                    file_ext = self._normalize_extension(os.path.splitext(file_path)[1])
                    # 类型过滤后端再做一次
                    if extension and file_ext != extension:
                        if process_log: process_log.add(f"跳过: {filename}（类型不符，仅处理{extension}）", level="skip")
                        continue
                    try:
                        with Image.open(file_path) as test_img:
                            test_img.verify()
                    except Exception:
                        if process_log: process_log.add(f"跳过: {filename}（不是有效图片）", level="skip")
                        continue
                    # 尺寸参数合法性
                    if resize_enabled and (not resize_width or not resize_height or resize_width < 1 or resize_height < 1):
                        if process_log: process_log.add(f"跳过: {filename}（非法尺寸参数）", level="skip")
                        continue
                    # 格式转换优化
                    if convert_format and file_ext == convert_format and not quality:
                        if process_log: process_log.add(f"跳过: {filename}（输入输出格式相同且无压缩变更）", level="skip")
                        continue
                    # 生成新文件名
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
                        shutil.move(temp_path, final_path)
                    elif os.path.exists(final_path):
                        os.remove(final_path)
                        shutil.move(temp_path, final_path)
                    else:
                        shutil.move(temp_path, final_path)
                    processed += 1
                    result_paths.append(final_path)
                    # 动图处理日志
                    with Image.open(file_path) as img:
                        if getattr(img, "is_animated", False):
                            if process_log:
                                process_log.add(f"提示: {filename} 为动图，仅处理首帧。", level="warn")
                    if process_log: process_log.add(f"成功: {filename} → {new_filename}", level="info")
                except Exception as e:
                    if process_log: process_log.add(f"失败: {filename}，原因: {str(e)}", level="error")
                finally:
                    self._update_progress(progress_callback, index + 1, total_files, filename)
        return (processed, total_files, result_paths)

    def _normalize_extension(self, ext: str) -> Optional[str]:
        if not ext:
            return None
        ext = ext.lower()
        if not ext.startswith("."):
            ext = "." + ext
        if ext == ".jpeg":
            return ".jpg"
        return ext

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
        resize_only_shrink: bool = True
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
        resize_only_shrink: bool = True
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
        resize_only_shrink: bool = True
    ) -> None:
        # 只处理第一帧
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
        self, callback: Optional[Callable[[int, str], None]], 
        processed: int, total: int, filename: str = ""
    ) -> None:
        if callback:
            progress = int(processed / total * 100)
            callback(progress, filename)

def find_duplicate_images(file_paths: List[str], threshold: int = 8) -> List[List[str]]:
    hashes = {}
    groups = []
    for path in file_paths:
        try:
            with Image.open(path) as img:
                h = imagehash.phash(img)
            hashes[path] = h
        except Exception:
            continue
    used = set()
    for path1, hash1 in hashes.items():
        if path1 in used:
            continue
        group = [path1]
        for path2, hash2 in hashes.items():
            if path2 != path1 and path2 not in used and hash1 - hash2 <= threshold:
                group.append(path2)
                used.add(path2)
        if len(group) > 1:
            for p in group:
                used.add(p)
            groups.append(group)
    return groups

def get_exif_data(image_path):
    try:
        exif_dict = piexif.load(image_path)
        exif_data = {}
        for ifd in exif_dict:
            if isinstance(exif_dict[ifd], dict):
                for tag in exif_dict[ifd]:
                    tag_name = piexif.TAGS[ifd][tag]["name"]
                    value = exif_dict[ifd][tag]
                    if isinstance(value, bytes):
                        try:
                            value = value.decode()
                        except Exception:
                            value = str(value)
                    exif_data[tag_name] = value
        return exif_data
    except Exception:
        return {}

def get_image_main_color(image_path):
    try:
        ct = ColorThief(image_path)
        dom_color = ct.get_color(quality=1)
        palette = ct.get_palette(color_count=6)
        return dom_color, palette
    except Exception:
        return None, []

def plot_image_histogram(image_path):
    try:
        img = Image.open(image_path).convert('RGB')
        plt.figure(figsize=(4,1.5))
        color = ('r','g','b')
        for i,c in enumerate(color):
            histo = img.getchannel(i).histogram()
            plt.plot(histo, color=c, label=f"{c.upper()}")
        plt.legend()
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return buf
    except Exception:
        return None

def ai_image_recognition_cloud(file_paths: List[str], provider: str = "baidu", **provider_kwargs) -> Dict[str, List[str]]:
    """
    云端AI识别接口入口，根据provider参数调用不同云厂商API
    """
    if provider == "baidu":
        return ai_recognition_baidu(file_paths, **provider_kwargs)
    elif provider == "aliyun":
        return ai_recognition_aliyun(file_paths, **provider_kwargs)
    elif provider == "tencent":
        return ai_recognition_tencent(file_paths, **provider_kwargs)
    elif provider == "azure":
        return ai_recognition_azure(file_paths, **provider_kwargs)
    elif provider == "google":
        return ai_recognition_google(file_paths, **provider_kwargs)
    elif provider == "deepseek":
        return ai_recognition_deepseek(file_paths, **provider_kwargs)
    else:
        raise ValueError(f"不支持的AI识别服务提供商：{provider}")

def ai_recognition_baidu(file_paths, app_id=None, api_key=None, secret_key=None, **kwargs):
    try:
        from aip import AipImageClassify
    except ImportError:
        raise Exception("请先 pip install baidu-aip")
    client = AipImageClassify(app_id, api_key, secret_key)
    results = {}
    for path in file_paths:
        with open(path, 'rb') as f:
            img_data = f.read()
        res = client.advancedGeneral(img_data)
        tags = [item['keyword'] for item in res.get('result', [])]
        results[path] = tags or ["未识别"]
    return results

def ai_recognition_aliyun(file_paths, access_key_id=None, access_key_secret=None, region_id='cn-shanghai', **kwargs):
    # 伪代码，需替换为阿里云API真实调用
    results = {}
    for path in file_paths:
        results[path] = ["阿里云标签示例"]
    return results

def ai_recognition_tencent(file_paths, secret_id=None, secret_key=None, region='ap-guangzhou', **kwargs):
    # 伪代码，需替换为腾讯云API真实调用
    results = {}
    for path in file_paths:
        results[path] = ["腾讯云标签示例"]
    return results

def ai_recognition_azure(file_paths, subscription_key=None, endpoint=None, **kwargs):
    # 伪代码，需替换为Azure SDK真实调用
    results = {}
    for path in file_paths:
        results[path] = ["Azure标签示例"]
    return results

def ai_recognition_google(file_paths, credentials_json=None, **kwargs):
    # 伪代码，需替换为Google Cloud SDK真实调用
    results = {}
    for path in file_paths:
        results[path] = ["Google标签示例"]
    return results

def ai_recognition_deepseek(file_paths, api_key=None, endpoint=None, **kwargs):
    """
    DeepSeek Vision API调用示例
    假设 DeepSeek 官方提供了 RESTful API，需自行适配参数（api_key、endpoint）。
    """
    import requests
    results = {}
    for path in file_paths:
        with open(path, 'rb') as f:
            img_data = f.read()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/octet-stream"
        }
        url = endpoint or "https://api.deepseek.com/v1/vision/detect"
        try:
            response = requests.post(
                url,
                data=img_data,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            res = response.json()
            # 假设返回格式为 {'labels': [...]} 或 {'result': [{'label': 'xxx'}, ...]}
            if "labels" in res:
                tags = res["labels"]
            elif "result" in res:
                tags = [item.get("label", "") for item in res["result"]]
            else:
                tags = ["未识别"]
            results[path] = tags or ["未识别"]
        except Exception as e:
            results[path] = [f"调用失败: {e}"]
    return results
