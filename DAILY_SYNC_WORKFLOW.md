# 每日协同开发指令手册

这份文档用于你在家里和办公室两台电脑之间稳定协同开发。  
工作目录默认：`~/Perception`

---

## 0. 一次性准备（首日）

```bash
cd ~/Perception
git remote -v
```

- 什么时候执行：第一次配置仓库时
- 含义：确认当前仓库是否已经绑定远程 GitHub 地址

```bash
source ~/.bashrc
alias wt-sync
```

- 什么时候执行：第一次配置快捷命令后
- 含义：加载 shell 配置，并确认 `wt-sync` 快捷命令可用

---

## 1. 每天开始工作前（必须执行）

```bash
cd ~/Perception
git pull --rebase
```

- 什么时候执行：每天开工第一步
- 含义：
  - `cd ~/Perception`：进入你的统一工作区
  - `git pull --rebase`：先拉最新代码并把本地提交“平铺”到最新版本上，减少冲突

---

## 2. 开发与进度更新阶段（工作中）

```bash
cd ~/Perception
python3 weekly_tracker.py web --port 8765
```

- 什么时候执行：开始记录目标/进度时
- 含义：
  - 启动可视化进度工具
  - 浏览器打开 `http://127.0.0.1:8765`

```bash
cd ~/Perception
python3 weekly_tracker.py update 2026-W19 1 --progress 40 --status in_progress --note "完成图像订阅与检测发布"
```

- 什么时候执行：当日某个目标有进展时
- 含义：
  - 更新指定周、指定目标的进度百分比/状态
  - 把当天进展写入备注，便于复盘和同步

> 说明：你可以用网页更新，也可以用命令行更新，数据写入同一个文件 `weekly_tracker_data.json`。

---

## 3. 每天结束工作前（必须执行）

### 推荐一键命令（最简单）

```bash
cd ~/Perception
wt-sync 2026-W19 --output synchronization_2026-W19.md
```

- 什么时候执行：每天收工前最后一步
- 含义（`wt-sync` 会自动执行以下动作）：
  1. 导出同步文档 `synchronization_2026-W19.md`
  2. `git pull --rebase`
  3. `git add weekly_tracker_data.json synchronization_2026-W19.md`
  4. `git commit`
  5. `git push`

### 先演练不提交（可选）

```bash
cd ~/Perception
wt-sync 2026-W19 --output synchronization_2026-W19.md --dry-run
```

- 什么时候执行：第一次使用或不确定时
- 含义：只打印将执行的命令，不真正提交/推送

---

## 4. 切换电脑时（家里 <-> 办公室）

### 在离开当前电脑前

```bash
cd ~/Perception
wt-sync 2026-W19 --output synchronization_2026-W19.md
```

- 什么时候执行：准备离开当前电脑时
- 含义：确保代码和进度都已经推送到远程

### 在另一台电脑开始前

```bash
cd ~/Perception
git pull --rebase
```

- 什么时候执行：另一台电脑开工前
- 含义：把刚才那台机器的最新修改同步下来

---

## 5. 每周固定操作

### 环境一致性检查（两台电脑都做）

```bash
cd ~/Perception
./environment_check/check_ros2_env.sh
```

- 什么时候执行：每周至少一次，或升级 ROS2/系统后立即执行
- 含义：采集当前机器 ROS2 与系统环境，生成 `environment_check/env_<hostname>_<timestamp>.txt`

### 对比家里与办公室环境

```bash
cd ~/Perception
./environment_check/compare_env_reports.sh
```

- 什么时候执行：两台电脑都生成报告后
- 含义：自动对比最近两份报告，检查 `ROS_DISTRO`、`ros2 --version`、`RMW_IMPLEMENTATION` 等关键项是否一致

### 查看本周状态

```bash
cd ~/Perception
python3 weekly_tracker.py report 2026-W19
```

- 什么时候执行：每周中检查进度/周末复盘前
- 含义：输出本周目标、完成度、备注、复盘信息

### 生成下周计划（滚动未完成项）

```bash
cd ~/Perception
python3 weekly_tracker.py plan-next 2026-W19 2026-W20 --theme "Fusion稳定性优化"
```

- 什么时候执行：周末做下周计划时
- 含义：把本周未完成目标自动滚动到下周

---

## 6. 异常处理（常见问题）

### 1）`git push` 失败（远程有新提交）

```bash
cd ~/Perception
git pull --rebase
git push
```

- 含义：先把远程变更整合到本地，再重新推送

### 2）提示有冲突（尤其是 `weekly_tracker_data.json`）

```bash
cd ~/Perception
git status
```

- 含义：查看冲突文件

手动编辑冲突后执行：

```bash
git add weekly_tracker_data.json
git rebase --continue
git push
```

- 含义：确认冲突解决并继续 rebase，然后推送

### 3）忘了本周编号

```bash
cd ~/Perception
python3 weekly_tracker.py dashboard
```

- 含义：查看所有周编号和完成度

---

## 7. 你每天最小必做清单（30秒版）

```bash
cd ~/Perception
git pull --rebase
# 开发 + 更新进度
wt-sync 2026-W19 --output synchronization_2026-W19.md
```

只要坚持这三步，你的两台电脑就能稳定协同，代码和进度会始终同步。
