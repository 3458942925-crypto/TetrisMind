# P2 渲染层规则

## 环境事实
- 项目根：当前 PyCharm 工作区根目录。
- Python 解释器：`.venv/Scripts/python.exe`。所有 python 命令均通过它执行，禁止使用全局 python。
- pygame 已安装在该 venv 中。禁止执行 pip install / pip uninstall / pip upgrade。
- contracts.py 位于项目根目录，是 State / Action / Engine 的唯一契约来源。
- 操作系统：Windows。所有路径使用 pathlib.Path，禁止硬编码盘符和用户名。

## P2 只读红线
- ui/ 下 render.py 和 input.py 不得对 state 任何属性赋值，不得调用 engine.step() 或任何引擎变更方法。
- 只有 replay.py 中的 ReplayPlayer 可以调用 engine.step(action)。
- input.py 只输出 Action，不驱动引擎。

## 入口约定
- 统一入口：`python -m ui --mode <mode>`。禁止创建 ui/demo.py。
- 每个模式必须支持 `--headless --frames N`，用于无窗口验证。

## 回放格式
- 回放文件统一为 JSON：{"seed": int, "actions": [...], "version": 1}。
- 回放路径禁止 random 或任何非确定性调用。