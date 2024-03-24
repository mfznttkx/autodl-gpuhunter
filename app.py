import os.path

import gradio as gr

from gpuhunter.autodl_client import FailedError, autodl_client
from gpuhunter.data_object import RegionList, Config
from main import LOGS_DIR

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
        with gr.Group():
            gr_gpu_type = gr.CheckboxGroup(["RTX 4090 (28)", "RTX 3090", "RTX 4090"], label="显卡型号", info="")
            gr_region = gr.CheckboxGroup(["西北B区 (12)", "北京B区 (0)"], label="地区", info="")
            gr_gpu_num = gr.Radio(choices=[n for n in range(1, 13)], label="GPU 数量", value=1)

        with gr.Row():
            with gr.Column():
                gr_instance_num = gr.Slider(label="租用 GPU 主机数量", info="可选择 1-10 台")
                gr_image_category = gr.Radio(choices=["基础镜像", "社区镜像", "我的镜像"], label="启动镜像")
                with gr.Group() as gr_base_image_group:
                    with gr.Row():
                        gr_base_image_framework_name = gr.Dropdown(
                            choices=["AUTOMATIC1111/stable-diffusion-webui/tzwm_sd_webui_A1111 / v18"],
                            show_label=False, info="框架名称")
                        gr_base_image_framework_version = gr.Dropdown(
                            choices=["AUTOMATIC1111/stable-diffusion-webui/tzwm_sd_webui_A1111 / v18"],
                            show_label=False, info="框架版本")
                    with gr.Row():
                        gr_base_image_python_version = gr.Dropdown(
                            choices=["AUTOMATIC1111/stable-diffusion-webui/tzwm_sd_webui_A1111 / v18"],
                            show_label=False, info="Python 版本")
                        gr_base_image_cuda_version = gr.Dropdown(
                            choices=["AUTOMATIC1111/stable-diffusion-webui/tzwm_sd_webui_A1111 / v18"],
                            show_label=False, info="Cuda 版本")
                with gr.Group() as gr_shared_image_group:
                    gr.Dropdown(choices=["AUTOMATIC1111/stable-diffusion-webui/tzwm_sd_webui_A1111 / v18"],
                                show_label=False, info="框架名称")
                with gr.Group() as gr_private_image_group:
                    gr.Dropdown(choices=["AUTOMATIC1111/stable-diffusion-webui/tzwm_sd_webui_A1111 / v18"],
                                show_label=False, info="框架名称")

                with gr.Accordion("扩容数据盘：50 GB", open=False) as gr_expand_disk_accordion:
                    gr_expand_disk_gb = gr.Slider(info="可选择容量范围 0-60 GB", show_label=False)

                with gr.Accordion("复制已有实例：adc5a6cc5a446a", open=False) as gr_clone_instance_accordion:
                    gr_clone_instance_uuid = gr.Dropdown(
                        choices=["AUTOMATIC1111/stable-diffusion-webui/tzwm_sd_webui_A1111 / v18"],
                        show_label=False, info="选择要复制的实例")

            with gr.Column():
                with gr.Accordion("定时关机：今天 23:59", open=False) as gr_shutdown_time_accordion:
                    gr_shutdown_time_type = gr.Radio(choices=["今天 23:59", "8 小时", "12 小时", "24 小时", "不关机"],
                                                     label="定时关机",
                                                     info="创建实例时自动设置定时关机，防止忘记关闭后产生费用。")

                with gr.Accordion("邮件通知：zhangsan@lisi.com", open=False) as gr_email_notify_accordion:
                    with gr.Row(equal_height=True):
                        with gr.Group():
                            gr_email_notify_sender = gr.Textbox(label="发信邮箱", type="email")
                            gr_email_notify_smtp_password = gr.Textbox(label="发信邮箱登录密码", type="password")
                            gr_email_notify_smtp_server = gr.Textbox(label="SMTP 服务器")
                        with gr.Column():
                            gr_email_notify_receipt = gr.Textbox(label="收信邮箱", type="email",
                                                                 info="可以用收信邮箱自己发给自己")
                            gr_email_notify_send_button = gr.Button("发送测试邮件", size="sm")
                            gr_email_notify_send_output = gr.Markdown("## 发送成功！")

                with gr.Accordion("更多选项", open=False):
                    gr_scan_interval = gr.Slider(minimum=1, maximum=60, value=10, step=1, label="扫描间隔时间",
                                                 info="如果不是急需，请设置长一点的时间，显卡空出来也需要时间，同时请避免给 AutoDL.com 增加压力。")
                    gr_shutdown_hunter_after_success = gr.Radio(choices=["关机", "不关机"],
                                                                label="守到后将 Hunter 关机",
                                                                info="成功后关闭运行此程序 (AutoDL GPU Hunter) 的机器，防止重复蹲守浪费资源。")

        gr_hunt_start_button = gr.Button("🙈 现在开始", variant="primary", size="lg")
        gr_hunt_stop_button = gr.Button("🤚 停止", variant="stop", size="lg")
        gr_hunt_logs = gr.Textbox(label="🙉 正在蹲守", autoscroll=True, lines=10)


        def read_output_logs():
            with open(os.path.join(LOGS_DIR, "output.log"), "r") as f:
                return f.read()


        # def load_stat(gpu_type_names=None, region_list=None):
        #     region_list = region_list or RegionList().load()
        #     gpu_type_names = gpu_type_names or [
        #         "RTX 4090",
        #         "RTX 3090",
        #         "RTX 3080 Ti",
        #         "RTX 3080",
        #         "RTX 3060",
        #     ]
        #     return {
        #         **update_matrix(gpu_type_names),
        #         gr_gpu_checkbox_group: gr.CheckboxGroup(choices=region_list.get_gpu_type_names(), value=gpu_type_names),
        #         gr_stat_note: gr.Markdown(f"以上是当前 AutoDL 官网查询到的 GPU 主机数量，"
        #                                   f'更新时间：{region_list.modified_time.strftime("%Y-%m-%d %H:%M:%S")}。'),
        #     }

        demo.load(read_output_logs, None, gr_hunt_logs, every=1)

        # 立即租用：
        #   定时关机：第二天0点  租用xxx分钟后  不设置
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
                                          f'更新时间：{region_list.modified_time.strftime("%Y-%m-%d %H:%M:%S")}。'),
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
                error_message = str(e)
                if "登录失败，请重试" in error_message:
                    error_message = "登录失败，请检查 Token 后重试。"
                elif "登陆超时" in error_message:
                    error_message = "登录超时，请先打开 AutoDL.com 官网登录一下账号，然后返回并点击确定。"
                return {
                    gr_token_input_group: gr.Group(visible=True),
                    gr_token_view_group: gr.Group(visible=False),
                    gr_token_input: gr.Textbox(value=config.token),
                    gr_token_input_error: gr.Markdown(visible=True, value=error_message),
                }
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
