<div align="center">
  <img src="https://github.com/riceshowerX/picx-images-hosting/raw/master/网站/android-chrome-192x192-1.6wqw9el8i6.webp" alt="SnapForge Logo" width="80" height="80">
  <h1 style="font-size: 3rem; font-weight: bold; color: #222; margin: 10px 0 0 0;">SnapForge</h1>
  <p style="font-size: 1.2rem; color: #616161; max-width: 600px; margin: 12px auto;">
    <b>SnapForge</b> 是一款基于 <b>Python</b> 打造的专业级图像批量处理平台，支持网页版（Streamlit UI），专为高效图片批量处理、重命名、格式转换、去重、去背景、AI识别等多场景设计，让图片管理更智能、更便捷。
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

![2025-07-03_154827](https://github.com/user-attachments/assets/a475207e-2650-4212-b7aa-3e3d32d6974b)


---

## ✨ 项目亮点

- **🖼️ 批量/单文件格式转换**  
  支持 JPEG、PNG、BMP、GIF、TIFF、WebP 等多种格式互转，适配多场景。

- **🔄 批量/单文件重命名**  
  灵活自定义前缀与编号，自动防止命名冲突，处理海量图片也游刃有余。

- **🗜️ 批量/单文件高效压缩**  
  多种格式质量调节，智能保持画质，显著减小体积，优化存储与加载。

- **📏 尺寸调整与多种缩放模式**  
  提供等比缩放、填充、裁剪等多样模式，满足不同分辨率需求。

- **🧹 智能去重与批量清理**  
  支持高效图片查重、相似图检测和批量清理。

- **🎯 去背景功能**  
  一键移除图片背景，基于AI模型（rembg+U2Net），适配常见照片、商品图等。

- **🤖 AI识别与OCR**  
  支持接入百度、DeepSeek等云端AI服务，图片内容自动识别与标签化，集成OCR批量文字识别。

- **🌈 现代化美观多语言界面**  
  提供 Streamlit 网页版，支持中/英文界面切换，布局美观，操作直观。

- **📝 详细日志与进度反馈**  
  批量处理详细日志与异常提示，处理情况一目了然。

- **🌐 跨平台支持**  
  Windows / macOS / Linux 全平台兼容。

---

## 🚀 快速开始

> **目前仅支持网页版（Streamlit UI），不再维护桌面版。**

1. **克隆项目代码**
   ```bash
   git clone https://github.com/riceshowerX/SnapForge.git
   ```

2. **安装依赖**
   ```bash
   cd SnapForge
   pip install -r requirements.txt
   ```

3. **运行网页版**
   ```bash
   streamlit run app.py
   ```
   浏览器访问 `http://localhost:8501`  
   首次运行去背景等功能时会自动下载模型文件（如 u2net.onnx，约176MB）。

---

## 🧠 关于去背景模型（U2Net）

SnapForge 的「去背景」功能基于 [rembg](https://github.com/danielgatis/rembg) 库和 [U2Net](https://github.com/xuebinqin/U-2-Net) 模型。首次使用时，程序会自动从官方地址下载模型文件：

- **模型下载地址（官方）**：[https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx](https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx)
- **模型大小**：约 176MB
- **模型版权**：U2Net 模型归原作者所有，仅用于学术/研究/非商业用途。  
  SnapForge 仅作调用，不分发、不二次上传模型文件。

如国内网络较慢，可通过第三方加速（如 [ghproxy](https://ghproxy.com/)）或手动下载后放入 `C:\Users\你的用户名\.u2net\u2net.onnx`（Windows）或 `~/.u2net/u2net.onnx`（Linux/Mac）。

---

## 🛣️ 未来开发计划

- [x] **多语言支持**：支持中/英文界面切换
- [x] **扩展图像处理功能**：批量裁剪、旋转、水印添加等
- [x] **智能查重与清理**：自动检测并处理重复图片
- [x] **去背景功能**：AI一键去背景，支持批量
- [x] **AI识别/OCR**：图片内容标签化、批量文字识别
- [ ] **自定义输出目录结构**：支持输出文件夹与命名模板自定义
- [ ] **增强预览与元数据展示**：支持缩略图和 EXIF 信息查看
- [ ] **自动化批处理脚本**：支持命令行参数和自动化工作流
- [ ] **一键多平台打包分发**：Windows/Mac/Linux 可执行文件
- [ ] **性能与体验优化**：提升处理效率和界面交互体验
- [ ] **社区共建**：持续聆听用户建议，开放更多贡献渠道

---

## 🤝 贡献指南

欢迎提交新功能、优化代码、完善文档，或反馈问题与建议！  
请通过 [Issue](https://github.com/riceshowerX/SnapForge/issues) 或 [Pull Request](https://github.com/riceshowerX/SnapForge/pulls) 与我们沟通协作。

> 本项目为个人业余维护，开发进度有限，感谢您的理解和支持！

---

## 📄 许可证

本项目采用 [MIT License](https://github.com/riceshowerX/SnapForge/blob/main/LICENSE) 开源，欢迎自由使用与再开发。

---

## ⚠️ 免责声明

本项目按“原样”提供，不附带任何明示或暗示的保证。  
使用本项目时，风险由用户自行承担，开发者和贡献者不承担任何直接或间接损失责任。详见 LICENSE 文件。
