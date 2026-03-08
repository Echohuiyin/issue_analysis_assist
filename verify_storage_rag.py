#!/usr/bin/env python3
"""
PostgreSQL 存储 + 本地 RAG 向量库联调验证脚本

验证项：
1. 案例写入（Create）
2. 案例读取（Read）
3. 案例更新（Update）
4. 案例删除（Delete）
5. 本地向量库 upsert / search / delete
"""

import os
import sys
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kernel_cases.settings")

import django  # noqa: E402

django.setup()

from cases.models import KernelCase  # noqa: E402
from cases.acquisition.storage import CaseStorage  # noqa: E402
from cases.rag import get_local_vector_store  # noqa: E402


def run_crud_and_rag_test() -> int:
    print("=== PostgreSQL + RAG 联调验证 ===")
    using_pg = os.getenv("USE_POSTGRES", "0") == "1"
    print(f"数据库模式: {'PostgreSQL' if using_pg else 'SQLite(当前)'}")

    storage = CaseStorage()
    vector_store = get_local_vector_store()

    case_id = f"INT-{uuid.uuid4().hex[:8].upper()}"
    case_data = {
        "case_id": case_id,
        "title": "Kernel panic in probe path due to null pointer",
        "module": "driver",
        "phenomenon": "系统启动阶段触发 kernel panic，日志显示 NULL pointer dereference 与 Call Trace。",
        "environment": "Linux 5.10.0 x86_64",
        "key_logs": "[123.456] BUG: unable to handle kernel NULL pointer dereference\nCall Trace: driver_probe+0x56/0x100",
        "analysis_process": "先收集 dmesg，再按调用栈定位到 driver_probe，代码审查确认未做空指针检查。",
        "problem_analysis": "按日志->调用栈->代码审查三步定位。",
        "related_code": "driver_probe(), driver_init(), devm_kzalloc()",
        "root_cause": "probe 函数中直接访问未初始化指针。",
        "solution": "增加 NULL 检查并补充错误路径资源释放。",
        "fix_code": "if (!dev || !dev->private_data) return -EINVAL;",
        "troubleshooting_steps": ["收集日志", "解析调用栈", "修复并回归测试"],
        "source": "integration_test",
        "source_id": case_id,
        "reference_url": "https://example.com/kernel-case",
    }

    # Create
    create_result = storage.store(case_data)
    if not create_result.get("success"):
        print(f"[FAIL] Create 失败: {create_result}")
        return 1
    print(f"[OK] Create 成功: {create_result.get('case_id')}")

    # Read
    case = KernelCase.objects.filter(case_id=case_id).first()
    if not case:
        print("[FAIL] Read 失败: 数据库未查到记录")
        return 1
    print(f"[OK] Read 成功: title={case.title}")

    # Update
    case.solution = "修复 probe 空指针并新增回归测试用例。"
    case.save()
    refreshed = KernelCase.objects.get(case_id=case_id)
    if "回归测试" not in refreshed.solution:
        print("[FAIL] Update 失败")
        return 1
    print("[OK] Update 成功")

    # RAG search
    search_results = vector_store.search("kernel panic null pointer driver probe", top_k=3)
    matched = any(item.get("case_id") == case_id for item in search_results)
    if not matched:
        print(f"[FAIL] RAG Search 失败: {search_results}")
        return 1
    print(f"[OK] RAG Search 成功: top_k={len(search_results)}")

    # Delete
    vector_store.delete_case(case_id)
    deleted, _ = KernelCase.objects.filter(case_id=case_id).delete()
    if deleted <= 0:
        print("[FAIL] Delete 失败")
        return 1
    print("[OK] Delete 成功")

    print("[OK] CRUD + RAG 联调全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_crud_and_rag_test())
