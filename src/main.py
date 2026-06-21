"""Command-line entry point.

Examples:
  python -m src.main list                         # show available scenarios
  python -m src.main transcribe --demo            # offline demo (no API keys)
  python -m src.main serve                        # run the media server
  python -m src.main call sunday_closed_day       # place one test call
  python -m src.main transcribe --call-sid CAxxxx --index 3
  python -m src.main analyze                       # LLM first-pass bug report
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="patient-bot")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List available scenarios.")

    p_call = sub.add_parser("call", help="Place one test call for a scenario.")
    p_call.add_argument("scenario", help="Scenario id (see `list`).")

    sub.add_parser("serve", help="Run the FastAPI media server (uvicorn).")

    p_tx = sub.add_parser("transcribe", help="Build a transcript.")
    p_tx.add_argument("--demo", action="store_true", help="Offline demo, no API keys.")
    p_tx.add_argument("--call-sid", help="Twilio call SID to transcribe.")
    p_tx.add_argument("--index", type=int, default=1, help="Transcript number for filenames.")

    sub.add_parser("analyze", help="LLM first-pass bug report over all transcripts.")

    sub.add_parser("check", help="Preflight: verify credentials before calling.")

    sub.add_parser("finalize", help="Number transcripts + download recordings for all calls.")

    args = parser.parse_args(argv)

    if args.command == "list":
        from .scenarios import list_scenarios

        for sid in list_scenarios():
            print(sid)
        return 0

    if args.command == "call":
        from .dialer import place_call

        place_call(args.scenario)
        return 0

    if args.command == "serve":
        import uvicorn

        uvicorn.run("src.server:app", host="0.0.0.0", port=8000)
        return 0

    if args.command == "transcribe":
        from . import transcribe

        if args.demo:
            transcribe.demo()
        elif args.call_sid:
            transcribe.download_recording(args.call_sid, args.index)
        else:
            print("Pass --demo or --call-sid <sid>.", file=sys.stderr)
            return 2
        return 0

    if args.command == "finalize":
        from . import transcribe

        transcribe.finalize()
        return 0

    if args.command == "analyze":
        from .analyze import analyze_all

        analyze_all()
        return 0

    if args.command == "check":
        from .preflight import run

        return run()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
