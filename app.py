#!/usr/bin/env python

import gradio as gr
import numpy as np


def flip_text(x):
    return x[::-1]


def flip_image(x):
    return np.fliplr(x)


with gr.Blocks(title="AutoDL GPU Hunter", theme=gr.themes.Default(text_size="lg")) as demo:
    gr.Markdown(
        """
        # 🐒 AutoDL GPU Hunter
        这是一个卡蹲蹲！帮你蹲守 AutoDL 显卡算力，请设置以下参数开始。官网链接：[算力市场](https://www.autodl.com/market/list)
        | [容器实例](https://www.autodl.com/console/instance/list)
        """
    )
    with gr.Tab("🌲 开始蹲守"):
        # 显卡型号： 多选
        # 地区： 全部，多选
        # 蹲到之后：立即租用，邮件通知  多选
        # 立即租用：
        #   定时关机：第二天0点  租用xxx分钟后  不设置
        #   开发者 Token（开发者 Token）
        # 邮件通知：接受通知的邮箱
        # 时间间隔：1分钟，10分钟（默认），30分钟，60分钟。（如果不是急需，请设置长一点的时间，避免给 autodl 增加压力）
        # 🙈 现在开始，🙉 正在蹲守（风险提示）
        # output：
        #   暂时还没有空闲的 GPU 主机。
        #   发现空间 GPU 主机，西北B区
        #   2024-03-02 15:03:34
        gr.Markdown("## 现在开始")

    with gr.Tab("🐰 算力实况"):
        gr.Markdown("## 当前 GPU 主机数量")
        gr.Matrix(
            headers=["地区", "RTX 4090", "RTX 3090", "RTX 4090", "RTX 3090", "RTX 4090", "RTX 3090", "RTX 4090", "RTX 3090"],
            datatype=["str", "number", "number", "number", "number", "number", "number", "number", "number"],
            value=[
                ["西北B区", 1, 123, 1, 123, 1, 123, 1, 123, 1, 123, 1, 123],
                ["北京B区", 2, 0, 2, 0, 2, 0, 2, 0, 2, 0, 2, 0],
                ["北京A区", 3, 0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 0],
            ],
        )
        with gr.Row():
            with gr.Column(scale=8):
                gr.Markdown("以上是当前 AutoDL 官网查询到的 GPU 主机数量，更新时间：2024-03-02 09:45:33。")
            with gr.Column(scale=2):
                text_button = gr.Button("立即更新", size="sm")

if __name__ == "__main__":
    demo.launch()
