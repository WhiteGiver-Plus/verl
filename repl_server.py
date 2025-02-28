# server.py
import os
import json
import time
import asyncio
import tempfile
import subprocess
from multiprocessing import Pool, Manager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging

DEFAULT_LAKE_PATH = "/AI4M/users/qzh/Lean_env/elan/bin/lake"
DEFAULT_LEAN_WORKSPACE = "/AI4M/users/qzh/Lean_env/lean_test_v4130"

# 请求模型
class VerifyRequest(BaseModel):
    code: str
    formal_statement: str
    lake_path: str = DEFAULT_LAKE_PATH
    lean_workspace: str = DEFAULT_LEAN_WORKSPACE
    timeout: int = 1200

# 全局进程池和队列
_pool = None
_task_queue = None
_result_dict = None

def init_pool(max_workers: int = 64):
    """初始化进程池"""
    global _pool, _task_queue, _result_dict
    cpu_count = os.cpu_count()  # 检测 CPU 核数（128）
    max_workers = min(max_workers, cpu_count)
    manager = Manager()
    _pool = Pool(processes=max_workers)
    _task_queue = manager.Queue()
    _result_dict = manager.dict()
    for _ in range(max_workers):
        _pool.apply_async(worker, (_task_queue, _result_dict))
    logging.info(f"Initialized pool with {max_workers} workers")

def worker(task_queue, result_dict):
    """后台工作进程"""
    while True:
        try:
            task_id, code, formal_statement, lake_path, lean_workspace, timeout = task_queue.get()
            result = verify_proof_single(code, formal_statement, lake_path, lean_workspace, timeout)
            result_dict[task_id] = result
        except Exception as e:
            logging.error(f"Worker failed: {str(e)}")
            result_dict[task_id] = False
        finally:
            task_queue.task_done()

def verify_proof_single(code: str, formal_statement: str, 
                       lake_path: str, lean_workspace: str, 
                       timeout: int) -> bool:
    """单次验证逻辑"""
    full_code = formal_statement.strip() + code
    command = {"cmd": full_code, "allTactics": False, "ast": False, 
              "tactics": False, "premises": False}
    message_str = json.dumps(command, ensure_ascii=False)
    
    try:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as temp_file:
            temp_file.write(message_str + "\r\n\r\n")
            temp_file.seek(0)
            outputs = subprocess.run(
                [lake_path, "exe", "repl"],
                stdin=temp_file,
                capture_output=True,
                text=True,
                cwd=lean_workspace,
                timeout=timeout,
            )
        result = json.loads(outputs.stdout)
        result = {
            "sorries": result.get("sorries", []),
            "errors": [m for m in result.get("messages", []) 
                      if m["severity"] == "error"],
        }
        return not result["errors"] and not result["sorries"]
    except Exception as e:
        logging.error(f"Verification failed: {str(e)}")
        return False

# FastAPI 应用
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """服务启动时初始化进程池"""
    init_pool(max_workers=128)  # 默认使用 128 核

@app.post("/verify")
async def verify(request: VerifyRequest):
    """API 端点：验证 proof"""
    global _task_queue, _result_dict
    
    task_id = f"{time.time()}_{id(request.code)}"
    _task_queue.put((
        task_id, 
        request.code, 
        request.formal_statement, 
        request.lake_path, 
        request.lean_workspace, 
        request.timeout
    ))
    
    # 等待结果
    while task_id not in _result_dict:
        await asyncio.sleep(0.01)
    
    result = _result_dict[task_id]
    del _result_dict[task_id]
    return {"task_id": task_id, "result": result}

if __name__ == "__main__":
    logging.basicConfig(filename="server_logs.txt", level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)