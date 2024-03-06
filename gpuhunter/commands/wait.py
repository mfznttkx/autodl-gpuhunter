import time
from datetime import timedelta, datetime
from functools import reduce

from gpuhunter.utils.helpers import end_of_day
from main import logger


def after_finished(config, created_instance_uuids=None):
    pass
    # if config.shutdown_hunter_after_finished:
    #     shutdown_current()


def try_to_create_instances():
    from gpuhunter.autodl_client import (
        autodl_client, resolve_image_info,
        get_running_instances, get_available_machines
    )
    from gpuhunter.data_object import Config, RegionList
    config = Config().load()
    region_list = RegionList().load()

    logger.info(f"尝试创建 {len(config.instance_num)} 个实例...")
    logger.info(f"Try to create {len(config.instance_num)} instances...")

    region_sign_list = reduce(
        lambda r, sl: r["region_sign"] + sl,
        [r for r in region_list if r["region_name"] in config.region_names], []
    )
    image_info = resolve_image_info(
        base_image_labels=config.base_image_labels,
        shared_image_keyword=config.shared_image_keyword,
        shared_image_username_keyword=config.shared_image_username_keyword,
        shared_image_version=config.shared_image_version,
        private_image_uuid=config.private_image_uuid,
        private_image_name=config.private_image_name
    )
    instances = get_running_instances(
        region_names=config.region_names,
        gpu_type_names=config.gpu_type_names,
        image=image_info["image"],
        private_image_uuid=image_info["private_image_uuid"],
        reproduction_uuid=image_info["reproduction_uuid"],
        reproduction_id=image_info["reproduction_id"]
    )
    instance_to_create_num = max(0, config.instance_num - len(instances))
    if instance_to_create_num == 0:
        logger.info(f"{len(instances)} 个符合要求的实例已经在运行。")
        logger.info(f"{len(instances)} requested instances are running.")
        after_finished(config)
    else:
        machines = get_available_machines(
            region_sign_list,
            config.gpu_type_names,
            gpu_idle_num=config.gpu_idle_num
        )
        if len(machines) == 0:
            logger.info(f"没有可用的 GPU 机器。")
            logger.info(f"No available machine.")
        else:
            created_instance_uuids = []
            for machine in machines[:instance_to_create_num]:
                instance_uuid = autodl_client.create_instance(
                    machine["machine_id"],
                    image_info["image"],
                    instance_name="😊🎁",
                    private_image_uuid=image_info["private_image_uuid"],
                    reproduction_uuid=image_info["reproduction_uuid"],
                    reproduction_id=image_info["reproduction_id"],
                    req_gpu_amount=config.gpu_idle_num,
                    expand_data_disk=config.expand_data_disk,
                    clone_instance_uuid=config.clone_instance_uuid,
                    copy_data_disk_after_clone=config.copy_data_disk_after_clone,
                    keep_src_user_service_address_after_clone=config.keep_src_user_service_address_after_clone,
                )
                shutdown_at = None
                if config.shutdown_instance_after_hours:
                    shutdown_at = datetime.now() + timedelta(hours=config.shutdown_instance_after_hours)
                elif config.shutdown_instance_today:
                    shutdown_at = end_of_day(datetime.now())
                if shutdown_at:
                    autodl_client.update_instance_shutdown(instance_uuid, shutdown_at)
                logger.info(f"已创建实例：{instance_uuid}")
                logger.info(f"Instance has been created: {instance_uuid}")
                created_instance_uuids.append(instance_uuid)
            if len(created_instance_uuids) == instance_to_create_num:
                logger.info(f"{len(config.instance_num)} 个实例创建完毕。")
                logger.info(f"{len(config.instance_num)} requested instances are running.")
                after_finished(config, created_instance_uuids)
            else:
                time.sleep(config.retry_interval_minutes * 60)
                try_to_create_instances()


def get_help():
    return "开始蹲守。 Start waiting."


def add_arguments(parser):
    parser.add_argument(
        "arg1",
        help="argument name",
    )


def main(arg1):
    from gpuhunter.autodl_client import autodl_client
    print([i["machine_id"] for i in autodl_client.list_instance(page_size=1)])
