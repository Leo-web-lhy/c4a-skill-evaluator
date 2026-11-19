# C4A 技能提交自动评审器（skill-evaluator）

一个**确定性**的技能提交评审工具：给它一个提交目录，它按 C4A rubric 的五个维度打分，输出 `report.json`（机器可读）与 `report.md`（人可读），每条结论都带**文件 + 行号 + 原文片段**的证据。

- 学号：2023108610260
- 工具版本：`c4a-evaluator/1.0.0`
- rubric 版本：`C4A 1.0.0`（`skill-evaluator/rubrics/c4a.json`）

## 1. 它解决什么问题

C4A 类技能提交的评审痛点是：**「写得像」和「真的做了」很难靠读文档区分**。人工评审要么花很多时间逐条核对，要么被措辞说服。

本工具把评审拆成三层：

| 层 | 职责 | 关键约束 |
| --- | --- | --- |
| 收集层 `lib/collect.py` | 遍历提交目录，产出 path/size/lines/text 的结构化文件表 | 跳过 `.git` / `node_modules` / `__pycache__` / `.venv` 等目录 |
| 探针层 `lib/signals.py` | 用 5 类探针（regex / absent / exists / size / count_files）采集证据 | 探针只**采集**，不下结论；没有证据就没有分数 |
| 评分层 `lib/scoring.py` | 权重 + 维度上限 + 红牌封顶 | 红牌只**封顶**，永不自动判定「不通过」 |

## 2. 明确不做什么（非目标）

1. **不评价语义质量**：它判断不了「这个方案好不好」，只判断「可验证的要素是否真的存在」。
2. **不自动拒绝**：任何红牌都只把对应维度封顶（如缺 AI 日志 → 反思维度最高 5 分），最终结论留给人。
3. **不猜缺失原因**：缺文件就报缺文件，不推测「大概是忘了」。
4. **不留无证据结论**：每条扣分都指向具体文件与行号。

## 3. 快速开始

```powershell
cd skill-evaluator
python evaluator.py --submission ..\..\C9\tabledoctor --out ..\demo\c9_tabledoctor --label c9_tabledoctor
```

输出：

```
label=c9_tabledoctor
files=31
total=49/100
  evaluatorQuality        8/25
  technicalExecution     16/20
  artifactCompleteness    5/15
  aiUsage                10/20
  reflectionQuality      10/20
red_flags=1
  flag missing_artifacts cap=5
deliverables=1/4
evidence_hash=d0ef143a0d266f92
json=..\demo\c9_tabledoctor\report.json
md=..\demo\c9_tabledoctor\report.md
```

> 控制台只打印 ASCII 统计行；所有中文材料写入 UTF-8 文件。这是为了让工具在中文 Windows 控制台上稳定运行（本机实测：非 ASCII 字面量会导致进程直接退出且不落任何输出）。

### 参数

| 参数 | 说明 |
| --- | --- |
| `--submission` | 待评审的提交目录（必填） |
| `--rubric` | 评分规则 JSON，默认 `rubrics/c4a.json` |
| `--out` | 报告输出目录，默认 `out/<label>` |
| `--label` | 报告标题与目录名 |

退出码：`0` 表示正常产出报告（**不代表通过评审**，只代表工具跑通）；`2` 表示参数或 rubric 错误。

## 4. 评分口径

总分 100，五个维度：

| 维度 | 满分 | 主要探针 |
| --- | --- | --- |
| evaluatorQuality 评审器质量 | 25 | rubric 外置、golden set、自测报告、结构化输出、可复现 |
| technicalExecution 技术实现 | 20 | 分层模块、无 TODO 残留、错误处理、版本清单、CLI 入口 |
| artifactCompleteness 交付完整度 | 15 | 四件必交物齐全且非空壳 |
| aiUsage AI 使用 | 20 | 日志规模、迭代轮次、Prompt 记录、失败与转向记录 |
| reflectionQuality 反思质量 | 20 | AAR 存在、具体卡点、可执行改进、失败保留 |

红牌（只封顶，不淘汰）：

| 红牌 | 触发条件 | 后果 |
| --- | --- | --- |
| `missing_artifacts` | 必交物缺失或为 20 字节以下空壳 | artifactCompleteness ≤ 5 |
| `no_ai_log` | 找不到 AI 日志 | reflectionQuality ≤ 5 |
| `one_shot_ai` | 有日志但日志过薄且无任何迭代记录 | aiUsage ≤ 5 |

## 5. Golden Set 与误判率

`tests/golden/` 下有 6 个用例，覆盖「理想提交 / 缺 AAR / 缺评审报告 / 无 AI 日志 / 有日志无迭代 / 评审报告为空壳」：

```powershell
cd skill-evaluator
python tests\golden\build_fixtures.py    # 从 fixtures.json 生成用例目录
python tests\golden\run_golden.py        # 断言语义 + 确定性，输出 results.json
```

最新一次结果：

```
PASS 01_perfect           total=100 flags=-
PASS 02_missing_aar       total= 80 flags=-
PASS 03_missing_report    total= 90 flags=missing_artifacts
PASS 04_no_ai_log         total= 55 flags=missing_artifacts,no_ai_log
PASS 05_no_iteration      total= 95 flags=-
PASS 06_empty_report      total= 90 flags=missing_artifacts
cases=6 passed=6 failed=0 fp=0 fn=0
```

断言的不是「分数等于某个魔数」，而是语义关系：期望红牌集合一致、封顶维度不超过上限、总分落区间、`05_no_iteration` 的 aiUsage 必须低于基线，且两次运行在 `evidence_hash`、总分与每个维度分上完全一致。

## 6. 确定性

工具**不调用任何模型、不联网、不含时钟与随机数**。同一份提交连续两次运行，`evidence_hash` 必须相同；`run_golden.py` 对每个用例跑两遍并比对，不一致即判 FAIL。

## 7. 目录结构

```
skill-evaluator/
  evaluator.py          CLI 入口（ASCII 统计输出）
  rubrics/c4a.json      rubric 与探针定义（中文集中在 JSON 里）
  lib/collect.py        目录遍历 → 文件表
  lib/deliverables.py   必交物匹配（按文件名，与平台语义一致）
  lib/signals.py        5 类探针 → 证据
  lib/scoring.py        权重 / 维度上限 / 红牌封顶
  lib/render.py         report.json / report.md 渲染
  tests/golden/         fixtures.json + 生成器 + 断言 runner + results.json
```

## 8. 已知边界

- 只做**文件级**证据，不做行内语义判断；「方案写得好不好」仍需人评。
- 必交物按**文件名**匹配（与平台 `requiredDeliverables` 的语义一致），换名提交会被判缺失——这是刻意的，宁可提示也不猜测。
- 只在 Windows + Python 3.12 上实跑验证过，其他平台未验证。
