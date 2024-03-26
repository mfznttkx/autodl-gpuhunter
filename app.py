import json
import os.path
import re

import gradio as gr

from gpuhunter.autodl_client import FailedError, autodl_client
from gpuhunter.data_object import RegionList, Config
from gpuhunter.utils.helpers import json_dumps, validate_email
from main import LOGS_DIR

css = """
.block.error-message, .block.success-message { padding: var(--block-padding); }
.block.error-message p, .block.success-message p { font-weight: bold; margin: 0; }
.error-message ul li, .block.error-message p { color: var(--error-icon-color);}
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
        gr_token_input = gr.Textbox(
            label="开发者 Token",
            lines=2,
            info="本 Token 以明文 JSON 格式保存在运行本程序的服务器上，"
                 "切勿在不信任的服务器上填写你的 Token，否则会被人盗用账号而造成意外损失！",
            placeholder="获取方法：进入 AutoDL 网站 / 控制台 / 账号 / 设置 / 开发者 Token"
        )
        gr_token_input_error = gr.Markdown(elem_classes=["error-message"], visible=False)
        gr_token_save_button = gr.Button("确定", variant="primary", size="lg")

    with gr.Group(visible=False) as gr_token_view_group:
        gr_token_view_input = gr.Textbox(label="开发者 Token", lines=1, interactive=False)
        gr_token_clear_button = gr.Button("退出", variant="secondary", size="sm")

    with gr.Tab("🌲 开始蹲守", visible=False) as gr_config_tab:
        with gr.Row():
            with gr.Column():
                with gr.Group():
                    gr_gpu_types = gr.CheckboxGroup(label="显卡型号")
                    gr_regions = gr.CheckboxGroup(label="地区")
                    gr_gpu_num = gr.Radio(choices=[n for n in range(1, 13)], label="GPU 个数", value=1)

            with gr.Column():
                gr_instance_num = gr.Slider(label="租用 GPU 主机数量", info="可选择 1-20 台", minimum=0, maximum=20,
                                            step=1, value=1)
                with gr.Group():
                    gr_image_category = gr.Radio(
                        choices=[("基础镜像", "base"), ("社区镜像", "shared"), ("我的镜像", "private")],
                        label="启动镜像",
                    )
                    with gr.Group(visible=False) as gr_base_image_group:
                        gr_base_image = gr.Dropdown(show_label=False, info="请选择镜像")
                    with gr.Group(visible=False) as gr_shared_image_group:
                        gr_shared_image_search = gr.Textbox(show_label=False, info="请填写关键字查找镜像")
                        gr_shared_image = gr.Dropdown(show_label=False, info="请选择镜像")
                    with gr.Group(visible=False) as gr_private_image_group:
                        gr_private_image = gr.Dropdown(show_label=False, info="请选择镜像")

                with gr.Accordion(open=False) as gr_expand_disk_accordion:
                    gr_expand_disk_gb = gr.Slider(
                        info="可选择扩容范围 0-3000 GB，按此扩容量挑选机器并要求扩容",
                        minimum=0,
                        maximum=3000,
                        step=1,
                        value=0,
                        show_label=False,
                    )

                with gr.Accordion(open=False) as gr_clone_instances_accordion:
                    with gr.Group():
                        with gr.Row():
                            gr_clone_instances = gr.Dropdown(
                                label="选择实例",
                                info="只能克隆同地区的实例，请确保实例已关机。如蹲守多个地区，"
                                     "可以为每个地区选择一个要克隆的实例，蹲守到主机后会按照主机所在地区进行匹配",
                                min_width=550,
                                multiselect=True
                            )
                            gr_clone_instances_refresh_button = gr.Button("刷新", size="sm", min_width=50)
                        gr_copy_data_after_clone = gr.Checkbox(label="克隆后复制数据盘", value=True)
                        gr_keep_address_after_clone = gr.Checkbox(label="克隆后保持服务网址", value=True)

                with gr.Accordion(open=False) as gr_shutdown_time_accordion:
                    gr_shutdown_time_type = gr.Radio(
                        show_label=False,
                        choices=["今晚 23:59", "8 小时", "12 小时", "24 小时", "不关机"],
                        value="今晚 23:59",
                        info="创建实例时自动设置定时关机，防止忘记关闭后产生费用。")

                with gr.Accordion(open=False) as gr_email_notify_accordion:
                    with gr.Group():
                        with gr.Row(equal_height=True):
                            with gr.Group():
                                gr_email_notify_sender = gr.Textbox(label="发信/收信邮箱", type="email")
                                gr_email_notify_smtp_password = gr.Textbox(
                                    label="发信密码", type="password",
                                    info="以明文方式保存在此机，请确保环境安全再填写！如果你的邮箱很重要，不推荐直接填写账号密码。"
                                         "很多邮箱都支持单独的发信密码 (或叫授权码等)，推荐使用这类临时密码。"
                                         "实在不信就新注册一个免费邮箱！"
                                )
                            gr_email_notify_smtp_server = gr.Textbox(label="SMTP 服务器")
                    gr_email_notify_send_button = gr.Button("发送测试邮件", size="sm")
                    gr_email_notify_send_output = gr.Markdown(visible=False)

                with gr.Accordion("更多选项", open=False):
                    gr_scan_interval = gr.Slider(
                        minimum=1,
                        maximum=60,
                        value=10,
                        step=1,
                        label="扫描间隔 (分钟)",
                        info="默认：10分钟，可选 1-60 分钟。如果不是急需，请设置长一点的时间，"
                             "因为显卡空出来也需要时间，同时也能减少给官网的访问压力。"
                    )
                    gr_shutdown_hunter_after_success = gr.Radio(
                        choices=[("关机", True), ("不关机", False)],
                        value=False,
                        label="守到后将 Hunter 关机",
                        info="成功后可以关闭运行此程序 (AutoDL GPU Hunter) 的机器，防止重复蹲守浪费资源。"
                    )

        gr_hunting_start_button = gr.Button("🙈 开始蹲守", variant="primary", size="lg")
        gr_hunting_error = gr.Markdown(elem_classes=["error-message"], visible=False)
        gr_hunting_stop_button = gr.Button("🤚 停止", variant="stop", size="lg", visible=False)
        gr_hunting_logs = gr.Textbox(label="🙉 正在蹲守", autoscroll=True, lines=10, visible=False)


        def load_region_options(gpu_type_names=None):
            region_list = RegionList().load()
            return {
                gr_regions: gr.CheckboxGroup(
                    choices=[
                        (f'{r["region_name"]} ({r["idle_gpu_num"]})', r["region_name"])
                        for r in region_list.get_region_stats(gpu_types=gpu_type_names or [])
                        if r["total_gpu_num"] > 0
                    ],
                ),
            }


        def load_gpu_options():
            region_list = RegionList().load()
            return {
                gr_gpu_types: gr.CheckboxGroup(
                    choices=[
                        (f'{g["gpu_type"]} ({g["idle_gpu_num"]})', g["gpu_type"])
                        for g in region_list.get_gpu_stats()
                        if g["total_gpu_num"] > 0
                    ],
                ),
            }


        def load_gpu_region_options():
            return {
                **load_gpu_options(),
                **load_region_options(),
            }


        def load_image_options(image_category):
            image_option_groups = {
                gr_base_image_group: gr.Group(visible=False),
                gr_shared_image_group: gr.Group(visible=False),
                gr_private_image_group: gr.Group(visible=False),
                gr_base_image: gr.Dropdown(),
                gr_shared_image: gr.Dropdown(),
                gr_private_image: gr.Dropdown(),
            }
            if image_category == "base":
                base_images = autodl_client.get_base_images()
                return {
                    **image_option_groups,
                    gr_base_image_group: gr.Group(visible=True),
                    gr_base_image: gr.Dropdown(
                        choices=[
                            (f'{f["label"]} / {fv["label"]} / {p["label"]} / {c["label"]}',
                             json_dumps({"base_image_labels": [f["label"], fv["label"], p["label"], c["label"]]}))
                            for f in base_images
                            for fv in f["children"]
                            for p in fv["children"]
                            for c in p["children"]
                        ]
                    )
                }
            elif image_category == "shared":
                return {
                    **image_option_groups,
                    gr_shared_image_group: gr.Group(visible=True),
                }
            elif image_category == "private":
                private_images = autodl_client.get_private_images()
                return {
                    **image_option_groups,
                    gr_private_image_group: gr.Group(visible=True),
                    gr_private_image: gr.Dropdown(
                        choices=[
                            (f'{i["name"]} ({i["image_uuid"]})',
                             json_dumps({
                                 "private_image_uuid": i["image_uuid"],
                                 "private_image_name": i["name"],
                             }))
                            for i in private_images
                        ]
                    )
                }
            else:
                return image_option_groups


        def load_shared_image_options(shared_image_search):
            shared_images = autodl_client.get_shared_images(shared_image_search)
            return {
                gr_shared_image: gr.Dropdown(
                    choices=[
                        (f'{i["uuid"]} / v{v["version"]} ({i["username"]})',
                         json_dumps({
                             "shared_image_keyword": i["uuid"],
                             "shared_image_username_keyword": i["username"],
                             "shared_image_version": str(v["version"]),
                         }))
                        for i in shared_images
                        for v in i["version_info"]
                    ]
                ),
            }


        def update_disk_accordion(expand_disk_gb):
            return {
                gr_expand_disk_accordion: gr.Accordion(
                    label=f"数据盘：免费 50 GB + 扩容 {expand_disk_gb} GB" if expand_disk_gb > 0 else "扩容数据盘"
                )
            }


        def load_clone_instances_options():
            def get_label(image):
                return f'{image["region_name"]} / {image["machine_alias"]} ({image["uuid"]})'

            return {
                gr_clone_instances: gr.Dropdown(
                    choices=[
                        *[
                            (get_label(i),
                             json_dumps({
                                 "label": get_label(i),
                                 "uuid": i["uuid"],
                                 "region_name": i["region_name"],
                             }))
                            for i in autodl_client.list_instance("shutdown")
                        ]
                    ]
                )
            }


        def update_clone_instances_accordion(clone_instances):
            title_suffix = ""
            if clone_instances:
                if len(clone_instances) == 1:
                    clone_instances_info = json.loads(clone_instances[0])
                    clone_instances_label = clone_instances_info["label"]
                    title_suffix = f"：{clone_instances_label}" if clone_instances_label else ""
                else:
                    title_suffix = f'：{"、".join([json.loads(i)["label"] for i in clone_instances])}'
            return {
                gr_clone_instances_accordion: gr.Accordion(label=f'克隆现有实例{title_suffix}')
            }


        def update_shutdown_time_accordion(shutdown_time_type):
            return {
                gr_shutdown_time_accordion: gr.Accordion(
                    f'定时关机{f"：{shutdown_time_type}" if shutdown_time_type else ""}'
                )
            }


        def update_email_notify_accordion(email_notify_sender):
            return {
                gr_email_notify_accordion: gr.Accordion(
                    f'邮件通知{f"：{email_notify_sender}" if email_notify_sender else ""}'
                ),
            }


        def send_test_email(email_notify_sender, email_notify_smtp_password, email_notify_smtp_server):
            error_message = None
            if not email_notify_sender:
                error_message = "请填写发信/收信邮箱"
            elif not email_notify_smtp_password:
                error_message = "请填写发信密码"
            elif not email_notify_smtp_server:
                error_message = "SMTP 服务器"
            if not error_message:
                from gpuhunter.utils.mail import normalize_smtp_server, send_mail
                from smtplib import SMTPException
                smtp_host, smtp_port = normalize_smtp_server(email_notify_smtp_server)
                try:
                    send_mail(
                        email_notify_sender,
                        "[GPUHunter] 可以收到邮件！",
                        content="恭喜！看到这份邮件说明你的邮件通知设置没有问题。",
                        sender=email_notify_sender,
                        smtp_host=smtp_host,
                        smtp_port=smtp_port,
                        smtp_username=email_notify_sender,
                        smtp_password=email_notify_smtp_password,
                    )
                except SMTPException as e:
                    error_message = f"发信失败：{str(e)}"
            return {
                **update_email_notify_accordion(email_notify_sender),
                gr_email_notify_send_output:
                    gr.Markdown(
                        error_message,
                        visible=True,
                        elem_classes=["error-message"]
                    ) if error_message
                    else gr.Markdown(
                        "邮件发送成功！",
                        visible=True,
                        elem_classes=["success-message"]
                    )
            }


        def hunting_start(gpu_types, regions, gpu_num, instance_num, image_category, base_image, shared_image,
                          private_image, expand_disk_gb, clone_instances, copy_data_after_clone,
                          keep_address_after_clone, shutdown_time_type, email_notify_sender,
                          email_notify_smtp_password, email_notify_smtp_server, scan_interval,
                          shutdown_hunter_after_success):
            error_messages = []
            if not gpu_types:
                error_messages.append("请选择显卡型号")
            if not regions:
                error_messages.append("请选择地区")
            if not gpu_num or gpu_num <= 0 or gpu_num > 12:
                error_messages.append("请选择有效的 GPU 个数")
            if not instance_num or instance_num <= 0 or instance_num > 20:
                error_messages.append("请选择有效的 GPU 主机数量")
            if not image_category:
                error_messages.append("请选择启动镜像")
            else:
                if image_category == "base" and not base_image \
                        or image_category == "shared" and not shared_image \
                        or image_category == "private" and not private_image:
                    error_messages.append("请选择镜像")
            if not shutdown_time_type:
                error_messages.append("请选择是否定时关机")
            if email_notify_sender:
                try:
                    validate_email(email_notify_sender)
                except ValueError:
                    error_messages.append("邮件地址不正确")
                if not email_notify_smtp_password:
                    error_messages.append("请填写发信密码")
                if not email_notify_smtp_server:
                    error_messages.append("请填写 SMTP 服务器地址")

            if len(error_messages) == 0:
                config = Config().load()

                config.region_names = regions
                config.gpu_type_names = gpu_types
                config.gpu_idle_num = gpu_num
                config.instance_num = instance_num

                config.base_image_labels = []
                config.shared_image_keyword = ""
                config.shared_image_username_keyword = ""
                config.shared_image_version = ""
                config.private_image_uuid = ""
                config.private_image_name = ""
                image_info_json = None
                if image_category == "base":
                    image_info_json = base_image
                elif image_category == "shared":
                    image_info_json = shared_image
                elif image_category == "private":
                    image_info_json = private_image
                if image_info_json:
                    image_info = json.loads(image_info_json)
                    for k, v in image_info.items():
                        setattr(config, k, v)

                config.expand_data_disk = expand_disk_gb * 1073741824

                if clone_instances:
                    config.clone_instances = [json.loads(i) for i in clone_instances]
                    config.copy_data_disk_after_clone = copy_data_after_clone
                    config.keep_src_user_service_address_after_clone = keep_address_after_clone
                else:
                    config.clone_instances = []
                    config.copy_data_disk_after_clone = False
                    config.keep_src_user_service_address_after_clone = False

                config.shutdown_instance_today = False
                config.shutdown_instance_after_hours = 0
                if shutdown_time_type == "今晚 23:59":
                    config.shutdown_instance_today = True
                elif shutdown_time_type.endswith("小时"):
                    config.shutdown_instance_after_hours = int(re.findall("^\\d+", shutdown_time_type)[0])

                config.shutdown_hunter_after_finished = shutdown_hunter_after_success
                config.retry_interval_minutes = max(1, scan_interval)

                if email_notify_sender:
                    from gpuhunter.utils.mail import normalize_smtp_server
                    config.mail_notify = True
                    config.mail_receipt = email_notify_sender
                    config.mail_sender = email_notify_sender
                    config.mail_smtp_host, config.mail_smtp_port = normalize_smtp_server(email_notify_smtp_server)
                    config.mail_smtp_username = email_notify_sender
                    config.mail_smtp_password = email_notify_smtp_password
                else:
                    config.mail_notify = False
                    config.mail_receipt = ""
                    config.mail_sender = ""
                    config.mail_smtp_host = ""
                    config.mail_smtp_port = ""
                    config.mail_smtp_username = ""
                    config.mail_smtp_password = ""
                print(config.to_dict())

                # todo 校验参数
                # todo 保存设置
                # todo 启动进程
                # todo 监控进程
                return {
                    gr_hunting_start_button: gr.Button(visible=False),
                    gr_hunting_error: gr.Markdown(visible=False),
                    gr_hunting_stop_button: gr.Button(visible=True),
                    gr_hunting_logs: gr.Textbox(visible=True),
                }
            else:
                return {
                    gr_hunting_start_button: gr.Button(visible=True),
                    gr_hunting_error: gr.Markdown(visible=True, value="\n".join([f"- {m}" for m in error_messages])),
                    gr_hunting_stop_button: gr.Button(visible=False),
                    gr_hunting_logs: gr.Textbox(visible=False),
                }


        def read_output_logs():
            with open(os.path.join(LOGS_DIR, "output.log"), "r") as f:
                return f.read()


        # GPU 和地区
        gr_gpu_types.change(load_region_options, [gr_gpu_types], outputs=[gr_regions])
        demo.load(load_gpu_region_options, None, [gr_gpu_types, gr_regions])

        # 镜像选择
        gr_image_category.change(
            load_image_options,
            [gr_image_category],
            [
                gr_base_image_group, gr_shared_image_group, gr_private_image_group,
                gr_base_image, gr_shared_image, gr_private_image
            ]
        )

        gr_shared_image_search.blur(load_shared_image_options, [gr_shared_image_search], [gr_shared_image])

        # 扩展磁盘
        gr_expand_disk_gb.change(
            update_disk_accordion,
            [gr_expand_disk_gb],
            [gr_expand_disk_accordion],
            show_progress=False
        )

        demo.load(update_disk_accordion, [gr_expand_disk_gb], [gr_expand_disk_accordion])

        # 复制已有实例
        gr_clone_instances_refresh_button.click(
            load_clone_instances_options, None,
            [gr_clone_instances]
        )
        gr_clone_instances.change(
            update_clone_instances_accordion,
            [gr_clone_instances],
            [gr_clone_instances_accordion],
            show_progress="hidden"
        )
        demo.load(update_clone_instances_accordion, [gr_clone_instances], [gr_clone_instances_accordion])
        demo.load(load_clone_instances_options, None, [gr_clone_instances])

        # 定时关机
        demo.load(update_shutdown_time_accordion, [gr_shutdown_time_type], [gr_shutdown_time_accordion])
        gr_shutdown_time_type.change(
            update_shutdown_time_accordion,
            [gr_shutdown_time_type],
            [gr_shutdown_time_accordion],
            show_progress=False
        )

        # 邮件通知
        demo.load(update_email_notify_accordion, [gr_email_notify_sender], [gr_email_notify_accordion])
        gr_email_notify_send_button.click(
            send_test_email,
            [gr_email_notify_sender, gr_email_notify_smtp_password, gr_email_notify_smtp_server],
            [gr_email_notify_accordion, gr_email_notify_send_output]
        )

        # 开始
        gr_hunting_start_button.click(
            hunting_start,
            [
                gr_gpu_types,
                gr_regions,
                gr_gpu_num,
                gr_instance_num,
                gr_image_category,
                gr_base_image,
                gr_shared_image,
                gr_private_image,
                gr_expand_disk_gb,
                gr_clone_instances,
                gr_copy_data_after_clone,
                gr_keep_address_after_clone,
                gr_shutdown_time_type,
                gr_email_notify_sender,
                gr_email_notify_smtp_password,
                gr_email_notify_smtp_server,
                gr_scan_interval,
                gr_shutdown_hunter_after_success,
            ],
            [
                gr_hunting_start_button,
                gr_hunting_error,
                gr_hunting_stop_button,
                gr_hunting_logs,
            ]
        )

        # 日志
        demo.load(read_output_logs, None, gr_hunting_logs, every=1)

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
                gr_stat_note: gr.Markdown(
                    f"以上是当前 AutoDL 官网查询到的 GPU 主机数量，"
                    f'更新时间：{region_list.modified_time.strftime("%Y-%m-%d %H:%M:%S")}。'
                ),
            }


        def update_matrix(gpu_type_names):
            region_list = RegionList().load()
            return {
                gr_gpu_region_matrix: gr.Matrix(
                    headers=["地区"] + [n for n in gpu_type_names],
                    value=[
                        [r["region_name"]] + [
                            region_list.get_region_stats([gn], [r["region_name"]])[0]["idle_gpu_num"] or ""
                            for gn in gpu_type_names
                        ]
                        for r in region_list.get_region_stats()
                    ]
                ),
            }


        gr_gpu_checkbox_group.change(
            update_matrix,
            inputs=[gr_gpu_checkbox_group],
            outputs=[gr_gpu_region_matrix],
            show_progress="hidden"
        )
        gr_stat_refresh_button.click(
            refresh_stat,
            inputs=[gr_gpu_checkbox_group],
            outputs=[gr_gpu_checkbox_group, gr_gpu_region_matrix, gr_stat_note]
        )
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


    demo.load(
        load_config,
        outputs=[gr_token_input_group, gr_token_input, gr_token_input_error,
                 gr_token_view_group, gr_token_view_input, gr_config_tab, gr_stat_tab]
    )

    gr_token_save_button.click(
        save_token,
        inputs=[gr_token_input],
        outputs=[gr_token_input_group, gr_token_input, gr_token_input_error,
                 gr_token_view_group, gr_token_view_input, gr_config_tab, gr_stat_tab]
    )
    gr_token_clear_button.click(
        clear_token,
        outputs=[gr_token_input_group, gr_token_input, gr_token_input_error,
                 gr_token_view_group, gr_token_view_input, gr_config_tab, gr_stat_tab]
    )

if __name__ == "__main__":
    demo.launch()
