# 技能提交自动评审（结构证据版）

- submission: `C:\.cogseed\userWorkSpace\我的挑战有哪些\C2G`
- rubric: `C4A` v1.0.0
- evaluator: c4a-evaluator/1.0.0
- evidence_hash: `64e7c7bf55519e1dedd6bac3361364c288f622f3310be4d99fcb6f687d2901c7`

## 总分：45 / 100

| 维度 | 得分 | 上限 | 命中探针 |
| --- | --- | --- | --- |
| 评审器质量 | 4 | 25 | 1/5 |
| 技术实现 | 16 | 20 | 4/5 |
| 产物完整性 | 5 | 15 | 3/3 |
| AI 使用质量 | 10 | 20 | 2/4 |
| 复盘质量 | 10 | 20 | 2/4 |

## 红线

- **核心交付物缺失或空壳**（artifactCompleteness 封顶 5）

## 封顶生效

- artifactCompleteness: 15 -> 5 (missing_artifacts)

## 必交物

| 模式 | 命中 | 文件数 | 空壳 |
| --- | --- | --- | --- |
| `*方案设计*` | yes | 1 | - |
| `*skill-evaluator*` | NO | 0 | - |
| `*评审报告*` | NO | 0 | - |
| `*AI日志*` | yes | 1 | - |

## 维度明细

### 评审器质量  4/25

- [MISS] `eval.rubric_external` +4 评分标准外置为可替换 JSON
- [MISS] `eval.golden_set` +5 存在带标注的 Golden Set 测试用例（≥3）
- [MISS] `eval.self_test_report` +8 自测报告给出量化误判率
- [MISS] `eval.structured_output` +4 输出结构化机读结果
- [PASS] `eval.determinism` +4 说明并验证同一输入结果一致
  - `AI日志.md:53` | `void_rule.py` | 无效运行判定脚本：按同参数量、同时长同伴的 tok/s 中位数与组内步数双判据标记 INVALID，可复算、可审计（`TOTAL=24 VALID=22 INVALID=2`） |
  - `消融结果.md:91` 最终输出：`TOTAL=24 VALID=22 INVALID=2`，被废的恰好是 `b2_base_s1`（tok/s 236 < 同伴中位 2739 的 50%，11 步 < 128 步的 50%）与 `b2_base_s2`（tok/s 1160，51 步），与人工判断一致，但现在是可复算的。

未得分（无证据或未命中）：
- probe `eval.rubric_external` (-4) 评分标准外置为可替换 JSON
- probe `eval.golden_set` (-5) 存在带标注的 Golden Set 测试用例（≥3）
- probe `eval.self_test_report` (-8) 自测报告给出量化误判率
- probe `eval.structured_output` (-4) 输出结构化机读结果

### 技术实现  16/20

- [MISS] `tech.layered_modules` +4 分层模块化实现
- [PASS] `tech.no_todo` +3 无 TODO/FIXME 残留
- [PASS] `tech.error_handling` +4 含错误处理
  - `void_rule.py:35` try:
  - `void_rule.py:38` except Exception:
- [PASS] `tech.version_manifest` +5 有版本号或变更记录
  - `AI日志.md:39` 5. **BPB 计算一度算错**。早期版本用 token 数做分母，而 BPB 的定义是 bits per **byte**，分母必须是评测字节数。修正为 `bpt = eval_bytes / eval_tokens` 后再乘交叉熵，probe 的 BPB 从错误值降到 2.82472 并在此后所有 run 中保持
- [PASS] `tech.cli_entry` +4 可执行入口
  - `2023108610260_C2G_train_gpt.py:22` import argparse
  - `2023108610260_C2G_train_gpt.py:324` def main():
  - `2023108610260_C2G_train_gpt.py:325` ap = argparse.ArgumentParser()

未得分（无证据或未命中）：
- probe `tech.layered_modules` (-4) 分层模块化实现

### 产物完整性  5/15

- [PASS] `art.deliverables_all` +6 必交物全命中（由 Layer 2 复核，见必交物表）
  - `README.md:1` # C2G 参数高尔夫：极限约束下的语言模型训练
  - `README.md:1` # C2G 参数高尔夫：极限约束下的语言模型训练
  - `README.md:1` # C2G 参数高尔夫：极限约束下的语言模型训练
- [PASS] `art.readme_usage` +5 README 含安装与用法
  - `README.md:45` python prep_data.py --out ./c2g_data
  - `README.md:46` python train_gpt.py --data-dir ./c2g_data --out ./runs/v_best \
- [PASS] `art.entrypoint` +4 存在可运行入口
  - `2023108610260_C2G_train_gpt.py:324` def main():
  - `2023108610260_C2G_train_gpt.py:456` if __name__ == "__main__":
  - `prep_data.py:64` def main():

### AI 使用质量  10/20

- [PASS] `ai.log_scale` +6 AI日志存在且成规模（≥1500 字节）
  - `AI日志.md:1` size=7443 bytes
- [MISS] `ai.iteration_rounds` +5 记录 ≥3 轮迭代
- [MISS] `ai.prompt_records` +5 含 Prompt / 指令记录
- [PASS] `ai.failure_turns` +4 记录失败与转向
  - `AI日志.md:11` 在"模型 + 代码 + tokenizer ≤ 16,000,000 字节、单次训练 ≤ 10 分钟、无网络"的硬约束下，做一轮可解释的语言模型训练调参：找出在固定时间预算内真正能降 BPB 的旋钮，用同机对照实验量化每个旋钮的边际收益，并把结论与失败点如实记录下来，而不是只报一个好看的数。
  - `AI日志.md:70` | 00:45:27 – 00:49:19 | 补跑干净基线种子 ×2（113s / 114s）；组合验证首次失败（6s，参数错） |

未得分（无证据或未命中）：
- probe `ai.iteration_rounds` (-5) 记录 ≥3 轮迭代
- probe `ai.prompt_records` (-5) 含 Prompt / 指令记录

### 复盘质量  10/20

- [PASS] `ref.aar_present` +4 存在 AAR / 复盘文档
  - `AAR.md:1` size=5921 bytes
- [MISS] `ref.concrete_blockers` +6 有具体卡点描述
  - `AAR.md:31` 2. **自写 CLI 的参数语义没在跑前核对。** `--save-quant` 需要路径，我当成布尔开关传，浪费了一轮 6 秒的失败 run。虽然代价小，但这类错误在有时间预算的任务里是纯损耗。**改进：跑之前先 `--help` 或读 argparse 定义。**
- [PASS] `ref.actionable_plan` +6 有可执行的改进方案
  - `AAR.md:15` | 策略判断 | Muon 优化器是主要改进方向 | **判断错了**。实测 −0.0059 BPB，近乎中性；真正有效的是学习率（−0.11）和解除权重共享（−0.08） |
  - `AAR.md:31` 2. **自写 CLI 的参数语义没在跑前核对。** `--save-quant` 需要路径，我当成布尔开关传，浪费了一轮 6 秒的失败 run。虽然代价小，但这类错误在有时间预算的任务里是纯损耗。**改进：跑之前先 `--help` 或读 argparse 定义。**
  - `AAR.md:33` 3. **批量后台跑实验时没有隔离机器负载。** batch B 前两轮被压到 1/10 吞吐，说明当时机器有别的负载（我自己的轮询脚本、系统的后续处理）。正确做法是串行跑且跑的时候不做别的重活；后两轮我改成前台串行，吞吐立刻稳定在 2700 左右。**改进：训练脚本里加入吞吐异常自检——若 tok/s 低于同配置历史
- [MISS] `ref.failure_kept` +4 记录被推翻的初判或失败用例

未得分（无证据或未命中）：
- probe `ref.concrete_blockers` (-6) 有具体卡点描述
- probe `ref.failure_kept` (-4) 记录被推翻的初判或失败用例

## 复核建议

- 必交物缺失：*skill-evaluator*、*评审报告* —— 请确认是否换名或未提交。
- 红线「核心交付物缺失或空壳」已触发（artifactCompleteness 封顶 5），请复核证据后决定是否放行。
- [评审器质量] 未得分探针 `eval.self_test_report`（-8）：自测报告给出量化误判率 —— 请人工判断是漏交还是本就不适用。
- [复盘质量] 未得分探针 `ref.concrete_blockers`（-6）：有具体卡点描述 —— 请人工判断是漏交还是本就不适用。
- [AI 使用质量] 未得分探针 `ai.iteration_rounds`（-5）：记录 ≥3 轮迭代 —— 请人工判断是漏交还是本就不适用。
- [AI 使用质量] 未得分探针 `ai.prompt_records`（-5）：含 Prompt / 指令记录 —— 请人工判断是漏交还是本就不适用。
- [评审器质量] 未得分探针 `eval.golden_set`（-5）：存在带标注的 Golden Set 测试用例（≥3） —— 请人工判断是漏交还是本就不适用。
- 本报告只做结构与证据层判定，不评价方案语义质量，也不代替打分决策。

