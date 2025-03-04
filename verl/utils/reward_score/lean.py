import re
import logging
import json
import time
import tempfile
import subprocess
from typing import Optional, Tuple
import random
import datetime

DEFAULT_LAKE_PATH = "/AI4M/users/qzh/Lean_env/elan/bin/lake"
DEFAULT_LEAN_WORKSPACE = "/AI4M/users/qzh/Lean_env/lean_test_v4130"
VERIFICATION_LOG_FILE = "verification_log.jsonl"  # New log file for JSONL output

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='verification_logs.txt'
)

def extract_solution(solution_str: str, method='strict') -> Optional[str]:
    """Extract the proof code from model output."""
    if method == 'strict':
        pattern = r"```lean\s*([\s\S]*?)```"
        match = re.search(pattern, solution_str)
        if match:
            code = match.group(1).strip()
            if ":= by" in code:
                return code.split(":= by")[-1]
            elif ":=by" in code:
                return code.split(":=by")[-1]
            else:
                with open('verification_logs.txt', 'a', encoding='utf-8') as f:
                    f.write(f"Not found\n")
        return None
    else:
        raise NotImplementedError

def log_verification_attempt(proof_code: str, formal_statement: str, result: dict, duration: float):
    """Log verification attempt to JSONL file."""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "proof_code": proof_code,
        "formal_statement": formal_statement,
        "result": result,
        "duration_seconds": duration
    }
    with open(VERIFICATION_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def verify_proof(code: str, formal_statement: str, 
                lake_path: str = DEFAULT_LAKE_PATH,
                lean_workspace: str = DEFAULT_LEAN_WORKSPACE,
                timeout: int = 300) -> bool:
    full_code = formal_statement.strip() + code
    command = {"cmd": full_code, "allTactics": False, "ast": False, 
              "tactics": False, "premises": False}
    message_str = json.dumps(command, ensure_ascii=False)
    
    process = None
    start_time = time.time()
    try:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as temp_file:
            temp_file.write(message_str + "\r\n\r\n")
            temp_file.seek(0)
            process = subprocess.Popen(
                [lake_path, "exe", "repl"],
                stdin=temp_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=lean_workspace
            )
            outputs, errors = process.communicate(timeout=timeout)
        result = json.loads(outputs)
        processed_result = {
            "sorries": result.get("sorries", []),
            "errors": [m for m in result.get("messages", []) if m["severity"] == "error"],
        }
        duration = time.time() - start_time
        log_verification_attempt(code, formal_statement, processed_result, duration)
        return not processed_result["errors"] and not processed_result["sorries"]
    except subprocess.TimeoutExpired:
        if process:
            process.kill()
        duration = time.time() - start_time
        log_verification_attempt(code, formal_statement, {"error": "timeout"}, duration)
        logging.error(f"Verification timed out after {timeout}s")
        return False
    except Exception as e:
        if process:
            process.kill()
        duration = time.time() - start_time
        log_verification_attempt(code, formal_statement, {"error": str(e)}, duration)
        logging.error(f"Verification failed: {str(e)}")
        return False
    finally:
        if process and process.poll() is None:
            process.kill()

def compute_score(solution_str: str, ground_truth: dict, 
                 method: str = 'strict',
                 format_score: float = 0.5,
                 score: float = 4.0) -> float:
    """Compute reward score for model output."""
    proof_code = extract_solution(solution_str, method)
    if proof_code is None:
        return -1.0
        
    total_score = format_score
    
    if verify_proof(proof_code, ground_truth['formal_statement']):
        total_score += score
        
    return total_score

def test_lean_reward():
    """Test the lean reward functionality."""
    # Test extract_solution
    test_input = """
Thus, we have proven that if \(\frac{d^2}{2} = 40\), then \(d^2 = 80\).

```lean4
theorem thm_26878 (d : ℝ) (h : d > 0) (h₀ : d ^ 2 / 2 = 40) : d ^ 2 = 80 := by
  have h₁ : d ^ 2 / 2 = 40 := h₀
  have h₂ : d ^ 2 = 80 := by
    rw [← mul_right_inj' (two_ne_zero' ℝ)] at h₁
    linarith
  exact h₂
```<｜end▁of▁sentence｜>
    """
    proof_code = extract_solution(test_input, 'strict')
    print(proof_code)
    assert proof_code is not None, "Failed to extract solution"
    
    invalid_input = "No final answer here"
    assert extract_solution(invalid_input, 'strict') is None, "Should return None for invalid input"
    
    test_statement = "import Mathlib\ntheorem test_add : 2 + 2 = 4 :="
    test_proof = "by ring"
    verification_result = verify_proof(
        test_proof,
        test_statement,
        DEFAULT_LAKE_PATH,
        DEFAULT_LEAN_WORKSPACE
    )
    assert verification_result, "Proof verification failed"
    
    ground_truth = {
        'formal_statement': test_statement
    }
    
    full_solution = f"""Some explanation
    Final Answer:
    {test_input}
    """
    score = compute_score(full_solution, ground_truth)
    assert score > 0, "Score should be positive for correct solution"
    
    bad_format = "Just some text without Final Answer"
    score = compute_score(bad_format, ground_truth)
    assert score == -1.0, "Score should be -1 for incorrect format"

if __name__ == "__main__":
    test_lean_reward()
    print("All tests passed!")