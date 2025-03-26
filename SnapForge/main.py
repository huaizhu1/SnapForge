import sys
import logging
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox

# 保留原有导入和变量
from ui import BatchRenameApp

def configure_logging() -> None:
    """配置应用日志记录"""
    logging.basicConfig(
        filename='app.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    logging.info("日志系统初始化完成")

def handle_exception(exc_type, exc_value, exc_traceback) -> None:
    """全局异常处理"""
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error(f"未捕获的异常：{error_msg}")
    
    # 显示用户友好的错误提示
    QMessageBox.critical(
        None,
        "应用程序错误",
        "发生严重错误，程序即将退出。详细信息已记录到日志文件。"
    )
    sys.exit(1)

def main() -> None:
    # 设置全局异常处理
    sys.excepthook = handle_exception

    # 初始化日志
    configure_logging()
    logging.info("应用程序启动")

    # 创建Qt应用
    app = QApplication(sys.argv)
    
    try:
        # 主窗口初始化
        window = BatchRenameApp()
        window.show()
        
        # 正常退出处理
        exit_code = app.exec()
        logging.info("应用程序正常退出")
        sys.exit(exit_code)
        
    except Exception as e:
        # 捕获未处理的异常
        handle_exception(type(e), e, e.__traceback__)

if __name__ == "__main__":
    main()