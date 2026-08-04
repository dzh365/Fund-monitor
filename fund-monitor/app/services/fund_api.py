"""
app/services/fund_api.py - 天天基金 API 调用服务
获取基金净值、名称等公开数据
"""

import re
import json
import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# 估值/实时数据
FUND_GZ_URL = "http://fundgz.1234567.com.cn/js/{code}.js"
# 历史净值
FUND_LSJZ_URL = "https://api.fund.eastmoney.com/f10/lsjz"
# 基金详情（获取名称）
FUND_DETAIL_URL = "https://fund.eastmoney.com/pingzhongdata/{code}.js"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://fund.eastmoney.com/",
}

TIMEOUT = 10
MAX_RETRIES = 3
RETRY_DELAY = 2


def _retry_get(url: str, params: dict = None, timeout: int = TIMEOUT) -> httpx.Response:
    """带重试的 GET 请求"""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url, params=params, headers=HEADERS)
                resp.raise_for_status()
                return resp
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
            last_exc = e
            logger.warning(f"请求 {url} 失败 (第{attempt + 1}次): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    raise last_exc


def validate_fund_code(code: str) -> bool:
    """校验基金代码：6位纯数字"""
    return bool(re.match(r'^\d{6}$', code))


def search_fund(fund_code: str) -> dict:
    """
    查询基金信息（名称 + 最新净值）
    优先使用历史净值 API（稳定可靠），估值 API 作为补充。

    返回:
    {
        "fund_code": "000001",
        "fund_name": "华夏成长混合",
        "nav": 1.2345,
        "nav_date": "2024-01-15",
        "change_pct": 0.12,
    }
    """
    if not validate_fund_code(fund_code):
        raise ValueError(f"基金代码格式无效: {fund_code}")

    # 优先：从历史净值接口获取最新数据（最可靠）
    try:
        result = _fetch_from_lsjz(fund_code)
        if result and result.get("nav"):
            # 尝试补充基金名称（lsjz 可能不含名称）
            if not result.get("fund_name"):
                name = _fetch_fund_name_from_gz(fund_code)
                if name:
                    result["fund_name"] = name
            return result
    except Exception as e:
        logger.warning(f"lsjz 接口获取基金 {fund_code} 失败: {e}，尝试估值接口")

    # 备用：估值接口
    gz_url = FUND_GZ_URL.format(code=fund_code)
    try:
        resp = _retry_get(gz_url)
        text = resp.text.strip()
        match = re.search(r'jsonpgz\((.*)\)', text)
        if not match:
            raise ValueError(f"基金 {fund_code} 估值数据格式异常")
        data = json.loads(match.group(1))
        return {
            "fund_code": fund_code,
            "fund_name": data.get("name", ""),
            "nav": float(data.get("dwjz", 0)),
            "nav_date": data.get("jzrq", ""),
            "change_pct": float(data.get("gszzl", 0) or 0),
        }
    except Exception as e:
        logger.error(f"获取基金 {fund_code} 全部失败: {e}")
        raise


def _fetch_from_lsjz(fund_code: str) -> dict:
    """从历史净值接口获取最新一条数据（主要数据源）"""
    params = {
        "fundCode": fund_code,
        "pageIndex": 1,
        "pageSize": 1,
        "startDate": "",
        "endDate": "",
    }
    resp = _retry_get(FUND_LSJZ_URL, params=params)
    data = resp.json()

    rows = data.get("Data", {}).get("LSJZList", [])
    if not rows:
        raise ValueError(f"基金 {fund_code} 无净值数据，代码可能无效")

    row = rows[0]
    fund_name = data.get("Data", {}).get("FundName", "") or ""
    return {
        "fund_code": fund_code,
        "fund_name": fund_name,
        "nav": float(row.get("DWJZ", 0)),
        "nav_date": row.get("FSRQ", ""),
        "change_pct": float(row.get("JZZZL", 0) or 0),
    }


def _fetch_fund_name_from_gz(fund_code: str) -> str:
    """从基金详情接口获取基金名称"""
    url = FUND_DETAIL_URL.format(code=fund_code)
    try:
        resp = _retry_get(url)
        match = re.search(r'fS_name\s*=\s*"([^"]+)"', resp.text)
        if match:
            return match.group(1)
    except Exception:
        pass
    return ""


def fetch_fund_name(fund_code: str) -> str:
    """仅获取基金名称"""
    try:
        info = search_fund(fund_code)
        return info.get("fund_name", "")
    except Exception:
        return ""


def batch_search(fund_codes: list[str]) -> dict:
    """
    批量查询基金净值

    返回: { "000001": {...}, "110011": {...}, }
    """
    results = {}
    for code in fund_codes:
        try:
            results[code] = search_fund(code)
        except Exception as e:
            logger.error(f"批量查询基金 {code} 失败: {e}")
            results[code] = None
    return results
