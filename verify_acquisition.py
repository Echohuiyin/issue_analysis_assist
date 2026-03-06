"""
内核案例获取模块 - 综合验证脚本
覆盖第2-5层验证：组件级、集成、数据库、网络
"""
import os
import sys
import io
import traceback
from unittest.mock import patch, MagicMock

# 修复 Windows GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

# 先在非 Django 环境下测试部分组件
from cases.acquisition.fetchers import HTTPFetcher, APIFetcher, RSSFetcher, BaseFetcher
from cases.acquisition.parsers import BlogParser, ForumParser, BaseParser
from cases.acquisition.validators import CaseValidator

# ============================================================
# 测试框架
# ============================================================
results = {"passed": 0, "failed": 0, "errors": []}

def test(name):
    """测试装饰器"""
    def decorator(func):
        def wrapper():
            try:
                func()
                results["passed"] += 1
                print(f"  ✅ {name}")
            except AssertionError as e:
                results["failed"] += 1
                results["errors"].append((name, str(e)))
                print(f"  ❌ {name}: {e}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append((name, traceback.format_exc()))
                print(f"  ❌ {name}: {type(e).__name__}: {e}")
        return wrapper
    return decorator


# ============================================================
# 第2层：组件级功能验证
# ============================================================
print("\n" + "=" * 60)
print("第2层：组件级功能验证")
print("=" * 60)

# --- 2.1 Fetcher 验证 ---
print("\n--- 2.1 Fetcher 验证 ---")

@test("HTTPFetcher: 自定义 timeout 生效")
def test_http_fetcher_custom_timeout():
    fetcher = HTTPFetcher(timeout=30)
    assert fetcher.timeout == 30, f"Expected 30, got {fetcher.timeout}"
    with patch('requests.get') as mock_get:
        mock_get.return_value = MagicMock(text="ok")
        fetcher.fetch("http://test.com")
        mock_get.assert_called_once_with("http://test.com", timeout=30)
test_http_fetcher_custom_timeout()

@test("HTTPFetcher: 默认 timeout 为 10")
def test_http_fetcher_default_timeout():
    fetcher = HTTPFetcher()
    assert fetcher.timeout == 10
test_http_fetcher_default_timeout()

@test("APIFetcher: mock 返回 JSON 数据")
def test_api_fetcher_json():
    fetcher = APIFetcher()
    with patch('requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"key": "value"}
        mock_get.return_value = mock_resp
        result = fetcher.fetch("http://api.test.com", params={"q": "test"}, headers={"Auth": "token"})
        assert result == {"key": "value"}, f"Expected dict, got {result}"
        mock_get.assert_called_once_with("http://api.test.com", params={"q": "test"}, headers={"Auth": "token"}, timeout=10)
test_api_fetcher_json()

@test("APIFetcher: 网络异常返回 None")
def test_api_fetcher_error():
    fetcher = APIFetcher()
    with patch('requests.get', side_effect=Exception("API error")):
        result = fetcher.fetch("http://api.test.com")
        assert result is None
test_api_fetcher_error()

@test("RSSFetcher: mock 返回 XML 数据")
def test_rss_fetcher():
    fetcher = RSSFetcher()
    with patch('requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = "<rss><channel><item>test</item></channel></rss>"
        mock_get.return_value = mock_resp
        result = fetcher.fetch("http://rss.test.com")
        assert result == "<rss><channel><item>test</item></channel></rss>"
test_rss_fetcher()

@test("RSSFetcher: 网络异常返回 None")
def test_rss_fetcher_error():
    fetcher = RSSFetcher()
    with patch('requests.get', side_effect=Exception("RSS error")):
        result = fetcher.fetch("http://rss.test.com")
        assert result is None
test_rss_fetcher_error()

# --- 2.2 Parser 验证 ---
print("\n--- 2.2 Parser 验证 ---")

@test("BlogParser: 非空内容返回结构化数据")
def test_blog_parser_valid():
    parser = BlogParser()
    result = parser.parse("<html>some content</html>")
    assert result is not None
    assert "title" in result
    assert "phenomenon" in result
    assert "environment" in result
    assert "root_cause" in result
    assert "troubleshooting_steps" in result
    assert "solution" in result
    assert isinstance(result["troubleshooting_steps"], list)
test_blog_parser_valid()

@test("BlogParser: None 输入返回 None")
def test_blog_parser_none():
    parser = BlogParser()
    result = parser.parse(None)
    assert result is None
test_blog_parser_none()

@test("BlogParser: 空字符串返回 None")
def test_blog_parser_empty():
    parser = BlogParser()
    result = parser.parse("")
    assert result is None
test_blog_parser_empty()

@test("ForumParser: 非空内容返回结构化数据")
def test_forum_parser_valid():
    parser = ForumParser()
    result = parser.parse("<html>forum post</html>")
    assert result is not None
    assert "title" in result
    assert "root_cause" in result
test_forum_parser_valid()

@test("ForumParser: None 输入返回 None")
def test_forum_parser_none():
    parser = ForumParser()
    result = parser.parse(None)
    assert result is None
test_forum_parser_none()

@test("ForumParser: 空字符串返回 None")
def test_forum_parser_empty():
    parser = ForumParser()
    result = parser.parse("")
    assert result is None
test_forum_parser_empty()

print("\n  ⚠️  已知限制: BlogParser/ForumParser 为硬编码模拟实现，未做真正 HTML 解析")

# --- 2.3 Validator 验证 ---
print("\n--- 2.3 Validator 验证 ---")

VALID_CASE = {
    "title": "Test Kernel Case",
    "phenomenon": "System hang",
    "environment": "Linux 5.4.0, x86_64",
    "root_cause": "Null pointer dereference in driver",
    "troubleshooting_steps": ["Step 1", "Step 2"],
    "solution": "Apply driver patch to fix issue",
}

@test("Validator: 完整合法数据通过验证")
def test_validator_valid():
    v = CaseValidator()
    result = v.validate(VALID_CASE)
    assert result["is_valid"] is True
    assert result["errors"] == []
test_validator_valid()

@test("Validator: 缺少 title 字段")
def test_validator_missing_title():
    v = CaseValidator()
    data = {k: v for k, v in VALID_CASE.items() if k != "title"}
    result = v.validate(data)
    assert result["is_valid"] is False
    assert any("title" in e for e in result["errors"])
test_validator_missing_title()

@test("Validator: 缺少 phenomenon 字段")
def test_validator_missing_phenomenon():
    v = CaseValidator()
    data = {k: v for k, v in VALID_CASE.items() if k != "phenomenon"}
    result = v.validate(data)
    assert result["is_valid"] is False
    assert any("phenomenon" in e for e in result["errors"])
test_validator_missing_phenomenon()

@test("Validator: 缺少 root_cause 字段")
def test_validator_missing_root_cause():
    v = CaseValidator()
    data = {k: v for k, v in VALID_CASE.items() if k != "root_cause"}
    result = v.validate(data)
    assert result["is_valid"] is False
    assert any("root_cause" in e for e in result["errors"])
test_validator_missing_root_cause()

@test("Validator: troubleshooting_steps 非 list 类型")
def test_validator_steps_not_list():
    v = CaseValidator()
    data = {**VALID_CASE, "troubleshooting_steps": "just a string"}
    result = v.validate(data)
    assert result["is_valid"] is False
    assert any("list" in e for e in result["errors"])
test_validator_steps_not_list()

@test("Validator: root_cause 长度 < 10")
def test_validator_short_root_cause():
    v = CaseValidator()
    data = {**VALID_CASE, "root_cause": "short"}
    result = v.validate(data)
    assert result["is_valid"] is False
    assert any("root_cause" in e and "10" in e for e in result["errors"])
test_validator_short_root_cause()

@test("Validator: solution 长度 < 10")
def test_validator_short_solution():
    v = CaseValidator()
    data = {**VALID_CASE, "solution": "fix it"}
    result = v.validate(data)
    assert result["is_valid"] is False
    assert any("solution" in e and "10" in e for e in result["errors"])
test_validator_short_solution()

@test("Validator: 空字典 → 所有必填字段报错")
def test_validator_empty_dict():
    v = CaseValidator()
    result = v.validate({})
    assert result["is_valid"] is False
    assert len(result["errors"]) >= 6  # 6 个必填字段
test_validator_empty_dict()

@test("Validator: root_cause 恰好 10 字符 → 通过")
def test_validator_boundary_root_cause():
    v = CaseValidator()
    data = {**VALID_CASE, "root_cause": "1234567890"}  # exactly 10 chars
    result = v.validate(data)
    # root_cause 长度检查应该通过（>= 10 不是 > 10）
    root_cause_errors = [e for e in result["errors"] if "root_cause" in e and "10" in e]
    assert len(root_cause_errors) == 0, f"root_cause=10 chars should pass, got errors: {root_cause_errors}"
test_validator_boundary_root_cause()

# 2.4 Storage 空数据验证移至 Django 初始化后（见第4层）


# ============================================================
# 第3层：端到端集成验证（mock 网络）
# ============================================================
print("\n" + "=" * 60)
print("第3层：端到端集成验证")
print("=" * 60)

# 需要 Django 环境来导入 main.py
import django
django.setup()

from cases.acquisition.main import CaseAcquisition

print("\n--- 3.1 acquire_case 流程 ---")

@test("acquire_case: 完整流程（mock fetch 成功）")
def test_acquire_case_success():
    ca = CaseAcquisition()
    with patch.object(ca.fetcher, 'fetch', return_value="<html>content</html>"):
        with patch.object(ca.storage, 'store', return_value={"success": True, "case_id": "TEST-001", "message": "ok"}):
            result = ca.acquire_case("http://example.com/case1", "blog")
            assert result["success"] is True
            assert result["case_id"] == "TEST-001"
test_acquire_case_success()

@test("acquire_case: fetch 返回 None → 失败")
def test_acquire_case_fetch_fail():
    ca = CaseAcquisition()
    with patch.object(ca.fetcher, 'fetch', return_value=None):
        result = ca.acquire_case("http://example.com/bad")
        assert result["success"] is False
        assert "Failed to fetch" in result["message"]
test_acquire_case_fetch_fail()

@test("acquire_case: 未知 content_type → 使用默认 BlogParser")
def test_acquire_case_unknown_type():
    ca = CaseAcquisition()
    with patch.object(ca.fetcher, 'fetch', return_value="<html>content</html>"):
        with patch.object(ca.storage, 'store', return_value={"success": True, "case_id": "TEST-002", "message": "ok"}):
            result = ca.acquire_case("http://example.com/case2", "unknown_type")
            assert result["success"] is True  # 应使用默认 BlogParser
test_acquire_case_unknown_type()

print("\n--- 3.2 acquire_cases 批量流程 ---")

@test("acquire_cases: 多个 source 各自返回结果")
def test_acquire_cases_multiple():
    ca = CaseAcquisition()
    sources = [
        {"url": "http://example.com/1", "content_type": "blog"},
        {"url": "http://example.com/2", "content_type": "forum"},
    ]
    with patch.object(ca.fetcher, 'fetch', return_value="<html>content</html>"):
        with patch.object(ca.storage, 'store', return_value={"success": True, "case_id": "TEST", "message": "ok"}):
            results_list = ca.acquire_cases(sources)
            assert len(results_list) == 2
            assert all(r["success"] for r in results_list)
            assert all("source_url" in r for r in results_list)
test_acquire_cases_multiple()

@test("acquire_cases: 缺少 url 的 source → 返回失败")
def test_acquire_cases_no_url():
    ca = CaseAcquisition()
    sources = [{"content_type": "blog"}]  # 没有 url
    results_list = ca.acquire_cases(sources)
    assert len(results_list) == 1
    assert results_list[0]["success"] is False
    assert "No URL" in results_list[0]["message"]
test_acquire_cases_no_url()

@test("acquire_cases: 混合有效/无效 source → 各自独立处理")
def test_acquire_cases_mixed():
    ca = CaseAcquisition()
    sources = [
        {"url": "http://example.com/good", "content_type": "blog"},
        {"content_type": "forum"},  # 无 url
    ]
    with patch.object(ca.fetcher, 'fetch', return_value="<html>content</html>"):
        with patch.object(ca.storage, 'store', return_value={"success": True, "case_id": "TEST", "message": "ok"}):
            results_list = ca.acquire_cases(sources)
            assert len(results_list) == 2
            assert results_list[0]["success"] is True
            assert results_list[1]["success"] is False
test_acquire_cases_mixed()


# ============================================================
# 第4层：Django 数据库集成验证
# ============================================================
print("\n" + "=" * 60)
print("第4层：Django 数据库集成验证")
print("=" * 60)

from cases.acquisition.storage import CaseStorage
from cases.models import KernelCase

print("\n--- 2.4 Storage 空数据验证 ---")

@test("Storage: 传入 None → 返回失败")
def test_storage_none():
    s = CaseStorage()
    result = s.store(None)
    assert result["success"] is False
test_storage_none()

@test("Storage: 传入空字典 → 返回失败")
def test_storage_empty():
    s = CaseStorage()
    result = s.store({})
    assert result["success"] is False
test_storage_empty()

@test("Storage+DB: 存储新案例并查询确认")
def test_storage_db_new_case():
    storage = CaseStorage()
    case_data = {
        "case_id": "VERIFY-TEST-001",
        "title": "Verification Test Case",
        "phenomenon": "Test symptom for verification",
        "environment": "Linux 5.15.0, x86_64, Ubuntu 22.04",
        "root_cause": "Test root cause for verification purpose",
        "solution": "Test solution for verification purpose",
        "troubleshooting_steps": ["Step 1", "Step 2"],
    }
    result = storage.store(case_data)
    assert result["success"] is True, f"Store failed: {result.get('message')}"
    assert result["case_id"] == "VERIFY-TEST-001"

    # 查询数据库确认
    case = KernelCase.objects.filter(case_id="VERIFY-TEST-001").first()
    assert case is not None, "Case not found in database"
    assert case.title == "Verification Test Case"
    assert case.kernel_version == "5.15.0"  # 从 environment 提取
    assert "Test symptom" in case.symptoms

    # 清理
    case.delete()
test_storage_db_new_case()

@test("Storage+DB: 重复 case_id 拒绝存储")
def test_storage_db_duplicate():
    storage = CaseStorage()
    case_data = {
        "case_id": "VERIFY-DUP-001",
        "title": "Duplicate Test",
        "phenomenon": "Test symptom",
        "environment": "Linux 5.4.0",
        "root_cause": "Test root cause for dup test",
        "solution": "Test solution for dup test",
        "troubleshooting_steps": ["Step 1"],
    }
    # 第一次存储
    result1 = storage.store(case_data)
    assert result1["success"] is True

    # 第二次存储同一 case_id
    result2 = storage.store(case_data)
    assert result2["success"] is False
    assert "already exists" in result2["message"]

    # 清理
    KernelCase.objects.filter(case_id="VERIFY-DUP-001").delete()
test_storage_db_duplicate()

@test("Storage+DB: 字段映射验证（phenomenon→symptoms, environment→kernel_version）")
def test_storage_db_field_mapping():
    storage = CaseStorage()
    case_data = {
        "case_id": "VERIFY-MAP-001",
        "title": "Field Mapping Test",
        "phenomenon": "Kernel panic on boot",
        "environment": "Linux 6.1.0, aarch64, Debian 12",
        "root_cause": "Driver initialization failure in early boot",
        "solution": "Update driver to latest version from upstream",
        "troubleshooting_steps": ["Check dmesg", "Identify driver"],
        "severity": "High",
    }
    result = storage.store(case_data)
    assert result["success"] is True

    case = KernelCase.objects.get(case_id="VERIFY-MAP-001")
    assert case.symptoms == "Kernel panic on boot"  # phenomenon → symptoms
    assert case.kernel_version == "6.1.0"  # 从 environment 提取
    assert case.severity == "High"
    assert "Kernel panic on boot" in case.description  # description 包含 phenomenon

    # 清理
    case.delete()
test_storage_db_field_mapping()


# ============================================================
# 第5层：真实网络请求验证
# ============================================================
print("\n" + "=" * 60)
print("第5层：真实网络请求验证")
print("=" * 60)

@test("HTTPFetcher: 真实 HTTP 请求（httpbin.org）")
def test_http_fetcher_real():
    fetcher = HTTPFetcher(timeout=10)
    result = fetcher.fetch("https://httpbin.org/html")
    assert result is not None, "Failed to fetch from httpbin.org"
    assert "Herman Melville" in result or "<html" in result.lower(), f"Unexpected content: {result[:100]}"
test_http_fetcher_real()

@test("HTTPFetcher: 超时机制验证（极短 timeout）")
def test_http_fetcher_timeout():
    fetcher = HTTPFetcher(timeout=0.001)  # 极短超时
    result = fetcher.fetch("https://httpbin.org/delay/5")  # 延迟 5 秒的端点
    assert result is None, "Should have timed out but got result"
test_http_fetcher_timeout()

@test("HTTPFetcher: 不可达 URL 返回 None")
def test_http_fetcher_unreachable():
    fetcher = HTTPFetcher(timeout=3)
    result = fetcher.fetch("http://192.0.2.1/nonexistent")  # RFC 5737 测试地址
    assert result is None
test_http_fetcher_unreachable()


# ============================================================
# 汇总结果
# ============================================================
print("\n" + "=" * 60)
print("验证结果汇总")
print("=" * 60)
total = results["passed"] + results["failed"]
print(f"\n总计: {total} 项测试")
print(f"通过: {results['passed']} ✅")
print(f"失败: {results['failed']} ❌")

if results["errors"]:
    print("\n失败详情:")
    for name, err in results["errors"]:
        print(f"  - {name}: {err[:200]}")

print("\n已知限制:")
print("  1. BlogParser/ForumParser 为硬编码模拟实现，不做真正 HTML 解析")
print("  2. APIFetcher.fetch 签名与基类 BaseFetcher.fetch 不一致（额外参数 params, headers）")
print("  3. requirements.txt 已被删除（git status: D requirements.txt）")

print(f"\n最终结论: {'✅ 全部通过' if results['failed'] == 0 else '❌ 存在失败项'}")
