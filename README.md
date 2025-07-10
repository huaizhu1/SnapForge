
<div align="center">
  <img src="https://github.com/riceshowerX/picx-images-hosting/raw/master/网站/android-chrome-192x192-1.6wqw9el8i6.webp" alt="SnapForge Logo" width="80" height="80">
  <h1>SnapForge</h1>
  <p>
    <b>SnapForge</b> 是一款基于 <b>Python</b> 的专业级图像批量处理平台，提供现代化网页版（Streamlit UI），专为高效图片管理、批量处理、重命名、格式转换、去重、去背景、AI识别等多场景设计，让图片管理更智能、更便捷。
  </p>
  <p>
    <a href="https://github.com/riceshowerX/SnapForge/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
    </a>
    <a href="https://github.com/riceshowerX/SnapForge/releases/latest" target="_blank">
      <img src="https://img.shields.io/github/v/release/riceshowerX/SnapForge" alt="Latest Release">
    </a>
    <a href="https://github.com/riceshowerX/SnapForge/issues" target="_blank">
      <img src="https://img.shields.io/github/issues/riceshowerX/SnapForge" alt="Open Issues">
    </a>
    <a href="https://github.com/riceshowerX/SnapForge/pulls" target="_blank">
      <img src="https://img.shields.io/github/issues-pr/riceshowerX/SnapForge" alt="Pull Requests">
    </a>
  </p>
</div>

---

## 🖼️ 软件界面预览

![界面预览](https://github.com/user-attachments/assets/a475207e-2650-4212-b7aa-3e3d32d6974b)

---

## ✨ 功能亮点

- **🖼️ 格式转换**  
  支持 JPEG、PNG、BMP、GIF、TIFF、WebP 等多种格式互转，适配多种应用场景。

- **🔄 批量/单文件重命名**  
  灵活自定义前缀与编号，自动防止命名冲突，应对大批量图片处理。

- **🗜️ 图片压缩**  
  多种格式质量调节，智能保持画质，压缩高效，节省存储空间。

- **📏 尺寸调整与多种缩放模式**  
  支持等比缩放、填充、裁剪等多种模式，满足不同分辨率需求。

- **🧹 智能去重与批量清理**  
  高效图片查重、相似图检测，支持批量清理。

- **🎯 一键去背景**  
  基于 AI（rembg+U2Net），适配常见照片、商品图等，精准抠图。

- **🤖 AI识别与OCR**  
  接入百度、DeepSeek 等云端 AI 服务，图片内容自动标签化，批量文字识别。

- **🌈 现代化多语言界面**  
  Streamlit 网页版，支持中/英文切换，布局美观，操作直观。

- **📝 详细日志与进度反馈**  
  批量处理详细日志、异常提示，处理过程一目了然。

- **🌐 跨平台支持**  
  完全兼容 Windows / macOS / Linux。

---

## 🚀 快速开始

> **目前仅提供网页版（Streamlit UI），桌面版已不再维护。**

1. **克隆项目**
   ```bash
   git clone https://github.com/riceshowerX/SnapForge.git
   ```

2. **安装依赖**
   ```bash
   cd SnapForge
   pip install -r requirements.txt
   ```

3. **运行网页端**
   ```bash
   streamlit run app.py
   ```
   浏览器访问 `http://localhost:8501`  
   首次运行去背景等功能时会自动下载模型文件（如 u2net.onnx，约176MB）。

---

## 🧠 关于去背景模型（U2Net）

SnapForge 的去背景功能基于 [rembg](https://github.com/danielgatis/rembg) 和 [U2Net](https://github.com/xuebinqin/U-2-Net) 模型。首次使用时将自动下载模型文件：

- **官方模型下载**：[u2net.onnx](https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx)（约176MB）
- **模型版权**：U2Net 归原作者所有，仅供学术/研究/非商业用途。SnapForge 仅作调用，不分发、不二次上传模型文件。

如国内网络较慢，可用 [ghproxy](https://ghproxy.com/) 加速，或手动下载至：
- Windows: `C:\Users\你的用户名\.u2net\u2net.onnx`
- Linux/Mac: `~/.u2net/u2net.onnx`

---

## 🛣️ 未来开发计划

- [x] 多语言支持（中/英文界面切换）
- [x] 扩展图像处理功能：批量裁剪、旋转、水印添加
- [x] 智能查重与清理
- [x] AI一键去背景（支持批量）
- [x] AI识别/OCR
- [ ] 自定义输出目录结构/命名模板
- [ ] 缩略图和 EXIF 信息展示
- [ ] 自动化批处理脚本（命令行/工作流）
- [ ] 一键多平台打包发布
- [ ] 性能与体验优化
- [ ] 社区共建与贡献渠道开放

---

## 🤝 贡献指南

欢迎提交新功能、优化代码、完善文档，或反馈问题与建议！  
请通过 [Issue](https://github.com/riceshowerX/SnapForge/issues) 或 [Pull Request](https://github.com/riceshowerX/SnapForge/pulls) 与我们交流。

> 项目为个人业余维护，开发进度有限，感谢理解与支持！

---

## 📄 许可证

- 主体代码采用 [MIT License](https://github.com/riceshowerX/SnapForge/blob/main/LICENSE) 开源，欢迎自由使用与再开发。
- 依赖的 Streamlit 库采用 [Apache License 2.0](https://github.com/riceshowerX/SnapForge/blob/main/LICENSE%E2%80%91STREAMLIT)（已在 LICENSE‑STREAMLIT 中保留完整版权及许可证）。

---

## ⚠️ 免责声明

本项目按“原样”提供，不附带任何明示或暗示的保证。  
使用风险由用户自担，开发者和贡献者不对任何直接或间接损失负责。详见 LICENSE 文件。
````
