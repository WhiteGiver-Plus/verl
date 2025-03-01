def split_and_save_dataset(df: pd.DataFrame, output_dir: str, test_size: int = 16):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 随机打乱数据
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # 拆分为测试集和训练集
    test_df = df_shuffled.iloc[:test_size]
    train_df = df_shuffled.iloc[test_size:]
    
    # 保存为 parquet 文件
    test_path = os.path.join(output_dir, "test.parquet")
    train_path = os.path.join(output_dir, "train.parquet")
    
    test_df.to_parquet(test_path, index=False)
    train_df.to_parquet(train_path, index=False)
    
    print(f"Test set saved to: {test_path} ({len(test_df)} rows)")
    print(f"Train set saved to: {train_path} ({len(train_df)} rows)")

# 示例用法
dataset_name = "your_dataset_name_here"  # 替换为实际的 HuggingFace 数据集名称
data_source = "user_specified_source"    # 由用户指定
output_dir = "/path/to/your/output/folder"  # 替换为指定的输出路径

# 处理数据集
df = process_dataset(dataset_name, data_source, key="proof")

# 拆分并保存
split_and_save_dataset(df, output_dir, test_size=16)