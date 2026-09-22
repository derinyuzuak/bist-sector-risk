import argparse
from .data import read_inputs
from .providers import fetch_evds, build_evds_macro
from .bist import prepare_bist_prices, assemble_study
from .yahoo import prepare_yahoo_prices


def main():
    parser = argparse.ArgumentParser(description="BIST sector risk research")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--data", required=True)
    validate.add_argument("--mode", choices=["research"], default="research")
    fetch = sub.add_parser("fetch-evds")
    fetch.add_argument("--series", nargs="+", required=True)
    fetch.add_argument("--start", default="01-12-2017")
    fetch.add_argument("--end", default="31-12-2024")
    fetch.add_argument("--out", default="data/private/evds")
    fetch.add_argument("--key-file", default="data/private/evds.key")
    macro = sub.add_parser("prepare-evds", help="Convert mapped EVDS raw data to macro.csv; does not create price data")
    macro.add_argument("--raw", default="data/private/evds-real")
    macro.add_argument("--out", default="data/private/study")
    bist = sub.add_parser("prepare-bist", help="Convert authorised BIST price-index ZIP/CSV files to prices.csv")
    bist.add_argument("--raw", required=True)
    bist.add_argument("--out", default="data/private/study-prices")
    yahoo = sub.add_parser("prepare-yahoo", help="Download verified Yahoo Finance BIST index closes as secondary source")
    yahoo.add_argument("--out", default="data/private/study-prices-yahoo")
    yahoo.add_argument("--start", default="2017-12-01")
    yahoo.add_argument("--end", default="2025-01-01")
    assembly = sub.add_parser("assemble-study", help="Combine prepared BIST price and EVDS macro inputs")
    assembly.add_argument("--prices", default="data/private/study-prices")
    assembly.add_argument("--macro", default="data/private/study-macro")
    assembly.add_argument("--out", default="data/private/study")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            read_inputs(args.data, args.mode)
            print("Input contracts and provenance valid. Run analysis for full coverage checks.")
        elif args.command == "fetch-evds":
            fetch_evds(args.series, args.start, args.end, args.out, args.key_file)
        elif args.command == "prepare-evds":
            build_evds_macro(args.raw, args.out)
        elif args.command == "prepare-bist":
            prepare_bist_prices(args.raw, args.out)
        elif args.command == "prepare-yahoo":
            prepare_yahoo_prices(args.out, args.start, args.end)
        else:
            assemble_study(args.prices, args.macro, args.out)
    except (ValueError, FileNotFoundError, KeyError) as exc:
        parser.exit(2, f"Input/configuration error: {exc}\n")


if __name__ == "__main__":
    main()
