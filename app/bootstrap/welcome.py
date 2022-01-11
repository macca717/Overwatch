from app.datastructures import AppConfig

SOLID_HORIZONTAL = "\u2501"
SOLID_VERTICAL = "\u2503"
TOP_LEFT = "\u250F"
TOP_RIGHT = "\u2513"
BOTTOM_LEFT = "\u2517"
BOTTOM_RIGHT = "\u251B"
LEFT_JOIN = "\u2523"
RIGHT_JOIN = "\u252B"

WIDTH = 60

SOLID_LINE = f"{LEFT_JOIN}{SOLID_HORIZONTAL * WIDTH}{RIGHT_JOIN}"


def print_welcome(config: AppConfig):
    title = "OVERWATCH SEIZURE DETECTOR"
    version = " Version: 0.1.0"
    websocket_port = f" Websocket Server Port: {config.server.websocket_port}"
    webserver_port = f" Web Server Port: {config.server.webserver_port}"

    print(f"{TOP_LEFT}{SOLID_HORIZONTAL * WIDTH}{TOP_RIGHT}")
    print(f"{SOLID_VERTICAL}{title.center(WIDTH)}{SOLID_VERTICAL}")
    print(SOLID_LINE)
    print(f"{SOLID_VERTICAL}{version:<{WIDTH}}{SOLID_VERTICAL}")
    print(SOLID_LINE)
    print(f"{SOLID_VERTICAL}{websocket_port:<{WIDTH}}{SOLID_VERTICAL}")
    print(SOLID_LINE)
    print(f"{SOLID_VERTICAL}{webserver_port:<{WIDTH}}{SOLID_VERTICAL}")
    print(f"{BOTTOM_LEFT}{SOLID_HORIZONTAL * WIDTH}{BOTTOM_RIGHT}")
