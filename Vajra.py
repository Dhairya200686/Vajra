#!/usr/bin/env python3
# VAJRA (वज्र) v2.3 — Universal Technical Intelligence CLI
# Entry point — thin dispatcher only. All logic lives in modules.

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from cli.args        import build_parser
from cli.handlers    import (
    handle_query, handle_file_query, handle_set_model,
    handle_list_models, handle_sysinfo, handle_service,
    handle_library, handle_ask, handle_run, handle_audit,
)
from cli.session_ui  import run_session


def main():
    parser = build_parser()
    args   = parser.parse_args()

    if args.list_models:
        handle_list_models()
        return

    if args.set_model:
        handle_set_model(args.set_model)
        return

    if args.session:
        run_session(mode=args.mode, model=args.model, load_file=args.load)
        return

    if not args.args:
        from cli.display import print_banner
        print_banner()
        parser.print_help()
        print()
        return

    cmd = args.args[0].lower()

    if cmd == "read":
        handle_file_query(
            args.args[1:], mode=args.mode,
            model=args.model, outfile=args.output)
        return

    if cmd == "sysinfo":
        question = " ".join(args.args[1:]) if len(args.args) > 1 else None
        handle_sysinfo(question=question, model=args.model)
        return

    if cmd == "service" and len(args.args) > 1:
        handle_service(" ".join(args.args[1:]))
        return

    if cmd == "library":
        handle_library(args.args[1:])
        return

    if cmd == "ask":
        handle_ask(
            " ".join(args.args[1:]), source_mode=args.source_mode,
            model=args.model, outfile=args.output)
        return

    if cmd == "run":
        handle_run(" ".join(args.args[1:]))
        return

    if cmd == "audit":
        handle_audit()
        return

    handle_query(
        " ".join(args.args), mode=args.mode,
        model=args.model, outfile=args.output)


if __name__ == "__main__":
    main()
