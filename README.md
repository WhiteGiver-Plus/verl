1. nohup安装

```
conda create -n verl python==3.9
conda activate verl
pip3 install torch==2.4.0 
pip3 install flash-attn --no-build-isolation
pip3 install -e .

```

2. 使用
   数据集制备: data/data_process.ipynb (由于各个数据集特征不一样,需要手动调整参数,切记data_source中必须包含lean,否则无法选择lean.py作为reward)
   运行: bash scripts/train_reinforce_plus_4gpu_7Binstruct.sh
   防止内存爆炸: nohup python kill_all.py
3. 重要文件:
   verl/trainer/main_ppo.py 入口文件

   verl/utils/reward_score/lean.py reward_func位置
   
   verl/workers/reward_manager/prime.py reward_func并行管理器

   verl/trainer/ppo/ray_trainer.py 这里yverl/trainer/ppo/ray_trainer.p有wandb的log