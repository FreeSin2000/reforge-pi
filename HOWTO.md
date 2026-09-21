# HOWTO — reforge 人类使用手册

> 这份文档写给**你（人）**，不是给 pi 的。pi 的约定在 `AGENTS.md`。
> 目标：让你知道每天怎么用这个工作区，以及什么时候该给 pi 下什么指令。

---

## 0. 这个框架在解决什么

你同时面对两个问题：
1. **理解**：一个几十万行的项目，怎么读得懂、记得住；
2. **不丢**：读了好几天的东西，不能因为会话压缩就没了。

框架的答案只有三句话：

1. **知识外化到文件**——会话会丢，文件不会；
2. **知识与方法分离**——项目细节放 `notes/<project>/`，可迁移的抽象放 `notes/_concepts/`；
3. **先静态后动态，先主干后边角**——别一上来就上 gdb，别纠缠错误处理。

---

## 1. 心智模型（30 秒）

```
                    ┌─────────────────────────────────────┐
   地图（知识）      │ AGENTS.md        —— 工作区约定/方法论  │
                    │ notes/<project>/ —— 每个项目的四份笔记 │
                    └─────────────────────────────────────┘
   跨项目（抽象）    ┌─────────────────────────────────────┐
                    │ notes/_concepts/ —— 可迁移的理解       │
                    └─────────────────────────────────────┘
   方法（未来）      ┌─────────────────────────────────────┐
                    │ skill / extension —— 重复 ≥3 次才做   │
                    └─────────────────────────────────────┘
```

**产物阶梯**：零散笔记 → 结构化笔记（01~04）→ 摘要/调用图 → 能白板复述的模型。
每上一级，都要落盘。

---

## 2. 每天怎么用（保姆级流程）

### 2.1 开始（每天/每次）

```bash
cd /home/freesin2000/learning/reforge
pi -c          # 继续上一个会话；想挑会话用 pi -r
```

进入后**第一句话固定是**（让 pi 恢复上下文，别靠会话记忆）：

```
读 notes/linux-6.12/index.md 恢复上下文，用 3 行告诉我：现在读到哪、下一步、有什么 Open Questions。
```

会话一开始就命名，方便以后找回：

```
/name linux-6.12 01-structure
```

### 2.2 工作中

- **让 pi 先看笔记再动手**：`读 notes/linux-6.12/01-structure.md，然后……`
- **要求证据**：结论要带 `路径:行` 或实测命令 —— 这是笔记质量的底线。
- **偏题就 parking**（见 4.4），不要被带跑。
- 需要看某个文件：用 `@` 引用，如 `@src/linux-6.12/init/main.c`。

### 2.3 结束 / 中断前（**最重要的一步**）

```bash
# 先让 pi 落盘
> 把今天的结论整理进 notes/linux-6.12/01-structure.md，
> 更新 notes/linux-6.12/index.md 的 TL;DR、状态、Reading Log。
```

确认写完后，压缩上下文：

```
/compact 保留：已确定的核心目录职责、入口文件、未解决的 Open Questions。
```

### 2.4 换方向 / 对比假设

```
/fork    # 从当前分叉出新会话，原方向保留
/tree    # 回看历史、在旧节点上继续
/clone   # 复制当前分支另起一条
```

---

## 3. 做一个新项目的标准流程

```bash
# 1) 建脚手架
cd notes && cp -r _template <project> && cd ..
# 2) 把源码放进 src/<project>/
# 3) 修改 notes/<project>/index.md 的「快速事实」
```

然后依次做四步，**每步一个会话**：

| 步 | 给 pi 的指令核心 | Done-when（做完的标准） |
|----|-----------------|------------------------|
| 01-structure | 「分层分类顶层目录，标出核心阅读对象和入口文件，别展开读源码」 | 不看树也能说出核心目录职责 + 从哪读起 |
| 02-build | 「梳理构建系统、脚本阅读顺序、选项、依赖，给出最小构建流程；先别真构建」 | 能从零复现构建 + 说清主要选项 |
| 03-main-path | 「只追正常启动主干，忽略错误处理；每阶段标锁与所有权」 | 能白板画出主干 |
| 04-debug-plan | 「给出 build/boot/debug 命令和前置 checklist，先规划不执行」 | 前置条件全绿 + 有脚本 |

四份写完后，回头把 `index.md` 的 TL;DR 提炼到 3~5 行。

---

## 4. 可直接复制的提示词模板

### 4.1 开始一份新文档

```
读 notes/<project>/index.md 恢复上下文。今天做 <NN-xxx>。
范围：<具体边界，如「先只分类顶层目录，不展开读源码」>。
要求：每条结论带 路径:行 或实测命令，直接写进 notes/<project>/<NN-xxx>.md；
完成后更新 index.md 的状态、TL;DR、Reading Log。
```

### 4.2 中途落盘（防止丢失）

```
先把目前已经确定的结论写进 notes/<project>/<NN-xxx>.md（带证据），
不确定的标「未验证」，然后我们再继续。
```

### 4.3 压缩前（先写后压）

```
把当前结论整理进 notes/<project>/<NN-xxx>.md；
更新 index.md 的 TL;DR、当前 Open Questions、Reading Log。
写完告诉我一句「可以压缩了」。
```
然后你再 `/compact`。

### 4.4 parking（遇到偏题）

```
这个点先 parking：作为一条 Open Question 写进 index.md，不要现在展开。
```

### 4.5 动态调试准备（只规划）

```
写 notes/<project>/04-debug-plan.md：给出构建带符号版本的命令、运行方式（qemu/容器）、
gdb 连接方式、首批断点、以及前置条件 checklist。不要执行任何构建。
```

### 4.6 沉淀跨项目概念

```
这条「<概念>」在别的项目里也成立，写进 notes/_concepts/<concept>.md 的「通用形态」，
并在项目笔记里引用它（不要复制）。
```

---

## 5. 使用示例

> 每题格式：**场景 → 你输入 → pi 应做 → 落到哪个文件**。命令都在 `reforge/` 下执行。

### 5.1 首次实战：Linux 6.12 做 01-structure

```bash
cd /home/freesin2000/learning/reforge
pi
```

1. 命名会话：`/name linux-6.12 01-structure`
2. 发：

```
读 notes/linux-6.12/index.md 恢复上下文。今天做 01-structure：
用 du/find 给顶层目录分类（源码/文档/构建/测试/工具/生成物），
标出核心阅读对象和 3 个入口文件，写进 notes/linux-6.12/01-structure.md，带证据。
不要展开读源码。
```

3. 中途 pi 若开始深挖某个子系统 → 用 5.4 parking。
4. 结束时用 5.3 落盘，再 `/compact`。
5. 满足 Done-when 后，把 index 里 `01-structure` 打勾。

**落到文件**：`notes/linux-6.12/01-structure.md`（正文）+ `index.md`（状态/Log）。

---

### 5.2 接入一个新项目（以 xv6-riscv 为例）

```bash
cp -r notes/_template notes/xv6-riscv
pi
```

**你输入**

```
新建项目 xv6-riscv，源码在 /home/freesin2000/learning/xv6-riscv。
先只填 notes/xv6-riscv/index.md 的「快速事实」：版本、语言、规模、构建系统、入口、许可证。
证据用实测命令（du/find/wc/读 Makefile）。01~04 先不动。
```

**pi 应做**：`du -sh` / `find | wc` 统计规模；读 `README`、`Makefile`；填表并附证据。
**落到文件**：`notes/xv6-riscv/index.md`。

---

### 5.3 中途落盘 + 压缩（防丢失）

**你输入（分两段）**

```
先把目前已经确定的结论写进 notes/linux-6.12/01-structure.md（带证据），
不确定的标「未验证」，然后我们再继续。
```

```
更新 index.md 的 TL;DR、Open Questions、Reading Log，完成后说「可以压缩了」。
```

然后你手动压缩：

```
/compact 保留：顶层目录分类结论、入口文件、未解决的 Open Questions。
```

**关键**：压缩前一定先看到文件已写入。

---

### 5.4 parking 偏题

**你输入**

```
这个点先 parking：作为一条 Open Question 写进 index.md，不展开。
```

**结果**：`index.md` 的 Open Questions 多出一条，例如

```markdown
- [ ] printk 的环形缓冲区如何避免递归？（parking from 01-structure）
```

---

### 5.5 追一条主干路径（03）

**你输入**

```
读 notes/linux-6.12/03-main-path.md 现有内容。只追 x86_64 正常启动主干：
arch/x86/boot/compressed → startup_64 → start_kernel → rest_init → kernel_init → run_init_process。
每步给 路径:行，忽略错误分支，每阶段标出锁与所有权。写进 03-main-path.md。
```

**pi 应产出**（示例形态）：

```
start_kernel()          init/main.c:xxx
  -> setup_arch()       arch/x86/kernel/setup.c:xxx
  -> trap_init()        arch/x86/kernel/traps.c:xxx
  -> rest_init()        init/main.c:xxx
       -> kernel_thread(kernel_init, ...)   init/main.c:xxx
       -> cpu_startup_entry()               kernel/sched/idle.c:xxx
```

**落到文件**：`notes/linux-6.12/03-main-path.md`（证据=每行 `file:line`）。

---

### 5.6 用 cscope/ctags 替代盲目 grep

```bash
cd src/linux-6.12
cscope -Rbkq -s kernel -s mm -s fs -s include   # 只给核心目录建库
```

**你输入**

```
用 cscope（别 grep 扫全树）找出所有调用 start_kernel 的位置，列 路径:行，先别总结。
```

**pi 应做**：`cscope -dLq -3 start_kernel`，把结果作为 03 的证据；需要定义用 `-1`，需要它调用了谁用 `-2`。

---

### 5.7 分叉对比假设（/fork）

```
/fork
> 假设：内核在 A 点完成 X，从 A 往下的调用链是……
（让 pi 去验证这条假设）

/tree            # 回到分叉点，选另一条
> 假设：其实在 B 点，理由是……
```

**价值**：两条分支的结论并存，对比后把「采信哪条」写进 index 的 Open Questions 决议。

---

### 5.8 规划动态调试（04，只规划不执行）

**你输入**

```
写 notes/linux-6.12/04-debug-plan.md：构建带符号版本的命令、运行方式（qemu）、
gdb 连接方式、首批断点、前置条件 checklist。不要执行任何构建。
```

**落到文件**：`notes/linux-6.12/04-debug-plan.md`。

---

### 5.9 真正跑构建 + qemu+gdb

先由**你确认**再执行。

**你输入**

```
可以执行了。用 tmux 分窗：
1) 在 .config 开启 CONFIG_DEBUG_INFO；
2) make -j"$(nproc)" bzImage；
3) qemu -kernel arch/x86/boot/bzImage -append "console=ttyS0 nokaslr" -nographic -s -S；
4) gdb vmlinux 连 :1234，在 start_kernel 下断点。
每步输出写到 notes/linux-6.12/raw/。
```

**pi 应做**：开 tmux、执行、把原始输出存到 `raw/`；成功后把 `index.md` 的 M1/M2/M3 打勾。
**落到文件**：`notes/linux-6.12/raw/*`、`04-debug-plan.md`、`index.md`。

---

### 5.10 沉淀跨项目概念（_concepts）

**你输入**

```
把「调度器的通用结构」这条抽象写进 notes/_concepts/scheduler-design.md 的「通用形态」，
并在 notes/linux-6.12/03-main-path.md 里引用它（不要复制内容）。
```

**落到文件**：`notes/_concepts/scheduler-design.md` + 项目笔记里的引用行。

---

### 5.11 换会话 / 恢复上下文

```bash
pi -c        # 续接最近会话
pi -r        # 列出所有会话，按 /name 起的名字挑
```

**进入后第一句**

```
读 notes/linux-6.12/index.md 恢复上下文，用 3 行说出现在读到哪、下一步、Open Questions。
```

---

## 6. 会话操作速查

| 命令 | 用途 |
|------|------|
| `pi -c` / `pi -r` | 续接最近 / 挑选会话 |
| `pi --name "x"` | 启动即命名 |
| `/name <x>` | 给当前会话命名 |
| `/tree` | 会话树，回看/跳转 |
| `/fork` / `/clone` | 从某点分叉 / 复制当前分支 |
| `/compact [提示]` | 手动压缩（有损，先落盘） |
| `/resume` / `/new` | 恢复 / 新建会话 |
| `/export [file]` | 导出会话为 HTML/JSONL |
| `@file` | 在消息里引用文件 |
| `!cmd` / `!!cmd` | 跑命令并把输出发给 pi / 不发 |
| `Ctrl+X` | 复制上一条回复 |

---

## 7. 笔记约定速查

- 文件名固定：`index.md` + `01-structure` … `04-debug-plan`。
- **证据**：`相对路径:行号` 或 commit hash；没有就写「未验证」。
- **单一事实来源**：同一结论只写一处，别处引用。
- 进度用 `[ ]` / `[x]`。
- 结尾必留 **Open Questions**。

目录：

```
reforge/
├── AGENTS.md          # 给 pi 的约定（自动加载）
├── HOWTO.md           # 本文件，给人看
├── .gitignore         # 忽略 src/
├── src/               # 各项目源码树（不入库）
│   └── linux-6.12/
└── notes/
    ├── _template/     # 新建项目从这里复制
    ├── _concepts/     # 跨项目抽象
    ├── _tooling/      # 工具清单 + 安装脚本
    └── linux-6.12/    # 当前项目笔记
```

---

## 8. 里程碑与完成判据

**Milestones**（在 `index.md` 里打勾）：

| 节点 | 含义 |
|------|------|
| M1 能构建 | 从干净源码产出可运行产物 |
| M2 能运行 | 独立跑起来，看到预期输出/启动 |
| M3 能观测 | 能加载符号、命中第一个断点 |
| M4 能追踪 | 能沿主干动态验证一个假设 |

**Done-when**：见 `index.md` 的表格；满足即收尾，不追求读完整棵树。

---

## 9. 工具速查

已就绪：`rg`、`cscope`、`universal-ctags`、`gcc`、`make`、`qemu`、`gdb`、`tmux`。
待装（需 sudo）：`clangd`、`bear`、`pahole` → `sudo bash notes/_tooling/install-tools.sh`

**建索引（限定范围，别全树）**：

```bash
cd src/linux-6.12
# cscope：对核心目录建库
cscope -Rbkq -s kernel -s mm -s fs -s include -s arch/x86
# 查询（-L 行模式，-d 不重建，-q 用倒排索引）
cscope -dLq -0 task_struct      # 找符号
cscope -dLq -1 start_kernel     # 找定义
cscope -dLq -3 start_kernel     # 谁调用了它
cscope -dLq -2 start_kernel     # 它调用了谁

# universal-ctags
ctags -R --fields=+n -f tags kernel mm fs include
readtags -t tags - start_kernel
```

**构建 / 调试预备命令**（`04-debug-plan` 里规划，**确认后再执行**）：

```bash
make x86_64_defconfig                 # 生成 .config
make -j"$(nproc)" bzImage             # 构建（需带 DEBUG_INFO 才适合调试）

# qemu 启动 + 冻结等 gdb（-s = gdbstub:1234, -S = 冻结）
qemu-system-x86_64 -kernel arch/x86/boot/bzImage \
  -append "console=ttyS0 nokaslr" -nographic -s -S

# 另开 tmux 窗格 / 终端
gdb vmlinux -ex 'target remote :1234' -ex 'b start_kernel' -ex 'c'
```

---

## 10. 反模式（别这么干）

| 别做 | 因为 |
|------|------|
| 把结论只留在会话里 | compaction 有损，白读 |
| 一上来就 qemu+gdb | 没主干地图，断点乱打 |
| 在 drivers/ 里迷路 | 占 69%，是噪声不是主线 |
| 追求读完整棵树 | 内核无限深，用 Done-when 收口 |
| 同一会话无限堆 | 用 `/fork` 分叉、`/name` 命名 |
| 预先写一堆 skill | 没重复到 3 次，写出来必错 |

---

## 11. 什么时候升级成 skill / extension

**rule of three**：同一个动作你**手动做了 3 次**，再固化。

- 重复的命令序列 → 写成 `notes/<project>/scripts/*.sh`（先脚本）；
- 重复的**方法**（跨项目）→ skill；
- 需要**自动化 / 拦截 / 自定义 UI** → extension。

候选（先记录在 `04-debug-plan.md`，不实现）：
GDB/MI 工具集、qemu 生命周期管理、source-index 查询、自动注入 `index.md`、`/checkpoint` 命令。

---

## 一句话

**每次开工先读 `index.md`；每有结论就落盘；压缩前先写；偏题就 parking；重复到 3 次再固化。**
