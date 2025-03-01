#!/usr/bin/env python3

import psutil
import subprocess
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("memory_monitor.log"),  # 日志保存到文件
        logging.StreamHandler()                     # 同时输出到终端
    ]
)

# 内存使用率阈值（百分比）
MEMORY_THRESHOLD = 60.0
# 检查间隔（秒）
CHECK_INTERVAL = 60  # 每分钟检查一次

def get_memory_usage():
    """获取当前系统内存使用率（百分比）和详细信息。"""
    memory = psutil.virtual_memory()
    return {
        "percent": memory.percent,
        "total": memory.total / (1024 ** 3),  # 转换为 GB
        "used": memory.used / (1024 ** 3),    # 转换为 GB
        "free": memory.free / (1024 ** 3)     # 转换为 GB
    }

def kill_repl_processes():
    """运行 pkill 命令终止所有 Lean REPL 进程。"""
    try:
        cmd = ['pkill', '-9', '-f', '.lake/packages/REPL/.lake/build/bin/repl']
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
        logging.info("Successfully killed all Lean REPL processes.")
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            # pkill 返回 1 表示没有匹配的进程
            logging.info("No Lean REPL processes found to kill.")
        else:
            logging.error(f"Failed to kill Lean REPL processes: {e.stderr}")
    except Exception as e:
        logging.error(f"Error while killing processes: {str(e)}")

def monitor_memory():
    """监控内存使用率，记录日志，并在超过阈值时杀死 Lean REPL 进程。"""
    logging.info(f"Starting memory monitor with threshold {MEMORY_THRESHOLD}%")
    while True:
        try:
            memory_info = get_memory_usage()
            percent = memory_info["percent"]
            total_gb = memory_info["total"]
            used_gb = memory_info["used"]
            free_gb = memory_info["free"]

            # 记录内存使用情况
            logging.info(
                f"Memory usage: {percent:.1f}% "
                f"(Total: {total_gb:.2f} GB, Used: {used_gb:.2f} GB, Free: {free_gb:.2f} GB)"
            )

            # 检查是否超过阈值
            if percent > MEMORY_THRESHOLD:
                logging.warning(
                    f"Memory usage ({percent:.1f}%) exceeds threshold ({MEMORY_THRESHOLD}%). "
                    "Killing Lean REPL processes..."
                )
                kill_repl_processes()
            else:
                logging.info("Memory usage is within safe limits.")

            # 休眠一段时间再检查
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logging.error(f"Error in memory monitoring: {str(e)}")
            time.sleep(CHECK_INTERVAL)  # 出错了也等待，避免无限循环过快

if __name__ == "__main__":
    monitor_memory()