"""Telemetry Agent entrypoint."""

from telemetry_agent.parser.cli import main as parser_main


def main() -> None:
    parser_main()


if __name__ == "__main__":
    main()
