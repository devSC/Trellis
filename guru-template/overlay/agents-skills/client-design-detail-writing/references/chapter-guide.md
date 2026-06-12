# 详细设计分章写作指南（references）

> 编排层产物：只补充逐类写法细则、章节模板与示例，不替代 L1/L2。规则正文与完成条件以
> `.trellis/spec/harness/detail/detail-structure-single-source.md`（L1）与 `detail-type-*.md`（L2）为准。

## 1. 规范装载矩阵（按当前批次命中装载，不全量装）

| doc_type | L2 | 额外必读 |
|----------|----|---------|
| controller | detail-type-controller.md | golden-path §6（Presentation 迷你路径） |
| usecase | detail-type-usecase.md | golden-path §3（Domain 迷你路径） |
| repository-datasource | detail-type-repository-datasource.md | golden-path §4/§5 |
| page-entry / service / db-dao / api-network / config-l10n / external-platform | 无（pending，按 L1 八问） | 对应 golden-path 迷你路径 + L2豁免声明 |

## 2. 章节正文模板（L1 §4 骨架的操作版）

新章节从此模板起稿（full 链=chapters/<slug>.md；light 链=design.md §2 内一章，可压缩小节层级）：

````markdown
# <chapter_target> 详细设计

> doc_type：usecase ｜ l2_status：v1 ｜ 承接索引：design-main 第 7 节 <chapter_target>
> 返回：[design-main](../design-main.md)

## 1. 单元职责
`RecognitionUseCase` 负责拍照/文字两入口的识别业务流（上传→等待→结果/失败/重试），
是 domain 层状态 owner。依赖 `FoodRepository.uploadAndAnalyze`；被 `ScanFoodController`、
`DescribeFoodController` 调用并订阅其状态流。

## 2. 行为定义
### 2.1 行为清单
- recognizeFromPhoto — 拍照识别（BHV-021/022）｜详见 §4.1
- recognizeFromText — 文字识别（BHV-031）｜详见 §4.2

### 2.2 接口定义
```dart
abstract class RecognitionUseCase {
  Stream<RecognitionState> get state;
  Future<void> recognizeFromPhoto(PhotoInput input);
  Future<void> recognizeFromText(String description);
}
```

## 3. 核心数据结构
### 3.1 数据模型
```dart
sealed class RecognitionState {}        // idle / recognizing / success(result) / failed(reason)
class PhotoInput { final String path; final DateTime loggedAt; final MealType mealType; }
```
### 3.2 错误类型表
| 错误名 | 枚举 | 语义 | 上抛/收口位置 |
|-------|------|------|--------------|
| RecognitionFailure.network | network | 上传/请求失败 | repository 转换，本单元收口为 failed(networkRetry) |
| RecognitionFailure.timeout | timeout | 超过阈值（TD-01 假设 8s） | 本单元定时器收口 |

## 4. 逐行为设计
### 4.1 recognizeFromPhoto
- 签名：`Future<void> recognizeFromPhoto(PhotoInput input)`
- 简述：承接 BHV-021/BHV-022——上传图片、流转识别态、失败分类收口。
- 输入参数：
  | 参数 | 类型 | 取值域/约束 | 必填 |
  |------|------|-----------|------|
  | input | PhotoInput | path 为本地压缩后文件 | 是 |
- 输出：无返回值；经 `state` 流发射 recognizing → success/failed。
- 执行流程：
  ```mermaid
  sequenceDiagram
      participant C as ScanFoodController
      participant U as RecognitionUseCase
      participant R as FoodRepository
      C->>U: 1. recognizeFromPhoto(input)
      U->>U: 2. state=recognizing；启动超时定时器
      U->>R: 3. uploadAndAnalyze(input)
      R-->>U: 4. RecognitionResult / RecognitionFailure
      U-->>C: 5. state=success(result) / failed(reason)
  ```
- 流程详述：
  1. 入参校验（path 存在）；非法 → state=failed(invalidInput)，终止。
  2. 置 recognizing，启动 8s 超时定时器（阈值来源：TD-01 显式假设）。
  3. 调 `FoodRepository.uploadAndAnalyze(input)`（网络错误在 repository 按 SLOT-04 转为 RecognitionFailure）。
  4. 成功 → 取消定时器，state=success(result)。
  5. 失败/超时 → state=failed(对应枚举)；重试由调用方再次触发本行为（BHV-022）。
- 异常处理表：
  | 异常情况 | 处置 | 错误转换位置 |
  |---------|------|-------------|
  | 网络失败 | failed(networkRetry)，可重试 | repository（SLOT-04） |
  | 超时 | failed(timeout)，取消进行中请求 | 本单元定时器 |

## 5. 状态管理
RecognitionState 写 owner = 本单元（概要归属表 §3 行 BHV-021）；初始 idle。
转移：idle→recognizing→success|failed；failed→recognizing（重试）。禁止外部直接写。

## 6. Widget 设计
N/A（非 page-entry）。

## 7. 测试映射
| BHV/行为 | 测试层 | 测试点 |
|----------|--------|--------|
| BHV-021 成功路径 | unit | 状态序列 idle→recognizing→success |
| BHV-022 网络失败 | unit | failed(networkRetry)；重试后可成功 |
| BHV-022 超时 | unit | 8s 无响应 → failed(timeout) 且请求取消 |

## 8. 不得补造清单
- 不决定上传通道与缓存（属 food-repository / TD-01）。
- 不决定结果页展示形态（属 analyze-food-page）。
````

## 3. 九类写作步骤（4.1~4.9）

每类的共同骨架同上模板；以下只列类型要点与易错点。

### 4.1 usecase（v1，按 L2）
先行为后接口：从承接的 BHV 推导行为清单，再写 abstract class。状态流是一等公民（写 owner 声明 + 转移）。依赖只注入 repository/service 接口；依赖其他 usecase 须声明方向并说明为何不下沉（L2 规则）。

### 4.2 controller（v1，按 L2）
只做"事件→usecase 行为 + 状态订阅→UI 态"映射；出现业务规则（重试/阈值/校验逻辑）即越权——回查概要归属。生命周期（onInit/onClose）逐项写订阅与释放。三态（loading/content/error）映射表必写。

### 4.3 repository-datasource（v1，按 L2）
合同从 domain 需要出发（不从接口/表结构出发）；local/remote 编排与缓存回落策略在此定；错误转换点（SLOT-04）逐错误枚举写明转换前后类型。datasource 单一数据来源、无业务判断。

### 4.4 page-entry（pending，L1 八问 + 模板 §6）
路由注册（Routes 常量）、Binding 注册（canonical DI 写法引用 golden-path §2.3，不展开实现）、Widget 树要点、designSpec 消费。页面不拥有任何规则——八问之 8 必列"不拥有业务判定"。

### 4.5 service（pending）
无状态、无流；纯函数式签名。与 usecase 区分：有状态/有流即不是 service——发现状态需求回退概要改归属。

### 4.6 db-dao（pending）
表定义（列/索引/约束）、迁移版本号与升级脚本要点（签名级）、DAO 合同逐方法。数据模型与 §3.1 的 domain 模型区分（DTO↔Entity 映射归 mapper，写明归属）。

### 4.7 api-network（pending）
@RestApi 方法签名级（路径/动词/Query/Body）、req/resp model 字段表、错误上抛约定（HTTP 状态→统一异常）。不写 Dio 配置实现（属实现阶段）。

### 4.8 config-l10n（pending）
配置项表（key/类型/默认值/来源/消费方）、ARB key 清单（key/英文基线/使用页面）。**禁止触发 l10n 同步脚本**（SLOT-07 人工受控）——只列 key，不执行同步。

### 4.9 external-platform（pending）
逐 SDK/通道：能力范围、初始化时机（签名级）、调用方清单、合规面（权限/数据采集用途/PrivacyInfo 条目）、失败降级。凭证只写引用方式，secret value 出现即 P1。

## 4. 批次收敛与 checkpoint 操作细则

- 批内自动 review 检查单（逐项打钩后才置 chapter_status）：
  1. 模板节齐全（§2 模板 1~8，含 N/A 声明）；
  2. 八问逐 UNIT 可回指（L1 §3 括号内可验证信号）；
  3. 粒度抽查：任选一个行为，按 L1 §3.1 四条逐条判；
  4. 依赖出现在概要架构图/归属表中；
  5. L2 命中时逐条核对类型差异规则。
- 层级 checkpoint（L1 §5.4）操作：列出该层全部 UNIT → 跑对应核对项 → 失效项标注到章节 → 回批次修复。domain 层 checkpoint 通过前不开始 data 层批次。
- 修复闭环上限：同一 finding 修复 2 轮仍不收敛 → 按强制约束 11 升级用户，不得带病置 passed。

## 5. 禁止事项（写作期红线速查）

1. 一轮全量生成全部章节（每批 ≤3 章）。
2. 越过签名级写实现代码/伪代码。
3. 补造概要外结构、改 owner、拍板未选定技术决策。
4. 把"见概要"当八问答案（每问就地作答，可引用但须有本地结论）。
5. 跳过失败路径的测试映射。
6. 执行 l10n 同步脚本（SLOT-07）。
7. 代替用户执行 `guru_gate.py confirm`（无 TTY 会被拒）。
