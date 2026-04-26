#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "weekly_tracker_data.json"
STATIC_DIR = BASE_DIR / "tracker_web"


def load_data() -> dict:
    if not DATA_FILE.exists():
        return {"weeks": {}}
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def calc_week_score(goals: list[dict]) -> float:
    if not goals:
        return 0.0
    total_weight = sum(int(g.get("weight", 0)) for g in goals)
    if total_weight <= 0:
        return 0.0
    weighted_sum = sum(
        (max(0, min(100, int(g.get("progress", 0)))) / 100.0) * int(g.get("weight", 0))
        for g in goals
    )
    return round((weighted_sum / total_weight) * 100.0, 1)


def is_goal_done(goal: dict) -> bool:
    return goal.get("status") == "done" or int(goal.get("progress", 0)) >= 100


class TrackerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/data":
            data = load_data()
            weeks = data.get("weeks", {})
            dashboard = []
            for week_id in sorted(weeks.keys()):
                week = weeks[week_id]
                dashboard.append(
                    {
                        "week_id": week_id,
                        "theme": week.get("theme", ""),
                        "goal_count": len(week.get("goals", [])),
                        "score": calc_week_score(week.get("goals", [])),
                    }
                )
            self._json(HTTPStatus.OK, {"ok": True, "data": data, "dashboard": dashboard})
            return
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/weeks":
                return self._create_week(payload)
            if path == "/api/goals":
                return self._add_goal(payload)
            if path == "/api/goals/update":
                return self._update_goal(payload)
            if path == "/api/weeks/notes":
                return self._update_week_notes(payload)
            if path == "/api/weeks/plan-next":
                return self._plan_next(payload)
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "接口不存在"})
        except ValueError as e:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(e)})
        except Exception:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": "服务内部错误"})

    def _create_week(self, payload: dict) -> None:
        week_id = str(payload.get("week_id", "")).strip()
        theme = str(payload.get("theme", "")).strip()
        if not week_id or not theme:
            raise ValueError("week_id 和 theme 不能为空")

        data = load_data()
        weeks = data.setdefault("weeks", {})
        if week_id in weeks:
            raise ValueError(f"周 {week_id} 已存在")

        weeks[week_id] = {
            "theme": theme,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "goals": [],
            "retrospective": "",
            "next_week_focus": "",
        }
        save_data(data)
        self._json(HTTPStatus.OK, {"ok": True})

    def _add_goal(self, payload: dict) -> None:
        week_id = str(payload.get("week_id", "")).strip()
        title = str(payload.get("title", "")).strip()
        metric = str(payload.get("metric", "可交付结果")).strip()
        weight = int(payload.get("weight", 20))
        if not week_id or not title:
            raise ValueError("week_id 和 title 不能为空")
        if weight <= 0:
            raise ValueError("weight 必须大于 0")

        data = load_data()
        weeks = data.setdefault("weeks", {})
        if week_id not in weeks:
            raise ValueError(f"周 {week_id} 不存在")
        goals = weeks[week_id].setdefault("goals", [])
        goal_id = len(goals) + 1
        goals.append(
            {
                "id": goal_id,
                "title": title,
                "metric": metric,
                "weight": weight,
                "progress": 0,
                "status": "not_started",
                "notes": [],
            }
        )
        save_data(data)
        self._json(HTTPStatus.OK, {"ok": True})

    def _update_goal(self, payload: dict) -> None:
        week_id = str(payload.get("week_id", "")).strip()
        goal_id = int(payload.get("goal_id", 0))
        progress = payload.get("progress")
        status = payload.get("status")
        note = str(payload.get("note", "")).strip()

        data = load_data()
        weeks = data.setdefault("weeks", {})
        if week_id not in weeks:
            raise ValueError(f"周 {week_id} 不存在")
        goals = weeks[week_id].setdefault("goals", [])
        if goal_id < 1 or goal_id > len(goals):
            raise ValueError("goal_id 无效")
        goal = goals[goal_id - 1]

        if progress is not None:
            p = int(progress)
            if p < 0 or p > 100:
                raise ValueError("progress 必须在 0-100")
            goal["progress"] = p
        if status is not None:
            if status not in {"not_started", "in_progress", "blocked", "done"}:
                raise ValueError("status 非法")
            goal["status"] = status
        if note:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            goal.setdefault("notes", []).append(f"[{stamp}] {note}")

        save_data(data)
        self._json(HTTPStatus.OK, {"ok": True})

    def _update_week_notes(self, payload: dict) -> None:
        week_id = str(payload.get("week_id", "")).strip()
        retrospective = payload.get("retrospective")
        next_week_focus = payload.get("next_week_focus")

        data = load_data()
        weeks = data.setdefault("weeks", {})
        if week_id not in weeks:
            raise ValueError(f"周 {week_id} 不存在")
        week = weeks[week_id]

        if retrospective is not None:
            week["retrospective"] = str(retrospective)
        if next_week_focus is not None:
            week["next_week_focus"] = str(next_week_focus)

        save_data(data)
        self._json(HTTPStatus.OK, {"ok": True})

    def _plan_next(self, payload: dict) -> None:
        from_week = str(payload.get("from_week", "")).strip()
        to_week = str(payload.get("to_week", "")).strip()
        theme = str(payload.get("theme", "")).strip()
        copy_all = bool(payload.get("copy_all", False))
        if not from_week or not to_week:
            raise ValueError("from_week 和 to_week 不能为空")

        data = load_data()
        weeks = data.setdefault("weeks", {})
        if from_week not in weeks:
            raise ValueError(f"来源周 {from_week} 不存在")
        if to_week in weeks:
            raise ValueError(f"目标周 {to_week} 已存在")

        source = weeks[from_week]
        from_goals = source.get("goals", [])
        carry_goals = [g for g in from_goals if copy_all or (not is_goal_done(g))]

        weeks[to_week] = {
            "theme": theme or f"{source.get('theme', '学习计划')}（滚动）",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "goals": [
                {
                    "id": i + 1,
                    "title": g.get("title", "未命名目标"),
                    "metric": g.get("metric", "可交付结果"),
                    "weight": int(g.get("weight", 20)),
                    "progress": 0,
                    "status": "not_started",
                    "notes": [
                        f"从 {from_week} 延续: 原进度 {int(g.get('progress', 0))}%, 原状态 {g.get('status', 'unknown')}"
                    ],
                }
                for i, g in enumerate(carry_goals)
            ],
            "retrospective": "",
            "next_week_focus": "",
        }
        save_data(data)
        self._json(HTTPStatus.OK, {"ok": True, "carry_count": len(carry_goals)})


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    if not STATIC_DIR.exists():
        raise SystemExit(f"静态目录不存在: {STATIC_DIR}")
    server = ThreadingHTTPServer((host, port), TrackerHandler)
    print(f"Weekly Tracker Web 已启动: http://{host}:{port}")
    print("按 Ctrl+C 停止服务")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")


if __name__ == "__main__":
    run_server()
