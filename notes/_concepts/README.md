# 跨项目概念层

这里放**项目无关**的理解——能迁移到下一个开源项目的抽象，而不是某个项目的细节。

- 项目细节 → `notes/<project>/`
- 只有当一条结论**在别的项目里也成立**时，才放这里。

## 用法

1. 读项目时遇到可迁移的抽象，**记进对应概念文件**；
2. 在项目笔记里**引用**它，不要复制内容（单一事实来源）；
3. 开新项目前**先读这里**，避免重复发明。

## 候选概念文件

按需创建，**不要预先铺满**：

`build-system-patterns.md` · `init-and-boot.md` · `scheduler-design.md` ·
`concurrency-primitives.md` · `memory-management.md` · `ipc-and-syscall.md` ·
`plugin-and-registry-patterns.md` · `error-handling-strategies.md`

## 写法

见 `_TEMPLATE.md`。核心是：**先写通用形态与权衡，再列你见过的实例**。
