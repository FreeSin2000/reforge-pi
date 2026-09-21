# reforge-pi

> 用 [pi](https://pi.dev) 重新学习开源项目（操作系统优先）的工作区：**读源码 + 真实构建 + 动态调试**，把理解沉淀成可追溯的笔记。
>
> Linux 6.12 只是起点，之后会扩展到各种开源项目。

## 它在解决什么

重新理解一个几十万行的项目，会遇到两个问题：

1. **理解**：怎么读得懂、记得住；
2. **不丢**：读了好几天的东西，不能因为会话压缩就没了。

本仓库用三条原则应对：

1. **知识外化到文件** —— 会话会丢，文件不会；
2. **知识与方法分离** —— 项目细节放 `notes/<project>/`，可迁移的抽象放 `notes/_concepts/`；
3. **先静态后动态，先主干后边角** —— 别一上来就上 gdb，别纠缠错误处理。

## 目录结构

```
reforge/
├── AGENTS.md      # 给 pi 的约定与方法论（pi 启动时自动加载）
├── HOWTO.md       # 人类使用手册（含 11 个使用示例）
├── notes/         # 所有学习产物
│   ├── _template/   # 新项目模板（index + 01~04）
│   ├── _concepts/   # 跨项目概念层（可迁移的抽象）
│   ├── _tooling/    # 工具清单 + 安装脚本
│   └── <project>/   # 每个项目一份笔记
└── src/           # 各项目源码树（git 忽略，不入库）
```

## 快速开始

```bash
# 1) 准备源码（本仓库不追踪源码）
mkdir -p src
# 例：下载 Linux 6.12
curl -LO https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.tar.xz
tar xf linux-6.12.tar.xz -C src/

# 2) 用 pi 打开工作区
cd /path/to/reforge
pi
```

进入 pi 后的第一句话（恢复上下文，别靠会话记忆）：

```
读 notes/<project>/index.md 恢复上下文，用 3 行说出现在读到哪、下一步、Open Questions。
```

完整流程、提示词模板与示例见 **[HOWTO.md](HOWTO.md)**；给 pi 的约定见 **[AGENTS.md](AGENTS.md)**。

## 拿到一个新项目要做什么

每个项目产出四份笔记（对应 `notes/<project>/`）：

| 文件 | 回答的问题 |
|------|-----------|
| `01-structure.md` | 这棵树里有什么？哪些是源码/文档/配置/测试？从哪读起？ |
| `02-build.md` | 怎么构建？构建系统、脚本、选项、依赖？ |
| `03-main-path.md` | 正常启动/运行的主干调用链是什么？（忽略错误处理） |
| `04-debug-plan.md` | 将来要动态调试该怎么做、需要准备什么？ |

配套记录：`index.md`（状态 + Open Questions + Reading Log）、`journal.md`（动态问答时间线）、
`glossary`/`map`（检索层，按需）、`notes/_concepts/`（跨项目抽象）。

## 依赖

- **[pi](https://pi.dev)** 编码代理
- 源码阅读 / 调试工具：`rg`、`cscope`、`universal-ctags`、`gcc`、`make`、`qemu`、`gdb`、`tmux`
  - 一键安装（需 sudo）：`sudo bash notes/_tooling/install-tools.sh`

## 当前项目

- **Linux 6.12 (LTS)** —— 笔记在 `notes/linux-6.12/`（脚手架就位，四份笔记待填写）

## 说明

- 本仓库**只追踪框架与笔记**，`src/` 下的源码树不入库；克隆后请自行准备源码。
- `AGENTS.md` 面向 pi，`HOWTO.md` / `README.md` 面向人。
