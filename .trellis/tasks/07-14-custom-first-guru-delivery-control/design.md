# Custom-first Guru Delivery Control Plane Design

本任务是 `guru_chain=full` 的高风险控制面改造，正式设计 SSOT 位于：

- 导航：[`design-package/README.md`](design-package/README.md)
- 概要主定义：[`design-package/design-main.md`](design-package/design-main.md)
- 详细设计：[`design-package/chapters/`](design-package/chapters/)

## 摘要

设计以官方 Custom-first、功能阶段 Trellis Core 零修改、完整可卸载为边界，将 Guru 的 Template Registry、project-local Extension、全任务路由、语义摘要、独立 review、有限监督、上下文复用、设计同步与回放基准收敛为一套可验证控制面。

本文件仅保留任务入口和摘要；行为归属、架构图、章节承接索引、UNIT 合同与测试映射均以正式设计包为准。
