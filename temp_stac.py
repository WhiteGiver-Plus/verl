import json
from collections import defaultdict
from typing import Tuple

VERIFICATION_LOG_FILE = "verification_log.jsonl"

def analyze_verification_log_with_8_repeats(n: int = -1) -> Tuple[float, float, int, int, int]:
    """
    分析最后 n 个条目中 formal_statement 重复 8 次的语句的准确率和成功证明比例。
    
    Args:
        n: 要分析的最后条目数 (-1 表示全部)
        
    Returns:
        Tuple of (success_rate, proportion_with_successful_proof, successful_entries, total_entries_with_8_repeats, unique_formal_with_8_repeats)
    """
    # 用于记录每个 formal_statement 出现的次数和成功情况
    statement_counts = defaultdict(int)
    statement_success = defaultdict(int)  # 记录成功的次数
    
    # 读取所有条目
    all_entries = []
    try:
        with open(VERIFICATION_LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                all_entries.append(json.loads(line.strip()))
    except FileNotFoundError:
        print(f"日志文件 {VERIFICATION_LOG_FILE} 未找到")
        return 0.0, 0.0, 0, 0, 0
    
    if not all_entries:
        print("日志文件为空")
        return 0.0, 0.0, 0, 0, 0
    
    # 确定要分析的条目
    if n == -1 or n >= len(all_entries):
        entries_to_analyze = all_entries
    else:
        entries_to_analyze = all_entries[-n:]
    
    # 统计每个 formal_statement 的出现次数和成功次数
    for entry in entries_to_analyze:
        result = entry.get('result', {})
        formal_statement = entry.get('formal_statement', '')
        
        if formal_statement:  # 确保 formal_statement 不为空
            statement_counts[formal_statement] += 1
            # 判断是否成功：无 sorries、无 errors、无 error 字段
            is_successful = (
                'sorries' in result and not result['sorries'] and
                'errors' in result and not result['errors'] and
                'error' not in result
            )
            if is_successful:
                statement_success[formal_statement] += 1
    
    # 筛选出重复 8 次的 formal_statement
    total_entries_with_8_repeats = 0
    successful_entries = 0
    unique_formal_with_8_repeats = 0
    successful_statements = 0  # 至少有一次成功的 formal_statement 计数
    
    for formal_statement, count in statement_counts.items():
        if count == 8:  # 只统计重复 8 次的 formal_statement
            unique_formal_with_8_repeats += 1
            total_entries_with_8_repeats += count  # 总计 8 次
            successful_entries += statement_success[formal_statement]
            if statement_success[formal_statement] > 0:  # 至少有一次成功
                successful_statements += 1
    
    # 计算准确率
    success_rate = successful_entries / total_entries_with_8_repeats if total_entries_with_8_repeats > 0 else 0.0
    
    # 计算至少有一次成功证明的比例
    proportion_with_successful_proof = successful_statements / unique_formal_with_8_repeats if unique_formal_with_8_repeats > 0 else 0.0
    
    return success_rate, proportion_with_successful_proof, successful_entries, total_entries_with_8_repeats, unique_formal_with_8_repeats

def print_analysis_with_8_repeats(n: int = -1):
    """格式化输出 formal_statement 重复 8 次的分析结果。"""
    success_rate, proportion_successful, successful, total, unique_count = analyze_verification_log_with_8_repeats(n)
    if n == -1:
        print("分析所有 formal_statement 重复 8 次的条目：")
    else:
        print(f"分析最后 {n} 个条目中 formal_statement 重复 8 次的条目：")
    
    print(f"准确率: {success_rate:.2%} ({successful}/{total} 成功)")
    print(f"至少有一次成功证明的 formal_statement 比例: {proportion_successful:.2%}")
    print(f"总计符合条件的条目数: {total}")
    print(f"重复 8 次的唯一 formal_statement 数量: {unique_count}")

if __name__ == "__main__":
    print("分析所有符合条件的条目：")
    print_analysis_with_8_repeats(-1)
    print("\n分析最后 5 个条目中符合条件的条目：")
    print_analysis_with_8_repeats(800)