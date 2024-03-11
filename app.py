import datetime

import gradio as gr

from gpuhunter.data_object import RegionList, Config

with gr.Blocks(title="AutoDL GPU Hunter", theme=gr.themes.Default(text_size="lg")) as demo:
    config = Config().load()
    all_region_list = RegionList().update()
    all_gpu_type_names = all_region_list.get_gpu_type_names()
    gr.Markdown(
        """
        # 🐒 AutoDL GPU Hunter
        这是一个卡蹲蹲！帮你蹲守 AutoDL 显卡主机，请设置以下参数开始蹲守。官网链接：[算力市场](https://www.autodl.com/market/list)
        | [容器实例](https://www.autodl.com/console/instance/list)
        """
    )
    gr.Textbox(label="开发者 Token", lines=2, placeholder="AutoDL/控制台/账号/设置/开发者 Token")
    with gr.Tab("🌲 开始蹲守"):
        gr.CheckboxGroup(["RTX 4090", "RTX 3090", "RTX 4090"], label="显卡型号", info=""),
        gr.CheckboxGroup(["西北B区", "北京B区"], label="地区", info=""),
        gr.Button("🙈 现在开始", variant="primary", size="lg")
        with gr.Row():
            with gr.Column(scale=8):
                gr.Markdown("### 暂时还没有空闲的 GPU 主机。")
                gr.Markdown("2024-03-02 15:03:34")
            with gr.Column(scale=2):
                gr.Button("停止", variant="stop", size="sm")
        # 显卡型号： 多选
        # 地区： 全部，多选
        # 显卡数量
        # 镜像
        # 蹲到之后：立即租用，邮件通知  多选
        # 立即租用：
        #   定时关机：第二天0点  租用xxx分钟后  不设置
        #   开发者 Token（开发者 Token）
        #   复制已有实例：
        #   租用数量：3
        # 邮件通知：接受通知的邮箱，需要发送测试邮件的功能
        # 时间间隔：1分钟，10分钟（默认），30分钟，60分钟。（如果不是急需，请设置长一点的时间，避免给 autodl 增加压力）
        # 🙈 现在开始，🙉 正在蹲守（风险提示）
        # output：
        #   暂时还没有空闲的 GPU 主机。
        #   发现 GPU 主机：西北B区，RTX 4090，立即租用
        #   当前已启动 4 个容器实例
        #   2024-03-02 15:03:34
        # 守到后关机

    with gr.Tab("🐰 算力实况"):
        gr.Markdown("## 当前 GPU 主机数量")
        last_update_time = datetime.datetime.now()
        selected_gpu_type_names = [
            "RTX 4090",
            "RTX 3090",
            "RTX 3080 Ti",
            "RTX 3080",
            "RTX 3060",
        ]

        gr_gpu_checkbox_group = gr.CheckboxGroup(all_gpu_type_names, label="显卡型号", value=selected_gpu_type_names)
        gr_gpu_region_matrix = gr.Matrix()

        with gr.Row():
            with gr.Column(scale=8):
                gr_bottom_text = gr.Markdown()
            with gr.Column(scale=2):
                stat_update_button = gr.Button("立即更新", size="sm")


        def update_matrix(gpu_type_names):
            global selected_gpu_type_names
            selected_gpu_type_names = gpu_type_names
            return {
                "headers": ["地区"] + [n for n in gpu_type_names],
                "data": [
                    [r["region_name"]] + [
                        all_region_list.get_region_stats([gn], [r["region_name"]])[0]["idle_gpu_num"] or ""
                        for gn in gpu_type_names
                    ]
                    for r in all_region_list.get_region_stats()
                ]
            }


        def refresh_matrix(gpu_type_names):
            global all_region_list, last_update_time
            all_region_list = RegionList().update()
            last_update_time = datetime.datetime.now()
            bottom_text = f"以上是当前 AutoDL 官网查询到的 GPU 主机数量，" \
                          f"更新时间：{last_update_time.strftime('%Y-%m-%d %H:%M:%S')}。"
            return update_matrix(gpu_type_names), bottom_text


        demo.load(update_matrix, inputs=[gr_gpu_checkbox_group], outputs=gr_gpu_region_matrix)
        gr_gpu_checkbox_group.input(update_matrix, inputs=[gr_gpu_checkbox_group], outputs=gr_gpu_region_matrix)
        stat_update_button.click(refresh_matrix, inputs=[gr_gpu_checkbox_group],
                                 outputs=[gr_gpu_region_matrix, gr_bottom_text])

if __name__ == "__main__":
    demo.launch()
