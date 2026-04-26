#!/usr/bin/env python3
"""
Weekly goal planner and progress tracker for skill building.

Usage examples:
  python weekly_tracker.py new-week 2026-W18 "Camera+Fusion 入门"
  python weekly_tracker.py add-goal 2026-W18 "跑通ROS2相机检测链路" --metric "demo可运行" --weight 35
  python weekly_tracker.py update 2026-W18 1 --progress 60 --note "已完成图像订阅和检测发布"
  python weekly_tracker.py plan-next 2026-W18 2026-W19 --theme "Fusion 稳定性强化"
  python weekly_tracker.py web --port 8765
  python weekly_tracker.py report 2026-W18
  python weekly_tracker.py dashboard
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


DATA_FILE = Path("weekly_tracker_data.json")


@dataclass
class Goal:
    id: int
    title: str
    metric: str
    weight: int
    progress: int
    status: str
    notes: List[str]


def load_data() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        return {"weeks": {}}
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: Dict[str, Any]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_week(data: Dict[str, Any], week_id: str) -> Dict[str, Any]:
    weeks = data.setdefault("weeks", {})
    if week_id not in weeks:
        raise ValueError(f"周 {week_id} 不存在，请先执行 new-week。")
    return weeks[week_id]


def calc_week_score(goals: List[Dict[str, Any]]) -> float:
    if not goals:
        return 0.0
    total_weight = sum(g["weight"] for g in goals)
    if total_weight <= 0:
        return 0.0
    weighted = sum((g["progress"] / 100.0) * g["weight"] for g in goals)
    return (weighted / total_weight) * 100.0


def cmd_new_week(args: argparse.Namespace) -> None:
    data = load_data()
    weeks = data.setdefault("weeks", {})
    if args.week_id in weeks:
        raise ValueError(f"周 {args.week_id} 已存在。")

    weeks[args.week_id] = {
        "theme": args.theme,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "goals": [],
        "retrospective": "",
        "next_week_focus": "",
    }
    save_data(data)
    print(f"已创建周计划: {args.week_id} | 主题: {args.theme}")


def is_goal_done(goal: Dict[str, Any]) -> bool:
    return goal.get("status") == "done" or goal.get("progress", 0) >= 100


def cmd_add_goal(args: argparse.Namespace) -> None:
    data = load_data()
    week = ensure_week(data, args.week_id)
    goals = week["goals"]
    goal_id = len(goals) + 1
    goal = Goal(
        id=goal_id,
        title=args.title,
        metric=args.metric,
        weight=args.weight,
        progress=0,
        status="not_started",
        notes=[],
    )
    goals.append(asdict(goal))
    save_data(data)
    print(f"已添加目标 #{goal_id}: {args.title}")


def cmd_update(args: argparse.Namespace) -> None:
    data = load_data()
    week = ensure_week(data, args.week_id)
    goals = week["goals"]
    if args.goal_id < 1 or args.goal_id > len(goals):
        raise ValueError(f"目标编号无效: {args.goal_id}")

    goal = goals[args.goal_id - 1]
    if args.progress is not None:
        if not (0 <= args.progress <= 100):
            raise ValueError("progress 必须在 0 到 100 之间。")
        goal["progress"] = args.progress

    if args.status is not None:
        if args.status not in {"not_started", "in_progress", "blocked", "done"}:
            raise ValueError("status 必须是 not_started/in_progress/blocked/done。")
        goal["status"] = args.status

    if args.note:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        goal["notes"].append(f"[{stamp}] {args.note}")

    save_data(data)
    print(
        f"目标 #{goal['id']} 已更新: progress={goal['progress']}%, status={goal['status']}"
    )


def cmd_retro(args: argparse.Namespace) -> None:
    data = load_data()
    week = ensure_week(data, args.week_id)
    week["retrospective"] = args.text
    save_data(data)
    print(f"已更新 {args.week_id} 复盘。")


def cmd_next_focus(args: argparse.Namespace) -> None:
    data = load_data()
    week = ensure_week(data, args.week_id)
    week["next_week_focus"] = args.text
    save_data(data)
    print(f"已更新 {args.week_id} 下周重点。")


def cmd_plan_next(args: argparse.Namespace) -> None:
    data = load_data()
    weeks = data.setdefault("weeks", {})

    if args.from_week not in weeks:
        raise ValueError(f"来源周 {args.from_week} 不存在。")
    if args.to_week in weeks:
        raise ValueError(f"目标周 {args.to_week} 已存在，请换一个周编号。")

    from_week = weeks[args.from_week]
    from_goals = from_week.get("goals", [])
    carry_goals = [
        g for g in from_goals if args.copy_all or (not is_goal_done(g))
    ]

    to_theme = args.theme or f"{from_week.get('theme', '学习计划')}（滚动）"
    new_week = {
        "theme": to_theme,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "goals": [],
        "retrospective": "",
        "next_week_focus": "",
    }

    for idx, g in enumerate(carry_goals, start=1):
        carry_note = (
            f"从 {args.from_week} 延续: 原进度 {g.get('progress', 0)}%, "
            f"原状态 {g.get('status', 'unknown')}"
        )
        new_week["goals"].append(
            {
                "id": idx,
                "title": g.get("title", "未命名目标"),
                "metric": g.get("metric", "可交付结果"),
                "weight": g.get("weight", 20),
                "progress": 0,
                "status": "not_started",
                "notes": [carry_note],
            }
        )

    weeks[args.to_week] = new_week
    save_data(data)

    print(
        f"已生成下周计划: {args.to_week} | 主题: {to_theme} | "
        f"继承目标: {len(carry_goals)}"
    )
    if not carry_goals:
        print("提示: 来源周已全部完成，建议手动添加更高优先级新目标。")


def format_goal_line(goal: Dict[str, Any]) -> str:
    status_map = {
        "not_started": "未开始",
        "in_progress": "进行中",
        "blocked": "阻塞",
        "done": "完成",
    }
    return (
        f"- #{goal['id']} [{status_map.get(goal['status'], goal['status'])}] "
        f"{goal['title']} | 指标: {goal['metric']} | 权重: {goal['weight']} | "
        f"进度: {goal['progress']}%"
    )


def cmd_report(args: argparse.Namespace) -> None:
    data = load_data()
    week = ensure_week(data, args.week_id)
    goals = week["goals"]
    score = calc_week_score(goals)

    print(f"===== 周报 {args.week_id} =====")
    print(f"主题: {week['theme']}")
    print(f"综合完成度: {score:.1f}%")
    print("")
    print("目标列表:")
    if not goals:
        print("- 暂无目标")
    else:
        for g in goals:
            print(format_goal_line(g))
            if g["notes"]:
                print("  记录:")
                for n in g["notes"][-3:]:
                    print(f"  - {n}")
    print("")
    print(f"复盘: {week.get('retrospective', '') or '（未填写）'}")
    print(f"下周重点: {week.get('next_week_focus', '') or '（未填写）'}")


def cmd_dashboard(_: argparse.Namespace) -> None:
    data = load_data()
    weeks = data.get("weeks", {})
    if not weeks:
        print("暂无周计划，请先执行 new-week。")
        return

    print("===== 学习进度总览 =====")
    for week_id in sorted(weeks.keys()):
        week = weeks[week_id]
        score = calc_week_score(week.get("goals", []))
        goals_count = len(week.get("goals", []))
        print(
            f"- {week_id} | 主题: {week.get('theme', '')} | 目标数: {goals_count} | 完成度: {score:.1f}%"
        )


def cmd_web(args: argparse.Namespace) -> None:
    from weekly_tracker_web import run_server

    run_server(host=args.host, port=args.port)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="每周目标制定与进度追踪工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new-week", help="创建新的一周计划")
    p_new.add_argument("week_id", help="周编号，例如 2026-W18")
    p_new.add_argument("theme", help="本周主题")
    p_new.set_defaults(func=cmd_new_week)

    p_add = sub.add_parser("add-goal", help="给周计划添加目标")
    p_add.add_argument("week_id")
    p_add.add_argument("title", help="目标名称")
    p_add.add_argument("--metric", default="可交付结果", help="验收指标")
    p_add.add_argument("--weight", type=int, default=20, help="目标权重(建议10-50)")
    p_add.set_defaults(func=cmd_add_goal)

    p_update = sub.add_parser("update", help="更新目标进度")
    p_update.add_argument("week_id")
    p_update.add_argument("goal_id", type=int, help="目标编号")
    p_update.add_argument("--progress", type=int, help="0-100")
    p_update.add_argument(
        "--status",
        choices=["not_started", "in_progress", "blocked", "done"],
        help="状态",
    )
    p_update.add_argument("--note", help="本次更新备注")
    p_update.set_defaults(func=cmd_update)

    p_retro = sub.add_parser("retro", help="填写周复盘")
    p_retro.add_argument("week_id")
    p_retro.add_argument("text", help="复盘内容")
    p_retro.set_defaults(func=cmd_retro)

    p_focus = sub.add_parser("next-focus", help="填写下周重点")
    p_focus.add_argument("week_id")
    p_focus.add_argument("text", help="下周重点")
    p_focus.set_defaults(func=cmd_next_focus)

    p_plan_next = sub.add_parser(
        "plan-next", help="基于本周进度自动生成下周计划"
    )
    p_plan_next.add_argument("from_week", help="来源周，例如 2026-W18")
    p_plan_next.add_argument("to_week", help="目标周，例如 2026-W19")
    p_plan_next.add_argument("--theme", help="下周主题，不填则自动生成")
    p_plan_next.add_argument(
        "--copy-all",
        action="store_true",
        help="复制来源周全部目标（默认仅复制未完成目标）",
    )
    p_plan_next.set_defaults(func=cmd_plan_next)

    p_web = sub.add_parser("web", help="启动可视化前端服务")
    p_web.add_argument("--host", default="127.0.0.1", help="监听地址，默认127.0.0.1")
    p_web.add_argument("--port", type=int, default=8765, help="监听端口，默认8765")
    p_web.set_defaults(func=cmd_web)

    p_report = sub.add_parser("report", help="输出某周周报")
    p_report.add_argument("week_id")
    p_report.set_defaults(func=cmd_report)

    p_dash = sub.add_parser("dashboard", help="输出所有周的总览")
    p_dash.set_defaults(func=cmd_dashboard)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as e:
        print(f"错误: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
