import os
import time
from datetime import timedelta, datetime
from smtplib import SMTPException

from gpuhunter.autodl_client import FailedError
from gpuhunter.utils.helpers import end_of_day
from main import logger


def after_finished(config, created_instance_names=None):
    # 如果需要，发送完成邮件
    if config.mail_notify and created_instance_names:
        from gpuhunter.utils.mail import send_mail
        try:
            content = (
                    "".join([
                        f"<p>- {n}</p>"
                        for n in created_instance_names
                    ])
                    + f'<p><a href="https://www.autodl.com/console/instance/list" target="_blank">打开控制台</a></p>'
            )
            send_mail(
                config.mail_receipt,
                subject=f"[GPUHunter] {len(created_instance_names)} 个实例创建完毕",
                content=content,
                sender=config.mail_sender,
                smtp_host=config.mail_smtp_host,
                smtp_port=config.mail_smtp_port,
                smtp_username=config.mail_smtp_username,
                smtp_password=config.mail_smtp_password
            )
        except SMTPException as e:
            logger.exception(e)
            logger.error(f"邮件发送失败，请确认邮件设置正确。"
                         f" Email sending failed, please check the email settings are correct.")
    # 尝试关机
    if config.shutdown_hunter_after_finished:
        logger.info(f"任务完成，现在关机。"
                    f" Mission accomplished, shutdown hunter now.")
        os.system("shutdown -h")


def try_to_create_instances():
    from gpuhunter.autodl_client import (
        autodl_client, resolve_image_info,
        get_running_instances, get_available_machines
    )
    from gpuhunter.data_object import Config, RegionList

    # todo 确保机器的数据盘扩容量足够
    # todo 确保要复制的实例已关机

    # 加载数据和配置
    config = Config().load()
    region_list = RegionList().update()
    region_sign_list = [s for r in region_list.list if r["region_name"] in config.region_names
                        for s in r["region_sign"]]
    logger.debug(f"config: {config.to_dict()!r}")
    logger.debug(f"region_list.list: {region_list.to_dict()!r}")

    # todo 按机器匹配要克隆的目标，修改配置 config.clone_instance_uuid -> config.clone_instances
    # 如果有克隆目标，确保使用同区域的机器
    if config.clone_instance_uuid:
        instance_snapshot = autodl_client.get_instance_snapshot(config.clone_instance_uuid)
        region_sign = instance_snapshot["machine_info_snapshot"]["region_sign"]
        if region_sign_list != [region_sign]:
            logger.info(f"即将克隆的实例 ({config.clone_instance_uuid}) 区域代码为：{region_sign}，"
                        f"只能使用该区域的机器，已选的区域将被忽略。"
                        f" Region code of the instance ({config.clone_instance_uuid}) to be cloned is: {region_sign}, "
                        f"only machines in that region can be used, selected regions will be ignored.")
            region_sign_list = [region_sign]
    logger.debug(f"region_sign_list: {region_sign_list!r}")
    logger.info(f"尝试创建 {config.instance_num} 个实例..."
                f" Try to create {config.instance_num} instances...")
    # 获取镜像
    image_info = resolve_image_info(
        base_image_labels=config.base_image_labels,
        shared_image_keyword=config.shared_image_keyword,
        shared_image_username_keyword=config.shared_image_username_keyword,
        shared_image_version=config.shared_image_version,
        private_image_uuid=config.private_image_uuid,
        private_image_name=config.private_image_name
    )
    logger.debug(f"image_info: {image_info!r}")
    # 获取当前运行的实例
    instances = get_running_instances(
        region_names=config.region_names,
        gpu_type_names=config.gpu_type_names,
        image=image_info["image"],
        private_image_uuid=image_info["private_image_uuid"],
        reproduction_uuid=image_info["reproduction_uuid"],
        reproduction_id=image_info["reproduction_id"]
    )
    if len(instances) > 0:
        logger.info(f"{len(instances)} 个符合要求的实例已经在运行。"
                    f" {len(instances)} requested instances are running.")
    instance_to_create_num = max(0, config.instance_num - len(instances))
    logger.debug(f"instances: {instances!r}")
    logger.debug(f"instance_to_create_num: {instance_to_create_num!r}")
    # 检查是否需要创建实例
    if instance_to_create_num == 0:
        # 如果没有，就立刻完成
        after_finished(config)
    else:
        # 如果需要，就创建实例
        # 寻找符合要求的机器
        machines = get_available_machines(
            region_sign_list,
            config.gpu_type_names,
            gpu_idle_num=config.gpu_idle_num,
            count=config.instance_num,
        )
        logger.debug(f"machines: {machines!r}")
        # 检查是否有可用的机器
        if len(machines) == 0:
            # 如果没有就跳过
            logger.info(f"没有可用的 GPU 机器。"
                        f" No available machine.")
        else:
            # 如果有符合要求的机器就创建实例
            created_instance_names = []
            for machine in machines[:instance_to_create_num]:
                try:
                    # 创建实例
                    instance_uuid = autodl_client.create_instance(
                        machine["machine_id"],
                        image_info["image"],
                        private_image_uuid=image_info["private_image_uuid"],
                        reproduction_uuid=image_info["reproduction_uuid"],
                        reproduction_id=image_info["reproduction_id"],
                        req_gpu_amount=config.gpu_idle_num,
                        expand_data_disk=config.expand_data_disk,
                        clone_instance_uuid=config.clone_instance_uuid,
                        copy_data_disk_after_clone=config.copy_data_disk_after_clone,
                        keep_src_user_service_address_after_clone=config.keep_src_user_service_address_after_clone,
                    )
                    # 设置实例名称
                    autodl_client.update_instance_name(instance_uuid, "🎁🐒")
                    # 设置定时关机
                    shutdown_at = None
                    if config.shutdown_instance_after_hours:
                        shutdown_at = datetime.now() + timedelta(hours=config.shutdown_instance_after_hours)
                    elif config.shutdown_instance_today:
                        shutdown_at = end_of_day(datetime.now())
                    if shutdown_at:
                        logger.debug(
                            f"shutdown planned, instance_uuid: {instance_uuid!r}, shutdown_at: {shutdown_at!r}")
                        autodl_client.update_instance_shutdown(instance_uuid, shutdown_at)
                    instance_name = f'{machine["region_name"]} / {machine["machine_alias"]}' \
                                    f' ({machine["gpu_name"]}, {instance_uuid})'
                    logger.info(f"已创建实例：{instance_name}。"
                                f" Instance has been created: {instance_name}.")
                    created_instance_names.append(instance_name)
                except FailedError:
                    logger.error(f'{machine["region_name"]} {machine["machine_alias"]} {machine["gpu_name"]}'
                                 f' ({machine["machine_id"]})')
                    logger.error(f"使用以上机器创建实例时发生错误，跳过并继续..."
                                 f" An error occurred while creating the instance with the above machine,"
                                 f" skip and continue...")
            logger.debug(f"created_instance_names: {created_instance_names!r}")
            # 检查是否完成
            if len(created_instance_names) == instance_to_create_num:
                # 创建的实例达到要求的数量后，完成
                logger.info(f"{instance_to_create_num} 个实例创建完毕。"
                            f" {instance_to_create_num} requested instances are created.")
                after_finished(config, created_instance_names)
            else:
                # 否则等待指定时间后重试
                logger.debug(f"wait for next retry, config.retry_interval_seconds: {config.retry_interval_seconds!r}")
                time.sleep(config.retry_interval_seconds * 60)
                try_to_create_instances()


def get_help():
    return "开始蹲守。 Start waiting."


def add_arguments(parser):
    pass


def main():
    try_to_create_instances()
