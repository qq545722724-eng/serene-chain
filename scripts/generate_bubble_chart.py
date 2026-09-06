#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产业链气泡图生成器
=================
基于 plotly 生成交互式产业链气泡图
X轴 = 壁垒高度, Y轴 = 利润水平, 气泡大小 = 增长速度
"""

import argparse
import json
import sys
import os
from pathlib import Path

try:
    import plotly.graph_objects as go
except ImportError:
    print("正在安装 plotly ...")
    os.system(f"{sys.executable} -m pip install plotly -q")
    import plotly.graph_objects as go


# 颜色映射：上/中/下游
TIER_COLORS = {
    "上游": "#E74C3C",   # 红色
    "中游": "#3498DB",   # 蓝色
    "下游": "#2ECC71",   # 绿色
    "upstream": "#E74C3C",
    "midstream": "#3498DB",
    "downstream": "#2ECC71",
}


def parse_args():
    parser = argparse.ArgumentParser(description="产业链气泡图生成器")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--data", type=str, help="JSON格式数据字符串")
    group.add_argument("--data-file", type=str, help="JSON数据文件路径")
    parser.add_argument("--output", type=str, default=None, help="输出HTML文件路径")
    return parser.parse_args()


def load_data(args):
    """加载数据"""
    if args.data:
        data = json.loads(args.data)
    else:
        with open(args.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data


def generate_bubble_chart(data, output_path=None):
    """生成气泡图"""
    industry = data.get("industry", "产业链")
    segments = data.get("segments", [])

    if not segments:
        print("错误：未找到环节数据")
        sys.exit(1)

    # 准备数据
    names = []
    x_vals = []  # 壁垒高度
    y_vals = []  # 利润水平
    sizes = []   # 增长速度 → 气泡大小
    colors = []
    hover_texts = []
    tier_labels = []

    for seg in segments:
        name = seg.get("name", "未知")
        tier = seg.get("tier", "中游")
        barrier = seg.get("barrier_score", 5)
        profit = seg.get("profit_score", 5)
        growth = seg.get("growth_score", 5)
        companies = seg.get("companies", [])
        notes = seg.get("notes", "")

        names.append(name)
        x_vals.append(barrier)
        y_vals.append(profit)
        # 增长速度映射为气泡大小 (5-40范围)
        sizes.append(growth * 5 + 10)
        colors.append(TIER_COLORS.get(tier, "#95A5A6"))
        tier_labels.append(tier)

        # 悬停文本
        company_str = "、".join(companies[:3]) if companies else "待补充"
        hover_text = (
            f"<b>{name}</b><br>"
            f"层级：{tier}<br>"
            f"壁垒高度：{barrier}/10<br>"
            f"利润水平：{profit}/10<br>"
            f"增长速度：{growth}/10<br>"
            f"代表公司：{company_str}<br>"
        )
        if notes:
            hover_text += f"备注：{notes}"
        hover_texts.append(hover_text)

    # 创建气泡图
    fig = go.Figure()

    # 按层级分组绘制（用于图例）
    tier_groups = {}
    for i, tier in enumerate(tier_labels):
        if tier not in tier_groups:
            tier_groups[tier] = []
        tier_groups[tier].append(i)

    for tier, indices in tier_groups.items():
        fig.add_trace(go.Scatter(
            x=[x_vals[i] for i in indices],
            y=[y_vals[i] for i in indices],
            marker=dict(
                size=[sizes[i] for i in indices],
                color=TIER_COLORS.get(tier, "#95A5A6"),
                opacity=0.75,
                line=dict(width=2, color="white"),
                sizemode="diameter",
            ),
            mode="markers+text",
            text=[names[i] for i in indices],
            textposition="top center",
            textfont=dict(size=11),
            name=tier,
            hovertemplate="%{hovertext}<extra></extra>",
            hovertext=[hover_texts[i] for i in indices],
            customdata=[hover_texts[i] for i in indices],
        ))

    # 添加"三高"区域高亮
    fig.add_shape(
        type="rect",
        x0=7, y0=7, x1=10.5, y1=10.5,
        fillcolor="rgba(255, 215, 0, 0.08)",
        line=dict(width=1, dash="dash", color="rgba(255, 215, 0, 0.5)"),
        layer="below",
    )
    fig.add_annotation(
        x=8.5, y=10.2,
        text="🏆 三高区域（壁垒≥7 & 利润≥7）",
        showarrow=False,
        font=dict(size=11, color="rgba(255, 165, 0, 0.8)"),
    )

    # 气泡大小图例
    fig.add_trace(go.Scatter(
        x=[0.5], y=[0.5],
        marker=dict(size=15, color="rgba(0,0,0,0)", line=dict(width=0)),
        mode="markers",
        showlegend=False,
        hoverinfo="skip",
    ))

    # 布局
    fig.update_layout(
        title=dict(
            text=f"{industry} 产业链气泡图<br>"
                 "<sub>X轴=壁垒高度 | Y轴=利润水平 | 气泡大小=增长速度</sub>",
            font=dict(size=20),
        ),
        xaxis=dict(
            title=dict(text="壁垒高度 (1-10)", font=dict(size=14)),
            range=[0, 11],
            dtick=1,
            gridcolor="rgba(0,0,0,0.1)",
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="利润水平 (1-10)", font=dict(size=14)),
            range=[0, 11],
            dtick=1,
            gridcolor="rgba(0,0,0,0.1)",
            zeroline=False,
        ),
        plot_bgcolor="rgba(248,249,250,1)",
        paper_bgcolor="white",
        legend=dict(
            title=dict(text="产业链层级"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Microsoft YaHei, PingFang SC, sans-serif",
        ),
        width=1200,
        height=800,
        margin=dict(l=80, r=40, t=120, b=60),
    )

    # 保存
    if output_path is None:
        output_path = f"{industry}_产业链气泡图.html"

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    fig.write_html(output_path)
    print(f"[OK] 气泡图已生成：{output_path}")
    return output_path


def main():
    args = parse_args()
    data = load_data(args)
    output = args.output or f"{data.get('industry', '产业链')}_产业链气泡图.html"
    generate_bubble_chart(data, output)


if __name__ == "__main__":
    main()
