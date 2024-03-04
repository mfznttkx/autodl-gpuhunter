def get_help():
    return "开始蹲守。 Start waiting."


def add_arguments(parser):
    parser.add_argument(
        "arg1",
        help="argument name",
    )


def main(arg1):
    from gpuhunter.data_object import RegionList
    d = RegionList()
    d.load()
    # d.update()

    print(d.get_gpu_stats())
    print(d.get_region_stats())

