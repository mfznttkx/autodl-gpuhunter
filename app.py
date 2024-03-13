import gradio as gr

from gpuhunter.autodl_client import FailedError, autodl_client
from gpuhunter.data_object import RegionList, Config

css = """
.block.error-message { padding: var(--block-padding); }
.block.error-message p { color: var(--error-icon-color); font-weight: bold; margin: 0; }
"""
with gr.Blocks(title="AutoDL GPU Hunter", theme=gr.themes.Default(text_size="lg"), css=css) as demo:
    gr.Markdown(
        """
        # 🐒 AutoDL GPU Hunter
        这是一个卡蹲蹲！帮你蹲守 AutoDL 显卡主机，请设置以下参数开始蹲守。官网链接：[算力市场](https://www.autodl.com/market/list)
        | [容器实例](https://www.autodl.com/console/instance/list)
        """
    )

    with gr.Group(visible=False) as gr_token_input_group:
        gr_token_input = gr.Textbox(label="开发者 Token", lines=2,
                                    info="本 Token 以明文 JSON 格式保存在运行本程序的服务器上，"
                                         "切勿在不信任的服务器上填写你的 Token，否则会被人盗用账号而造成意外损失！",
                                    placeholder="获取方法：进入 AutoDL 网站 / 控制台 / 账号 / 设置 / 开发者 Token")
        gr_token_input_error = gr.Markdown(elem_classes=["error-message"], visible=False)
        gr_token_save_button = gr.Button("确定", variant="primary", size="lg")

    with gr.Group(visible=False) as gr_token_view_group:
        gr_token_view_input = gr.Textbox(label="开发者 Token", lines=1, interactive=False)
        gr_token_clear_button = gr.Button("退出", variant="secondary", size="sm")

    with gr.Tab("🌲 开始蹲守", visible=False) as gr_config_tab:
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

    with gr.Tab("🐰 算力实况", visible=False) as gr_stat_tab:
        gr.Markdown("## 当前 GPU 主机数量")
        gr_gpu_checkbox_group = gr.CheckboxGroup([], label="显卡型号")
        gr_gpu_region_matrix = gr.Matrix()
        with gr.Row():
            with gr.Column(scale=8):
                gr_stat_note = gr.Markdown()
            with gr.Column(scale=2):
                gr_stat_refresh_button = gr.Button("立即更新", size="sm")


        def refresh_stat(gpu_type_names=None):
            region_list = RegionList().update()
            return load_stat(gpu_type_names, region_list)


        def load_stat(gpu_type_names=None, region_list=None):
            region_list = region_list or RegionList().load()
            gpu_type_names = gpu_type_names or [
                "RTX 4090",
                "RTX 3090",
                "RTX 3080 Ti",
                "RTX 3080",
                "RTX 3060",
            ]
            return {
                **update_matrix(gpu_type_names),
                gr_gpu_checkbox_group: gr.CheckboxGroup(choices=region_list.get_gpu_type_names(), value=gpu_type_names),
                gr_stat_note: gr.Markdown(f"以上是当前 AutoDL 官网查询到的 GPU 主机数量，"
                                          f"更新时间：{region_list.modified_time.strftime('%Y-%m-%d %H:%M:%S')}。"),
            }


        def update_matrix(gpu_type_names):
            region_list = RegionList().load()
            return {
                gr_gpu_region_matrix: gr.Matrix(headers=["地区"] + [n for n in gpu_type_names], value=[
                    [r["region_name"]] + [
                        region_list.get_region_stats([gn], [r["region_name"]])[0]["idle_gpu_num"] or ""
                        for gn in gpu_type_names
                    ]
                    for r in region_list.get_region_stats()
                ]),
            }


        gr_gpu_checkbox_group.change(update_matrix, inputs=[gr_gpu_checkbox_group], outputs=[gr_gpu_region_matrix],
                                     show_progress="hidden")
        gr_stat_refresh_button.click(refresh_stat, inputs=[gr_gpu_checkbox_group],
                                     outputs=[gr_gpu_checkbox_group, gr_gpu_region_matrix, gr_stat_note])
        demo.load(load_stat, outputs=[gr_gpu_checkbox_group, gr_gpu_region_matrix, gr_stat_note])


    def load_config(config=None):
        if config is None:
            config = Config().load()
        if config.token:
            try:
                RegionList().update()
            except FailedError as e:
                if "登录失败，请重试" in str(e):
                    return {
                        gr_token_input_group: gr.Group(visible=True),
                        gr_token_view_group: gr.Group(visible=False),
                        gr_token_input: gr.Textbox(value=config.token),
                        gr_token_input_error: gr.Markdown(visible=True, value="登录失败，请检查 Token 后重试。"),
                    }
                else:
                    raise
            return {
                gr_token_input_group: gr.Group(visible=False),
                gr_token_view_group: gr.Group(visible=True),
                gr_token_view_input: config.token[:6] + "******" + config.token[-6:],
                gr_config_tab: gr.Tab(visible=True),
                gr_stat_tab: gr.Tab(visible=True),
                gr_token_input_error: gr.Markdown(visible=False),
            }
        else:
            return {
                gr_token_input_group: gr.Group(visible=True),
                gr_token_view_group: gr.Group(visible=False),
                gr_token_input: gr.Textbox(value=""),
                gr_config_tab: gr.Tab(visible=False),
                gr_stat_tab: gr.Tab(visible=False),
            }


    def save_token(token):
        config = Config().load()
        config.token = token
        config.save()
        autodl_client.load_config()
        return load_config(config)


    def clear_token():
        return save_token("")


    demo.load(load_config, outputs=[gr_token_input_group, gr_token_input, gr_token_input_error,
                                    gr_token_view_group, gr_token_view_input, gr_config_tab, gr_stat_tab])

    gr_token_save_button.click(save_token, inputs=[gr_token_input],
                               outputs=[gr_token_input_group, gr_token_input, gr_token_input_error,
                                        gr_token_view_group, gr_token_view_input, gr_config_tab, gr_stat_tab])
    gr_token_clear_button.click(clear_token,
                                outputs=[gr_token_input_group, gr_token_input, gr_token_input_error,
                                         gr_token_view_group, gr_token_view_input, gr_config_tab, gr_stat_tab])

if __name__ == "__main__":
    demo.launch()
