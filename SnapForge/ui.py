import os
import streamlit as st
import tempfile
import shutil
import zipfile
import io
from logic import (
    ImageProcessor, ProcessLog, find_duplicate_images,
    ai_image_recognition_cloud, get_exif_data, get_image_main_color, plot_image_histogram
)
from PIL import Image

# ------------------- 全局UI美化CSS -------------------
custom_css = """
<style>
body { background: #f3f6fa; }
.header-banner {margin-top: -2.5rem;margin-bottom: 2.5rem;padding: 36px 0 28px 0;background: linear-gradient(90deg, #406aff 0%, #5cc6fa 100%);border-radius: 1.2rem;box-shadow: 0 4px 24px 0 #406aff22;color: #fff;text-align: center;position: relative;}
.header-banner .logo {font-size: 3.6rem;line-height: 1;margin-bottom: 6px;}
.header-banner h1 {font-size: 2.6rem;font-weight: 850;letter-spacing: 1.2px;margin-bottom: 8px;font-family: 'Segoe UI', 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;}
.header-banner .subtitle {font-size: 1.15rem;font-weight: 500;letter-spacing: 0.2px;margin-bottom: 0;}
.gh-btn-area {margin: 1.3rem auto 0.7rem auto;display: flex;justify-content: center;align-items: center;gap: 1.2em;}
.gh-btn-area a {background: #fff;color: #406aff;font-weight: 700;padding: 0.5em 1.7em;border-radius: 2em;box-shadow: 0 2px 14px #406aff25;font-size: 1.08rem;text-decoration: none;transition: background 0.15s, color 0.15s;border: 2px solid #5cc6fa;}
.gh-btn-area a:hover {background: #406aff;color: #fff;border: 2px solid #406aff;}
.gh-author {display: flex;flex-direction: row;align-items: center;justify-content: center;margin-bottom: 0.6rem;gap: 0.6em;font-size: 1.05rem;}
.gh-author img {border-radius: 50%;border: 2px solid #fff;width: 34px;height: 34px;box-shadow: 0 2px 10px #406aff22;margin-right: 0.4em;}
.main-card {background: #fff;border-radius: 1.2rem;padding: 2.2rem 2rem 1.5rem 2rem;margin: 0 auto 2rem auto;box-shadow: 0 2px 16px 0 #406aff10;max-width: 780px;}
.card h3 {font-size: 1.35rem;font-weight: 700;margin-bottom: 1.25rem;color: #406aff;}
.stButton>button, .stDownloadButton>button {border-radius: 1.8rem;font-weight: 700;font-size: 1.1rem;min-height: 2.7rem;box-shadow: 0 2px 12px 0 #406aff22;transition: 0.2s;}
.stButton>button:hover, .stDownloadButton>button:hover {background: #406aff;color: #fff;}
.stSlider {padding-bottom: 1.0rem;}
.stProgress > div > div {border-radius: 1rem;}
.stTextInput>div>input, .stNumberInput>div>input, .stSelectbox>div>div>div {border-radius: 0.7rem;min-height: 2.3rem;}
.stAlert {border-radius: 1rem;}
.stTextArea>div>textarea {border-radius: 0.7rem;min-height: 8rem;font-size: 1.03rem;}
.res-card {background:linear-gradient(100deg,#e9f2fe 0%,#e8fcff 100%);border-radius: 1.2rem;padding: 1.5rem 1.5rem 1.3rem 1.5rem;margin: 1.3rem 0;box-shadow: 0 2px 14px 0 #406aff14;}
.footer {margin-top: 2.5rem;padding: 0.8rem 0;color: #b1b4bb;text-align: center;font-size: 1.02rem;}
@media (max-width: 800px) {.header-banner { font-size: 1.8rem; padding: 28px 0 18px 0; }.main-card { padding: 1.1rem 0.7rem 1rem 0.7rem; }.res-card { padding: 1.0rem 0.4rem 1.0rem 0.4rem; }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ------------------- 顶部Banner -------------------
st.markdown("""
<div class="header-banner">
    <div class="logo">🖼️⚒️</div>
    <h1>SnapForge</h1>
    <div class="subtitle">
        <b>高效、专业、美观的批量/单文件图片处理平台</b><br>
        <span style="opacity:.85">一个完全开源的图像处理项目，支持多种格式转换、压缩与高级操作</span>
    </div>
    <div class="gh-btn-area">
        <a href="https://github.com/riceshowerX/SnapForge" target="_blank" title="前往GitHub仓库">GitHub仓库主页</a>
        <a href="https://github.com/riceshowerX/SnapForge/issues/new/choose" target="_blank" title="反馈建议/提Issue">反馈建议</a>
    </div>
    <div class="gh-author">
        <img src="https://avatars.githubusercontent.com/u/46900545?v=4" alt="riceshowerX头像">
        <span>
            由 <a href="https://github.com/riceshowerX" target="_blank" style="color:#fff;text-decoration:underline;font-weight:600;">riceshowerX</a> 开发 &nbsp;|&nbsp; <a href="https://github.com/riceshowerX/SnapForge" target="_blank" style="color:#fff;text-decoration:underline;">@SnapForge</a>
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-card">', unsafe_allow_html=True)
tab_titles = ["批量/单文件图片处理", "图片信息查看", "图片去重", "AI识别"]
tabs = st.tabs(tab_titles)

# ------------------- Tab 0: 批量/单文件图片处理 -------------------
with tabs[0]:
    processor = ImageProcessor()

    def save_uploaded_files(files, temp_dir):
        file_paths = []
        for f in files:
            file_name = os.path.basename(f.name)
            file_name = "".join(x for x in file_name if x.isalnum() or x in "._-")
            temp_path = os.path.join(temp_dir, file_name)
            with open(temp_path, "wb") as out:
                out.write(f.read())
            file_paths.append(temp_path)
        return file_paths

    def pack_files_to_zip(file_paths):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for file in file_paths:
                zipf.write(file, arcname=os.path.basename(file))
        zip_buffer.seek(0)
        return zip_buffer

    def get_extension(path_or_file):
        name = path_or_file.name if hasattr(path_or_file, "name") else path_or_file
        return os.path.splitext(name)[1].lower()

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3>📂 上传图片 & 选择模式</h3>', unsafe_allow_html=True)
        col_mode, col_tip = st.columns([2,1])
        with col_mode:
            mode = st.radio("处理模式", ["批量处理（多文件上传）", "单文件处理"], horizontal=True)
        with col_tip:
            st.info("单图片请选“单文件处理”，批量请选“批量处理”", icon="📁")

        files = []
        extension = None

        if mode == "批量处理（多文件上传）":
            files = st.file_uploader("上传图片文件", type=["jpg","jpeg","png","bmp","gif","tiff","webp"], accept_multiple_files=True, help="多选支持 Ctrl 或 Shift")
            extension = st.selectbox("仅处理指定类型", [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"], index=0)
        else:
            one_file = st.file_uploader("上传一个图片文件", type=["jpg","jpeg","png","bmp","gif","tiff","webp"], accept_multiple_files=False)
            if one_file:
                files = [one_file]
            extension = None
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3>🛠️ 图片处理参数</h3>', unsafe_allow_html=True)
        with st.expander("重命名、格式转换与压缩", expanded=True):
            para1, para2, para3 = st.columns([2,2,2])
            with para1:
                enable_rename = st.checkbox("启用重命名", value=True)
                prefix = st.text_input("文件名前缀", "image", disabled=not enable_rename)
                start_num = st.number_input("起始编号", min_value=1, value=1, disabled=not enable_rename)
            with para2:
                enable_convert = st.checkbox("启用格式转换")
                target_ext = st.selectbox("目标格式", [".jpg",".jpeg",".png",".bmp",".gif",".tiff",".webp"], index=2, disabled=not enable_convert)
            with para3:
                enable_compress = st.checkbox("启用质量压缩")
                quality = st.slider("压缩质量 (1-100)", 1, 100, 85, disabled=not enable_compress)
                st.caption("💡 JPEG/WEBP用质量，PNG为压缩等级")
        with st.expander("尺寸调整与高级选项", expanded=False):
            para4, para5 = st.columns([2,2])
            with para4:
                enable_resize = st.checkbox("启用尺寸调整")
                resize_width = st.number_input("目标宽度(px)", min_value=1, value=800, disabled=not enable_resize)
                resize_height = st.number_input("目标高度(px)", min_value=1, value=600, disabled=not enable_resize)
            with para5:
                resize_mode = st.selectbox(
                    "缩放模式",
                    ["等比缩放（fit）", "拉伸填充（fill）", "填充白边（pad）", "中心裁剪（crop）"],
                    disabled=not enable_resize
                )
                resize_only_shrink = st.checkbox("仅缩小不放大", value=True, disabled=not enable_resize)
            st.markdown("---")
            para6 = st.columns([2])[0]
            with para6:
                preserve_metadata = st.checkbox("保留元数据 (EXIF)", value=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card res-card">', unsafe_allow_html=True)
        st.markdown('<h3>📄 处理进度与结果</h3>', unsafe_allow_html=True)
        log_area = st.empty()
        progress_bar = st.empty()
        result_area = st.empty()
        download_area = st.empty()

        def streamlit_progress_callback(pct, filename=None):
            if filename:
                progress_bar.progress(pct, f"正在处理：{filename}")
            else:
                progress_bar.progress(pct)

        st.markdown('<hr>', unsafe_allow_html=True)
        btn_cols = st.columns([2,5,2])
        with btn_cols[1]:
            run_btn = st.button("🚀 开始处理图片", type="primary", use_container_width=True, disabled=not files)

        if run_btn:
            if not files or (mode == "批量处理（多文件上传）" and len(files) == 0):
                result_area.warning("请先上传图片文件！", icon="⚠️")
            else:
                # 合法性检查
                if enable_resize and (resize_width < 1 or resize_height < 1):
                    result_area.error("目标宽或高必须为正整数！", icon="❌")
                    st.stop()
                # 保存上传文件
                temp_dir = tempfile.mkdtemp()
                try:
                    file_paths = save_uploaded_files(files, temp_dir)
                    if mode == "批量处理（多文件上传）" and extension:
                        selected_paths = [f for f in file_paths if get_extension(f) == extension]
                        if not selected_paths:
                            result_area.error(f"没有找到扩展名为{extension}的文件。", icon="❌")
                            shutil.rmtree(temp_dir)
                            st.stop()
                        file_paths = selected_paths
                    resize_modes = {
                        0: "fit",
                        1: "fill",
                        2: "pad",
                        3: "crop"
                    }
                    log = ProcessLog()
                    args = {
                        'files': file_paths,
                        'prefix': prefix if enable_rename else '',
                        'start_number': start_num if enable_rename else 1,
                        'extension': extension if extension else get_extension(file_paths[0]),
                        'convert_format': target_ext if enable_convert else '',
                        'quality': quality if enable_compress else None,
                        'progress_callback': streamlit_progress_callback,
                        'preserve_metadata': preserve_metadata,
                        'resize_enabled': enable_resize,
                        'resize_width': resize_width if enable_resize else None,
                        'resize_height': resize_height if enable_resize else None,
                        'resize_mode': resize_modes[["等比缩放（fit）","拉伸填充（fill）","填充白边（pad）","中心裁剪（crop）"].index(resize_mode)] if enable_resize else "fit",
                        'resize_only_shrink': resize_only_shrink if enable_resize else True,
                        'process_log': log
                    }
                    with st.spinner("图片处理中，请稍候..."):
                        result_area.info("正在处理图片，请耐心等待...", icon="⏳")
                        processed, total_files, result_file_paths = processor.batch_process(**args)
                        progress_bar.progress(100)
                        log_area.text_area("处理日志", log.get_text(), height=200)
                        if processed == 0:
                            result_area.error("❌ 未成功处理任何图片，请检查日志与参数。")
                        elif processed < total_files:
                            result_area.warning(f"⚠️ 有部分图片未处理成功：{processed}/{total_files}")
                        else:
                            result_area.success(f"✅ 处理完成：{processed}/{total_files} 个文件")
                        if result_file_paths:
                            zip_buffer = pack_files_to_zip(result_file_paths)
                            download_area.download_button(
                                label="⬇️ 下载全部处理结果（zip包）",
                                data=zip_buffer,
                                file_name="处理结果.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                except Exception as e:
                    result_area.error(f"处理过程中发生错误: {e}", icon="❗")
                    log_area.text_area("日志", log.get_text() if 'log' in locals() else str(e), height=200)
                    import traceback
                    st.error(traceback.format_exc())
                finally:
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
        else:
            result_area.info("请上传图片并设置参数后，点击【开始处理图片】", icon="ℹ️")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------- Tab 1: 图片信息查看（升级版） -------------------
with tabs[1]:
    st.subheader("图片信息查看（升级版）")
    uploaded = st.file_uploader("上传图片查看信息", type=["jpg","jpeg","png","bmp","gif","tiff","webp"])
    if uploaded:
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, uploaded.name)
        with open(temp_path, "wb") as out:
            out.write(uploaded.read())
        img = Image.open(temp_path)
        st.image(img, caption="图片预览")

        # 文件和基础信息
        st.write(f"**尺寸**: {img.size}  |  **模式**: {img.mode}  |  **格式**: {img.format}")
        st.write(f"**文件大小**: {os.path.getsize(temp_path)//1024} KB")
        dpi = img.info.get("dpi")
        if dpi: st.write("**DPI**:", dpi)

        # EXIF数据
        exif_data = get_exif_data(temp_path)
        if exif_data:
            with st.expander("EXIF详细信息"):
                for k,v in exif_data.items():
                    st.write(f"`{k}`: {v}")
                if "GPSLatitude" in exif_data and "GPSLongitude" in exif_data:
                    lat = exif_data["GPSLatitude"]
                    lon = exif_data["GPSLongitude"]
                    st.markdown(f"[在地图中查看](https://maps.google.com/?q={lat},{lon})")
                st.download_button("导出EXIF为JSON", data=str(exif_data), file_name="exif.json")
        else:
            st.info("无EXIF元数据")

        # 主色与色板
        dom_color, palette = get_image_main_color(temp_path)
        if dom_color:
            st.write("**主色调**:")
            st.markdown(f'<div style="width:50px;height:30px;background:rgb{dom_color};display:inline-block;border-radius:3px;border:1px solid #888"></div>', unsafe_allow_html=True)
            st.write("**色板**:")
            for col in palette:
                st.markdown(f'<div style="width:30px;height:20px;background:rgb{col};display:inline-block;border-radius:2px;border:1px solid #ccc"></div>', unsafe_allow_html=True)
        else:
            st.info("无法获取主色信息")

        # 直方图
        buf = plot_image_histogram(temp_path)
        if buf:
            st.image(buf, caption="RGB直方图", use_column_width=False)
        else:
            st.info("无法生成直方图")

        # 动图帧数
        if getattr(img, "is_animated", False):
            st.write(f"**帧数**: {img.n_frames}")
        st.info("如需更多元数据支持或可视化对比，请提出需求！")
        shutil.rmtree(temp_dir)

# ------------------- Tab 2: 图片去重 -------------------
with tabs[2]:
    st.subheader("图片去重")
    files = st.file_uploader("上传需去重的图片", type=["jpg","jpeg","png","bmp","gif","tiff","webp"], accept_multiple_files=True)
    threshold = st.slider("相似度阈值(越低越严格)", 0, 20, 8)
    run_btn = st.button("开始去重", use_container_width=True, disabled=not files)
    if run_btn and files:
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        for f in files:
            path = os.path.join(temp_dir, f.name)
            with open(path, "wb") as out:
                out.write(f.read())
            file_paths.append(path)
        with st.spinner("正在查找重复图片..."):
            dups = find_duplicate_images(file_paths, threshold)
            if not dups:
                st.success("未检测到重复图片。")
            else:
                st.warning(f"检测到 {len(dups)} 组重复图片：")
                for group in dups:
                    cols = st.columns(len(group))
                    for idx, path in enumerate(group):
                        img = Image.open(path)
                        cols[idx].image(img, caption=os.path.basename(path), width=120)
                st.info("请手动删除或下载需要保留/去除的图片。")
        shutil.rmtree(temp_dir)

# ------------------- Tab 3: AI识别 -------------------
with tabs[3]:
    st.subheader("AI识别 - 云端图片内容标签")
    files = st.file_uploader("上传图片进行AI识别", type=["jpg","jpeg","png","bmp","gif","tiff","webp"], accept_multiple_files=True)
    provider = st.selectbox("选择AI识别服务", ["baidu", "aliyun", "tencent", "azure", "google", "deepseek"])
    api_params = {}
    if provider == "baidu":
        api_params["app_id"] = st.text_input("Baidu App ID")
        api_params["api_key"] = st.text_input("Baidu API Key")
        api_params["secret_key"] = st.text_input("Baidu Secret Key")
    elif provider == "aliyun":
        api_params["access_key_id"] = st.text_input("Aliyun Access Key ID")
        api_params["access_key_secret"] = st.text_input("Aliyun Access Key Secret")
        api_params["region_id"] = st.text_input("Aliyun Region ID", value="cn-shanghai")
    elif provider == "tencent":
        api_params["secret_id"] = st.text_input("Tencent Secret ID")
        api_params["secret_key"] = st.text_input("Tencent Secret Key")
        api_params["region"] = st.text_input("Tencent Region", value="ap-guangzhou")
    elif provider == "azure":
        api_params["subscription_key"] = st.text_input("Azure Subscription Key")
        api_params["endpoint"] = st.text_input("Azure Endpoint")
    elif provider == "google":
        api_params["credentials_json"] = st.text_input("Google Cloud credentials.json 路径")
    elif provider == "deepseek":
        api_params["api_key"] = st.text_input("DeepSeek API Key")
        api_params["endpoint"] = st.text_input("DeepSeek Endpoint", value="https://api.deepseek.com/v1/vision/detect")
    run_btn = st.button("开始AI识别", use_container_width=True, disabled=not files)
    if run_btn and files:
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        for f in files:
            path = os.path.join(temp_dir, f.name)
            with open(path, "wb") as out:
                out.write(f.read())
            file_paths.append(path)
        with st.spinner("正在识别图片内容..."):
            try:
                results = ai_image_recognition_cloud(file_paths, provider=provider, **api_params)
                for path, tags in results.items():
                    st.image(path, caption=os.path.basename(path), width=180)
                    st.write("识别标签：", ", ".join(tags))
            except Exception as e:
                st.error(f"AI识别调用失败: {e}")
        shutil.rmtree(temp_dir)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    <span>© 2025 <b>SnapForge</b> | <a href="https://github.com/riceshowerX/SnapForge" target="_blank" style="color:#406aff;text-decoration:none;font-weight:500;">GitHub开源项目</a> | 设计&开发：<a href="https://github.com/riceshowerX" target="_blank" style="color:#406aff;text-decoration:none;font-weight:500;">riceshowerX</a>
    </span>
</div>
""", unsafe_allow_html=True)
