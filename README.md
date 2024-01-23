## 简介
大型语言模型评估（LLMs evaluation）已成为评价和改进大模型的重要流程和手段，为了更好地支持大模型的评测，我们提出了llmuses框架，该框架主要包括以下几个部分：
- 预置了多个常用的测试基准数据集，包括：MMLU、C-Eval、GSM8K、ARC、HellaSwag、TruthfulQA、MATH、HumanEval等
- 常用评估指标（metrics）的实现
- 统一model接入，兼容多个系列模型的generate、chat接口
- 自动评估（evaluator）：
    - 客观题自动评估
    - 使用专家模型实现复杂任务的自动评估
- 评估报告生成
- 竞技场模式(Arena）
- 可视化工具

特点
- 轻量化，尽量减少不必要的抽象和配置
- 易于定制
  - 仅需实现一个类即可接入新的数据集
  - 模型可部署在本地，或[ModelScope](https://modelscope.cn)上
  - 评估报告可视化展现
- 丰富的评估指标
- model-based自动评估流程，支持多种评估模式
  - Single mode: 专家模型对单个模型打分
  - Pairwise-baseline mode: 与 baseline 模型对比
  - Pairwise (all) mode: 全部模型两两对比


## 环境准备
```shell
# 1. 代码下载
git clone git@github.com:modelscope/llmuses.git

# 2. 安装依赖
cd llmuses/
pip install -r requirements/requirements.txt
pip install -e .
```


## 快速开始

### 简单评估
```shell
# 在特定数据集上评估某个模型
python llmuses/run.py --model ZhipuAI/chatglm3-6b --datasets mmlu ceval --limit 10
```

### 带参数评估
```shell
python llmuses/run.py --model ZhipuAI/chatglm3-6b --model-args revision=v1.0.2,precision=torch.float16,device_map=auto --datasets mmlu ceval --mem-cache --limit 10

# 参数说明
# --model-args: 模型参数，以逗号分隔，key=value形式
# --datasets: 数据集名称，参考下文`数据集列表`章节
# --mem-cache: 是否使用内存缓存，若开启，则已经跑过的数据会自动缓存，并持久化到本地磁盘
# --limit: 每个subset最大评估数据量
```


### 竞技场模式（Arena）
竞技场模式允许多个候选模型通过两两对比(pairwise battle)的方式进行评估，并可以选择借助AI Enhanced Auto-Reviewer（AAR）自动评估流程或者人工评估的方式，最终得到评估报告，流程示例如下：
#### 1. 环境准备
```text
a. 数据准备，questions data格式参考：llmuses/registry/data/question.jsonl
b. 如果需要使用自动评估流程（AAR），则需要配置相关环境变量，我们以GPT-4 based auto-reviewer流程为例，需要配置以下环境变量：
> export OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

#### 2. 配置文件
```text
arena评估流程的配置文件参考： llmuses/registry/config/cfg_arena.yaml
字段说明：
    questions_file: question data的路径
    answers_gen: 候选模型预测结果生成，支持多个模型，可通过enable参数控制是否开启该模型
    reviews_gen: 评估结果生成，目前默认使用GPT-4作为Auto-reviewer，可通过enable参数控制是否开启该步骤
    elo_rating: ELO rating 算法，可通过enable参数控制是否开启该步骤，注意该步骤依赖review_file必须存在
```

#### 3. 执行脚本
```shell
#Usage:
cd llmuses

# dry-run模式 (模型answer正常生成，但专家模型不会被触发，评估结果会随机生成)
python llmuses/run_arena.py -c registry/config/cfg_arena.yaml --dry-run

# 执行评估流程
python llmuses/run_arena.py --c registry/config/cfg_arena.yaml
```

#### 4. 结果可视化

```shell
# Usage:
streamlit run viz.py -- --review-file llmuses/registry/data/qa_browser/battle.jsonl --category-file llmuses/registry/data/qa_browser/category_mapping.yaml
```


### 单模型打分模式（Single mode）

这个模式下，我们只对单个模型输出做打分，不做两两对比。
#### 1. 配置文件
```text
评估流程的配置文件参考： llmuses/registry/config/cfg_single.yaml
字段说明：
    questions_file: question data的路径
    answers_gen: 候选模型预测结果生成，支持多个模型，可通过enable参数控制是否开启该模型
    reviews_gen: 评估结果生成，目前默认使用GPT-4作为Auto-reviewer，可通过enable参数控制是否开启该步骤
    rating_gen: rating 算法，可通过enable参数控制是否开启该步骤，注意该步骤依赖review_file必须存在
```
#### 2. 执行脚本
```shell
#Example:
python llmuses/run_arena.py --c registry/config/cfg_single.yaml
```

### Baseline模型对比模式（Pairwise-baseline mode）

这个模式下，我们选定 baseline 模型，其他模型与 baseline 模型做对比评分。这个模式可以方便的把新模型加入到 Leaderboard 中（只需要对新模型跟 baseline 模型跑一遍打分即可）
#### 1. 配置文件
```text
评估流程的配置文件参考： llmuses/registry/config/cfg_pairwise_baseline.yaml
字段说明：
    questions_file: question data的路径 
    answers_gen: 候选模型预测结果生成，支持多个模型，可通过enable参数控制是否开启该模型
    reviews_gen: 评估结果生成，目前默认使用GPT-4作为Auto-reviewer，可通过enable参数控制是否开启该步骤
    rating_gen: rating 算法，可通过enable参数控制是否开启该步骤，注意该步骤依赖review_file必须存在
```
#### 2. 执行脚本
```shell
# Example:
python llmuses/run_arena.py --c llmuses/registry/config/cfg_pairwise_baseline.yaml
```


## 数据集列表

| dataset name       | link                                                                                   | status | note |
|--------------------|----------------------------------------------------------------------------------------|--------|------|
| `mmlu`             | [mmlu](https://modelscope.cn/datasets/modelscope/mmlu/summary)                         | active |    |
| `ceval`            | [ceval](https://modelscope.cn/datasets/modelscope/ceval-exam/summary)                  | active |    |
| `gsm8k`            | [gsm8k](https://modelscope.cn/datasets/modelscope/gsm8k/summary)                       | active |    |
| `arc`              | [arc](https://modelscope.cn/datasets/modelscope/ai2_arc/summary)                       | active |    |
| `hellaswag`        | [hellaswag](https://modelscope.cn/datasets/modelscope/hellaswag/summary)               | active |    |
| `truthful_qa`      | [truthful_qa](https://modelscope.cn/datasets/modelscope/truthful_qa/summary)           | active |    |
| `competition_math` | [competition_math](https://modelscope.cn/datasets/modelscope/competition_math/summary) | active |    |
| `humaneval`        | [humaneval](https://modelscope.cn/datasets/modelscope/humaneval/summary)               | active |    |
| `bbh`                | [bbh](https://modelscope.cn/datasets/modelscope/bbh/summary)                           | active |    |


## Leaderboard 榜单
ModelScope LLM Leaderboard大模型评测榜单旨在提供一个客观、全面的评估标准和平台，帮助研究人员和开发者了解和比较ModelScope上的模型在各种任务上的性能表现。

[Leaderboard](https://modelscope.cn/leaderboard/58/ranking?type=free)



## 实验和报告
参考： [Experiments](./resources/experiments.md)

## TO-DO List
- [ ] Agents evaluation
- [ ] vLLM
- [ ] Distributed evaluating
- [ ] Multi-modal evaluation
- [ ] Benchmarks
  - [ ] GAIA
  - [ ] GPQA
  - [ ] MBPP
- [ ] Auto-reviewer
  - [ ] Qwen-max
