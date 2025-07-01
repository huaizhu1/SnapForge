import sys
import logging
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox

# 配置应用日志记录
def configure_logging() -> None:
    """配置应用日志记录"""
    logging.basicConfig(
        filename='app.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    logging.info("日志系统初始化完成")

# 全局异常处理
def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """处理全局异常"""
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error(f"未捕获的异常：{error_msg}")
    
    # 检查QApplication实例是否存在
    app = QApplication.instance()
    if app is not None:
        # 显示用户友好的错误提示
        QMessageBox.critical(
            None,
            "应用程序错误",
            "发生严重错误，程序即将退出。详细信息已记录到日志文件。"
        )
    else:
        # 如果没有QApplication实例，输出到标准错误
        sys.stderr.write("发生严重错误，程序即将退出。详细信息已记录到日志文件。\n")
    
    sys.exit(1)

def main() -> None:
    # 设置全局异常处理
    sys.excepthook = handle_exception

    # 初始化日志
    configure_logging()
    logging.info("应用程序启动")

    try:
        # 创建Qt应用
        app = QApplication(sys.argv)
        
        # 动态导入UI模块（避免导入错误被全局钩子处理）
        from ui import BatchRenameApp
        
        # 主窗口初始化
        window = BatchRenameApp()
        window.show()
        
        # 正常退出处理
        exit_code = app.exec()
        logging.info("应用程序正常退出")
        sys.exit(exit_code)
        
    except Exception as e:
        # 捕获初始化阶段的异常
        handle_exception(type(e), e, e.__traceback__)

if __name__ == "__main__":
    main()
