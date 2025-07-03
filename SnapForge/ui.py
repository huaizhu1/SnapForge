import os
import streamlit as st
import tempfile
import shutil
import zipfile
import io
from logic import ImageProcessor, ProcessLog
from PIL import Image

# =======================
# SnapForge 定制美观CSS（包含主内容区卡片样式）
# =======================
custom_css = """
<style>
body {
    background: #f3f6fa;
}
.header-banner {
    margin-top: -2.5rem;
    margin-bottom: 2.5rem;
    padding: 36px 0 28px 0;
    background: linear-gradient(90deg, #406aff 0%, #5cc6fa 100%);
    border-radius: 1.2rem;
    box-shadow: 0 4px 24px 0 #406aff22;
    color: #fff;
    text-align: center;
    position: relative;
}
.header-banner .logo {
    font-size: 3.6rem;
    line-height: 1;
    margin-bottom: 6px;
}
.header-banner h1 {
    font-size: 2.6rem;
    font-weight: 850;
    letter-spacing: 1.2px;
    margin-bottom: 8px;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.header-banner .subtitle {
    font-size: 1.15rem;
    font-weight: 500;
    letter-spacing: 0.2px;
    margin-bottom: 0;
}
.gh-btn-area {
    margin: 1.3rem auto 0.7rem auto;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1.2em;
}
.gh-btn-area a {
    background: #fff;
    color: #406aff;
    font-weight: 700;
    padding: 0.5em 1.7em;
    border-radius: 2em;
    box-shadow: 0 2px 14px #406aff25;
    font-size: 1.08rem;
    text-decoration: none;
    transition: background 0.15s, color 0.15s;
    border: 2px solid #5cc6fa;
}
.gh-btn-area a:hover {
    background: #406aff;
    color: #fff;
    border: 2px solid #406aff;
}
.gh-author {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.6rem;
    gap: 0.6em;
    font-size: 1.05rem;
}
.gh-author img {
    border-radius: 50%;
    border: 2px solid #fff;
    width: 34px;
    height: 34px;
    box-shadow: 0 2px 10px #406aff22;
    margin-right: 0.4em;
}
.main-card {
    background: #fff;
    border-radius: 1.2rem;
    padding: 2.2rem 2rem 1.5rem 2rem;
    margin: 0 auto 2rem auto;
    box-shadow: 0 2px 16px 0 #406aff10;
    max-width: 780px;
}
.card h3 {
    font-size: 1.35rem;
    font-weight: 700;
    margin-bottom: 1.25rem;
    color: #406aff;
}
.stButton>button, .stDownloadButton>button {
    border-radius: 1.8rem;
    font-weight: 700;
    font-size: 1.1rem;
    min-height: 2.7rem;
    box-shadow: 0 2px 12px 0 #406aff22;
    transition: 0.2s;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    background: #406aff;
    color: #fff;
}
.stSlider {
    padding-bottom: 1.0rem;
}
.stProgress > div > div {
    border-radius: 1rem;
}
.stTextInput>div>input, .stNumberInput>div>input, .stSelectbox>div>div>div {
    border-radius: 0.7rem;
    min-height: 2.3rem;
}
.stAlert {
    border-radius: 1rem;
}
.stTextArea>div>textarea {
    border-radius: 0.7rem;
    min-height: 8rem;
    font-size: 1.03rem;
}
.res-card {
    background:linear-gradient(100deg,#e9f2fe 0%,#e8fcff 100%);
    border-radius: 1.2rem;
    padding: 1.5rem 1.5rem 1.3rem 1.5rem;
    margin: 1.3rem 0;
    box-shadow: 0 2px 14px 0 #406aff14;
}
.footer {
    margin-top: 2.5rem;
    padding: 0.8rem 0;
    color: #b1b4bb;
    text-align: center;
    font-size: 1.02rem;
}
.exit-btn {
    display: flex;
    justify-content: center;
    margin-top: 1.2rem;
    margin-bottom: 0.8rem;
}
.exit-btn button {
    background: #fa5252;
    color: #fff;
    border: none;
    padding: 0.75em 2.7em;
    font-size: 1.18rem;
    border-radius: 2rem;
    font-weight: 700;
    box-shadow: 0 2px 12px #fa525277;
    cursor: pointer;
    transition: background 0.18s;
}
.exit-btn button:hover {
    background: #c92a2a;
}
.exit-note {
    text-align: center;
    color: #fa5252;
    margin-top: 0.5em;
    font-size: 1.07rem;
    font-weight: 500;
}
@media (max-width: 800px) {
    .header-banner { font-size: 1.8rem; padding: 28px 0 18px 0; }
    .main-card { padding: 1.1rem 0.7rem 1rem 0.7rem; }
    .res-card { padding: 1.0rem 0.4rem 1.0rem 0.4rem; }
    .exit-btn button { font-size: 1rem; padding: 0.65em 1.2em; }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ========== SnapForge 品牌横幅与开源信息 ==========
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

# ========== 主功能Tabs ==========
st.markdown('<div class="main-card">', unsafe_allow_html=True)
tab_titles = ["批量/单文件图片处理", "图片信息查看", "图片去重（开发中）", "AI识别（开发中）"]
tabs = st.tabs(tab_titles)

# 1️⃣ 批量/单文件图片处理
with tabs[0]:
    processor = ImageProcessor()
    def save_uploaded_files(files, temp_dir):
        file_paths = []
        for f in files:
            temp_path = os.path.join(temp_dir, f.name)
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

        if mode == "批量处理（多文件上传）":
            files = st.file_uploader(
                "上传图片文件",
                type=["jpg","jpeg","png","bmp","gif","tiff","webp"],
                accept_multiple_files=True,
                help="多选支持 Ctrl 或 Shift"
            )
            extension = st.selectbox("仅处理指定类型", [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"], index=0)
        else:
            one_file = st.file_uploader(
                "上传一个图片文件",
                type=["jpg","jpeg","png","bmp","gif","tiff","webp"],
                accept_multiple_files=False
            )
            files = [one_file] if one_file else []
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
            para6, para7 = st.columns([2,2])
            with para6:
                preserve_metadata = st.checkbox("保留元数据 (EXIF)", value=True)
            with para7:
                file_action = st.selectbox("原始文件处理", [
                    "保留原始文件", "删除原始文件", "移动到备份目录"
                ])
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
                        'original_file_action': {
                            "保留原始文件": "keep",
                            "删除原始文件": "delete",
                            "移动到备份目录": "move_to_backup"
                        }[file_action],
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
        else:
            result_area.info("请上传图片并设置参数后，点击【开始处理图片】", icon="ℹ️")
        st.markdown('</div>', unsafe_allow_html=True)

# 2️⃣ 图片信息查看
with tabs[1]:
    st.subheader("图片信息查看")
    uploaded = st.file_uploader("上传图片查看信息", type=["jpg","jpeg","png","bmp","gif","tiff","webp"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="图片预览")
        st.write("尺寸:", img.size)
        st.write("模式:", img.mode)
        st.write("格式:", img.format)
        exif_data = img.info.get("exif")
        if exif_data:
            st.write("EXIF信息存在，可以进一步解析")
        else:
            st.write("无EXIF信息")

# 3️⃣ 图片去重（开发中）
with tabs[2]:
    st.subheader("图片去重（开发中）")
    st.info("此功能即将上线，敬请期待！")

# 4️⃣ AI识别（开发中）
with tabs[3]:
    st.subheader("AI识别（开发中）")
    st.info("此功能即将上线，敬请期待！")

st.markdown('</div>', unsafe_allow_html=True)

# ==================
# 关闭页面功能按钮
# ==================
st.markdown("""
<div class="exit-btn">
    <button onclick="window.close();">❌ 关闭/退出网页</button>
</div>
<div class="exit-note">
    如未自动关闭，请手动关闭本标签页
</div>
""", unsafe_allow_html=True)

# ==================
# 定制化页脚
# ==================
st.markdown("""
<div class="footer">
    <span>© 2025 <b>SnapForge</b> | <a href="https://github.com/riceshowerX/SnapForge" target="_blank" style="color:#406aff;text-decoration:none;font-weight:500;">GitHub开源项目</a> | 设计&开发：<a href="https://github.com/riceshowerX" target="_blank" style="color:#406aff;text-decoration:none;font-weight:500;">riceshowerX</a>
    </span>
</div>
""", unsafe_allow_html=True)
