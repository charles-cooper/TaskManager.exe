import argparse

from taskman import core


def main() -> None:
    parser = argparse.ArgumentParser(prog="taskman")
    subparsers = parser.add_subparsers(dest="command")

    # Setup commands
    subparsers.add_parser("init")
    install_mcp = subparsers.add_parser("install-mcp")
    install_mcp.add_argument("agent", choices=["claude", "cursor", "codex"])
    subparsers.add_parser("install-skills")
    uninstall_mcp = subparsers.add_parser("uninstall-mcp")
    uninstall_mcp.add_argument("agent", choices=["claude", "cursor", "codex"])
    subparsers.add_parser("uninstall-skills")
    subparsers.add_parser("stdio")

    wt_parser = subparsers.add_parser("wt")
    wt_parser.add_argument("name", nargs="?", default=None,
                           help="worktree name (omit to just clone .agent-files in current dir)")

    # Operation commands
    desc = subparsers.add_parser("describe")
    desc.add_argument("reason")

    sy = subparsers.add_parser("sync")
    sy.add_argument("reason")

    hd = subparsers.add_parser("history-diffs")
    hd.add_argument("file")
    hd.add_argument("start_rev")
    hd.add_argument("end_rev", nargs="?", default="@")

    hb = subparsers.add_parser("history-batch")
    hb.add_argument("file")
    hb.add_argument("start_rev")
    hb.add_argument("end_rev", nargs="?", default="@")

    hs = subparsers.add_parser("history-search")
    hs.add_argument("pattern")
    hs.add_argument("--file", default=None)
    hs.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.command == "init":
        print(core.init())
    elif args.command == "wt":
        print(core.wt(args.name))
    elif args.command == "install-mcp":
        print(core.install_mcp(args.agent))
    elif args.command == "install-skills":
        print(core.install_skills())
    elif args.command == "uninstall-mcp":
        print(core.uninstall_mcp(args.agent))
    elif args.command == "uninstall-skills":
        print(core.uninstall_skills())
    elif args.command == "stdio":
        from taskman.server import main as server_main

        server_main()
    elif args.command == "describe":
        print(core.describe(args.reason))
    elif args.command == "sync":
        print(core.sync(args.reason))
    elif args.command == "history-diffs":
        print(core.history_diffs(args.file, args.start_rev, args.end_rev))
    elif args.command == "history-batch":
        print(core.history_batch(args.file, args.start_rev, args.end_rev))
    elif args.command == "history-search":
        print(core.history_search(args.pattern, args.file, args.limit))
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
