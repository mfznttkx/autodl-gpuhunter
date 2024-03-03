from gpuhunter.config import Config


def get_help():
    return ""


def add_arguments(parser):
    parser.add_argument(
        "arg1",
        help="argument name",
    )


def main(arg1):
    c = Config(token="asdfasdfafs")
    c.save()

