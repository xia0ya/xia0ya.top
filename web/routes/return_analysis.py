"""退货分析API路由"""
import os
import json
import shutil
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/return", tags=["退货分析"])
templates = Jinja2Templates(directory="web/templates")

# 数据目录
DATA_DIR = Path("/var/www/GetReview/return_data")
ALL_ORDERS_DIR = Path("/var/www/GetReview/return_data/all_orders")

# Kimi API配置
KIMI_API_KEY = "sk-zLm3bR4BsOjy6x5Qog6z8zMJK1mQRIfBivvf0JxsBYEMIu3F"
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
ALL_ORDERS_DIR.mkdir(parents=True, exist_ok=True)


def get_versions():
    """获取所有版本"""
    versions = []
    if DATA_DIR.exists():
        for v in DATA_DIR.iterdir():
            if v.is_dir():
                # 检查版本目录是否有有效数据
                result_file = v / "analysis_result.json"
                csv_file = v / "退货_退款订单.csv"
                if result_file.exists() or csv_file.exists():
                    versions.append({
                        'name': v.name,
                        'date': v.name,
                        'has_result': result_file.exists()
                    })
    return sorted(versions, key=lambda x: x['date'], reverse=True)


@router.get("/")
async def index(request: Request):
    """主页"""
    return templates.TemplateResponse("return_analysis.html", {"request": request})


@router.get("/api/versions")
async def list_versions():
    """获取版本列表"""
    versions = get_versions()
    return JSONResponse(content={'versions': versions})


@router.post("/api/upload")
async def upload_data(
    version: str = Form(...),
    return_file: UploadFile = File(...),
    all_orders_file: UploadFile = File(None)
):
    """上传数据文件"""
    version_dir = DATA_DIR / version
    version_dir.mkdir(parents=True, exist_ok=True)

    errors = []

    # 保存退货数据文件
    if return_file.filename.endswith('.csv'):
        return_path = version_dir / "退货_退款订单.csv"
    elif return_file.filename.endswith(('.xlsx', '.xls')):
        return_path = version_dir / "退货_退款订单.xlsx"
    else:
        return_path = version_dir / return_file.filename

    try:
        with open(return_path, "wb") as f:
            shutil.copyfileobj(return_file.file, f)
    except Exception as e:
        errors.append(f"退货数据上传失败: {str(e)}")

    # 保存全部订单文件（可选）
    if all_orders_file and all_orders_file.filename and all_orders_file.size > 0:
        all_orders_path = ALL_ORDERS_DIR / all_orders_file.filename
        try:
            with open(all_orders_path, "wb") as f:
                shutil.copyfileobj(all_orders_file.file, f)
        except Exception as e:
            errors.append(f"全部订单上传失败: {str(e)}")

    if errors:
        return JSONResponse(content={'success': False, 'errors': errors}, status_code=400)

    return JSONResponse(content={
        'success': True,
        'message': f'文件上传成功，版本: {version}',
        'version': version
    })


@router.post("/api/analyze")
async def run_analysis(version: str = Form(...)):
    """触发分析"""
    version_dir = DATA_DIR / version
    return_csv = version_dir / "退货_退款订单.csv"
    return_xlsx = version_dir / "退货_退款订单.xlsx"

    # 确定使用哪个文件
    if return_csv.exists():
        data_file = str(return_csv)
    elif return_xlsx.exists():
        data_file = str(return_xlsx)
    else:
        return JSONResponse(
            content={'success': False, 'error': '数据文件不存在，请先上传'},
            status_code=400
        )

    # 查找全部订单文件
    all_orders_file = None
    all_orders_files = list(ALL_ORDERS_DIR.glob("*.xlsx"))
    if all_orders_files:
        all_orders_file = str(all_orders_files[0])

    # 运行分析脚本
    script_path = Path("/var/www/GetReview/return_analyzer.py")
    if not script_path.exists():
        return JSONResponse(
            content={'success': False, 'error': '分析脚本不存在'},
            status_code=500
        )

    cmd = ["python3", str(script_path), version, str(DATA_DIR)]
    if all_orders_file:
        cmd.append(all_orders_file)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            return JSONResponse(
                content={'success': False, 'error': result.stderr},
                status_code=500
            )
    except subprocess.TimeoutExpired:
        return JSONResponse(
            content={'success': False, 'error': '分析超时'},
            status_code=500
        )
    except Exception as e:
        return JSONResponse(
            content={'success': False, 'error': str(e)},
            status_code=500
        )

    return JSONResponse(content={
        'success': True,
        'message': '分析完成',
        'version': version
    })


@router.get("/api/data/{version}")
async def get_data(version: str):
    """获取分析结果"""
    result_file = DATA_DIR / version / "analysis_result.json"
    if not result_file.exists():
        return JSONResponse(
            content={'success': False, 'error': '分析结果不存在'},
            status_code=404
        )

    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return JSONResponse(content=data)


@router.get("/api/download/{version}/excel")
async def download_excel(version: str):
    """下载Excel文件"""
    excel_file = DATA_DIR / version / "退货分析结果.xlsx"
    if not excel_file.exists():
        return JSONResponse(
            content={'success': False, 'error': 'Excel文件不存在'},
            status_code=404
        )
    return FileResponse(
        excel_file,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=f'退货分析_{version}.xlsx'
    )


@router.delete("/api/version/{version}")
async def delete_version(version: str):
    """删除版本"""
    version_dir = DATA_DIR / version
    if not version_dir.exists():
        return JSONResponse(
            content={'success': False, 'error': '版本不存在'},
            status_code=404
        )

    shutil.rmtree(version_dir)
    return JSONResponse(content={'success': True, 'message': f'版本 {version} 已删除'})


@router.post("/api/insights")
async def get_insights(version: str = Form(...)):
    """获取AI洞察分析"""
    result_file = DATA_DIR / version / "analysis_result.json"
    if not result_file.exists():
        return JSONResponse(
            content={'success': False, 'error': '分析结果不存在'},
            status_code=404
        )

    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 构建分析提示词
    overview = data.get('overview', {})
    by_reason = data.get('by_reason', [])
    by_type = data.get('by_type', [])
    top_skus = data.get('top_skus', [])[:5]  # Top 5 SKU
    return_rate = data.get('return_rate', {})

    # 构建月统计摘要
    monthly = data.get('monthly', [])
    if monthly:
        latest_month = monthly[-1] if len(monthly) >= 1 else {}
        prev_month = monthly[-2] if len(monthly) >= 2 else {}
        month_change = ""
        if latest_month and prev_month:
            change = latest_month.get('退货订单数', 0) - prev_month.get('退货订单数', 0)
            direction = "上升" if change > 0 else "下降"
            month_change = f"较上月{direction}了{abs(change)}单"
    else:
        latest_month = {}
        month_change = "数据不足"

    # 原因Top3
    top3_reasons = by_reason[:3] if len(by_reason) >= 3 else by_reason
    reason_summary = "、".join([f"{r['原因中文']}({r['订单数']}单)" for r in top3_reasons]) if top3_reasons else "无数据"

    # 计算退款率
    refund_only = overview.get('仅退款订单数', 0)
    return_refund = overview.get('退货退款订单数', 0)
    total = overview.get('总退货订单数', 1)
    refund_ratio = (refund_only / total * 100) if total > 0 else 0
    return_ratio = (return_refund / total * 100) if total > 0 else 0

    prompt = f"""你是一位专业的电商退货分析专家。请基于以下退货数据，给出简洁有力的分析洞察：

【总体概况】
- 总退货订单: {overview.get('总退货订单数', 0)}单
- 总退货金额: ${overview.get('总退货金额', 0):.2f}
- 平均退货金额: ${overview.get('平均退货金额', 0):.2f}
- 趋势: {month_change}

【退货类型分布】
- 仅退款: {refund_only}单 ({refund_ratio:.1f}%)
- 退货退款: {return_refund}单 ({return_ratio:.1f}%)

【退货原因Top3】
{reason_summary}

【问题SKU Top5】
{', '.join([f"{s['SKU']}({s['退货金额']:.2f})" for s in top_skus]) if top_skus else '无数据'}

请从以下维度给出分析（用中文回答，每点简洁有力，总字数控制在300字以内）：
1. **健康度诊断**: 退货率是否正常，问题严重程度
2. **核心问题**: 最需要关注的产品和原因
3. **趋势预警**: 近期退货趋势是否异常
4. **行动建议**: 2-3条具体可执行的改进建议

请直接输出分析内容，不要有"以下是分析"之类的废话，用emoji增加可读性。"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KIMI_API_KEY}"
        }
        payload = {
            "model": "moonshot-v1-8k",
            "messages": [
                {"role": "system", "content": "你是一位专业的电商退货分析专家，擅长从数据中发现问题并给出可执行的建议。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        resp = requests.post(KIMI_API_URL, headers=headers, json=payload, timeout=30)
        result = resp.json()

        if 'choices' in result and len(result['choices']) > 0:
            insight = result['choices'][0]['message']['content']
            return JSONResponse(content={'success': True, 'insight': insight})
        else:
            return JSONResponse(content={'success': False, 'error': 'Kimi API返回格式错误'})
    except Exception as e:
        return JSONResponse(content={'success': False, 'error': str(e)})
