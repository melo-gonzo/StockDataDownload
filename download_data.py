import argparse
import datetime
import multiprocessing
import os
import time
from pathlib import Path

import yfinance as yf
import pandas as pd
from tqdm import tqdm


def get_now_epoch():
    """Get current timestamp as epoch"""
    return int(time.time())


def download_ticker_data(
    symbol,
    start_date=None,
    end_date=None,
    csv_location="./",
    append_to_file=False,
    verbose=True,
):
    """
    Download historical data for a single ticker using yfinance

    Args:
        symbol: Stock ticker symbol
        start_date: Start date (epoch timestamp or datetime string)
        end_date: End date (epoch timestamp or datetime string)
        csv_location: Directory to save CSV files
        append_to_file: Whether to append to existing file
        verbose: Print status messages

    Returns:
        bool: True if successful, False otherwise
    """
    filename = Path(csv_location) / f"{symbol}.csv"

    try:
        # Create ticker object
        ticker = yf.Ticker(symbol)

        # Convert epoch timestamps to datetime strings if needed
        if start_date:
            if isinstance(start_date, (int, float)):
                start_date = datetime.datetime.fromtimestamp(start_date).strftime(
                    "%Y-%m-%d"
                )
        else:
            start_date = "1900-01-01"  # Default to very early date

        if end_date:
            if isinstance(end_date, (int, float)):
                end_date = datetime.datetime.fromtimestamp(end_date).strftime(
                    "%Y-%m-%d"
                )
        else:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Download historical data
        if verbose:
            print(f"Downloading {symbol} from {start_date} to {end_date}")

        hist_data = ticker.history(start=start_date, end=end_date)

        if hist_data.empty:
            if verbose:
                print(f"No data found for {symbol}")
            return False

        # Prepare data for saving
        hist_data.index = hist_data.index.strftime("%Y-%m-%d")
        hist_data.index.name = "Date"

        # Reset index to make Date a column (to match original format)
        hist_data = hist_data.reset_index()

        if append_to_file and filename.exists():
            # Read existing data
            try:
                existing_data = pd.read_csv(filename)
                # Combine data and remove duplicates
                combined_data = pd.concat([existing_data, hist_data]).drop_duplicates(
                    subset=["Date"]
                )
                combined_data = combined_data.sort_values("Date")
                combined_data.to_csv(filename, index=False)
            except Exception as e:
                if verbose:
                    print(f"Error appending data for {symbol}: {e}")
                # If append fails, save as new file
                hist_data.to_csv(filename, index=False)
        else:
            # Save new file
            hist_data.to_csv(filename, index=False)

        if verbose:
            print(f"{symbol} download successful")
        return True

    except Exception as e:
        if verbose:
            print(f"Error downloading {symbol}: {str(e)}")
        return False


def process_single_ticker(args_tuple):
    """Wrapper function for multiprocessing"""
    (
        symbol,
        start_date,
        end_date,
        csv_location,
        append_to_file,
        verbose,
        list_location,
    ) = args_tuple

    # Check if file exists and determine if we need to append
    filename = Path(csv_location) / f"{symbol}.csv"

    if filename.exists() and filename.stat().st_size > 1000:
        # File exists and has reasonable size, try to append new data
        try:
            existing_data = pd.read_csv(filename)
            if not existing_data.empty and "Date" in existing_data.columns:
                last_date = existing_data["Date"].iloc[-1]
                start_date = int(
                    datetime.datetime.strptime(last_date, "%Y-%m-%d").timestamp()
                )
                append_to_file = True
        except Exception:
            # If we can't read the existing file, download from scratch
            append_to_file = False
            start_date = None
    else:
        # File doesn't exist or is too small
        append_to_file = False
        start_date = None

    success = download_ticker_data(
        symbol, start_date, end_date, csv_location, append_to_file, verbose
    )

    # Log results if list_location is provided
    if list_location:
        if success:
            completed_file = Path(list_location).stem + "_completed_list.txt"
            with open(completed_file, "a") as f:
                f.write(f"{symbol}\n")
        else:
            failed_file = Path(list_location).stem + "_failed_list.txt"
            with open(failed_file, "a") as f:
                f.write(f"{symbol}\n")

    return success


def gather_tickers(ticker_file):
    """Read tickers from file"""
    with open(ticker_file, "r") as f:
        tickers = [line.strip() for line in f if line.strip()]
    return tickers


def download_parallel_quotes(symbols, args):
    """Download quotes in parallel"""
    csv_location = args.csv_location
    verbose = args.verbose
    list_location = args.ticker_location
    end_date = get_now_epoch()

    # Initialize log files
    if list_location:
        completed_file = Path(list_location).stem + "_completed_list.txt"
        failed_file = Path(list_location).stem + "_failed_list.txt"

        # Clear existing log files
        with open(completed_file, "w") as _:
            pass
        with open(failed_file, "w") as _:
            pass

    # Prepare arguments for multiprocessing
    args_list = [
        (symbol, None, end_date, csv_location, False, verbose, list_location)
        for symbol in symbols
    ]

    if args.num_workers == 1:
        # Sequential processing
        for args_tuple in tqdm(args_list, desc="Downloading tickers"):
            process_single_ticker(args_tuple)
    else:
        # Parallel processing
        num_workers = (
            multiprocessing.cpu_count() if args.num_workers == -1 else args.num_workers
        )

        with multiprocessing.Pool(processes=num_workers) as pool:
            list(
                tqdm(
                    pool.imap(process_single_ticker, args_list),
                    total=len(args_list),
                    desc="Downloading tickers",
                )
            )


def add_tickers(args):
    """Add new tickers to the list and download their data"""
    # Read existing tickers
    if os.path.exists(args.ticker_location):
        with open(args.ticker_location, "r") as f:
            existing_tickers = [line.strip() for line in f if line.strip()]
    else:
        existing_tickers = []

    # Parse new tickers
    new_tickers = [t.strip() for t in args.add_tickers.split(",") if t.strip()]
    new_tickers = [t for t in new_tickers if t not in existing_tickers]

    if not new_tickers:
        print("No new tickers to add")
        return

    # Download data for new tickers
    print(f"Adding {len(new_tickers)} new tickers: {', '.join(new_tickers)}")

    for symbol in tqdm(new_tickers, desc="Downloading new tickers"):
        download_ticker_data(
            symbol, csv_location=args.csv_location, verbose=args.verbose
        )

    # Update ticker list
    all_tickers = sorted(list(set(existing_tickers + new_tickers)))
    with open(args.ticker_location, "w") as f:
        f.write("\n".join(all_tickers))

    print(f"Added {len(new_tickers)} tickers to {args.ticker_location}")


def remove_tickers(args):
    """Remove tickers from the list and delete their CSV files"""
    if not os.path.exists(args.ticker_location):
        print("Ticker file does not exist")
        return

    # Read existing tickers
    with open(args.ticker_location, "r") as f:
        existing_tickers = [line.strip() for line in f if line.strip()]

    # Parse tickers to remove
    remove_list = [t.strip() for t in args.remove_tickers.split(",") if t.strip()]

    # Remove from list
    remaining_tickers = [t for t in existing_tickers if t not in remove_list]

    # Update ticker file
    with open(args.ticker_location, "w") as f:
        f.write("\n".join(sorted(remaining_tickers)))

    # Remove CSV files
    csv_location = Path(args.csv_location)
    removed_count = 0

    for ticker in remove_list:
        csv_file = csv_location / f"{ticker}.csv"
        if csv_file.exists():
            csv_file.unlink()
            removed_count += 1

    print(f"Removed {len(remove_list)} tickers from list and {removed_count} CSV files")


def create_argument_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Stock Market Ticker Downloader using yfinance"
    )

    parser.add_argument(
        "--ticker_location",
        default="./tickers.txt",
        help="Path to text file containing list of tickers (one per line)",
    )

    parser.add_argument(
        "--csv_location", default="./csv_files/", help="Directory to save CSV files"
    )

    parser.add_argument(
        "--add_tickers",
        default="",
        type=str,
        help="Add tickers to list and download data. Format: 'AAPL' or 'AAPL,GOOGL,TSLA'",
    )

    parser.add_argument(
        "--remove_tickers",
        default="",
        type=str,
        help="Remove tickers from list and delete CSV files. Format: 'AAPL' or 'AAPL,GOOGL,TSLA'",
    )

    parser.add_argument(
        "--multitry", default=True, type=bool, help="Retry downloading failed tickers"
    )

    parser.add_argument(
        "--num_workers",
        default=-1,
        type=int,
        help="Number of parallel workers (-1 for all CPU cores, 1 for sequential)",
    )

    parser.add_argument(
        "--verbose", default=True, type=bool, help="Print download status messages"
    )

    return parser


def check_arguments(args):
    """Validate command line arguments"""
    # Create CSV directory if it doesn't exist
    csv_path = Path(args.csv_location)
    csv_path.mkdir(parents=True, exist_ok=True)

    # Create ticker file if it doesn't exist
    ticker_path = Path(args.ticker_location)
    if not ticker_path.exists():
        ticker_path.parent.mkdir(parents=True, exist_ok=True)
        ticker_path.touch()
        print(f"Created empty ticker file: {ticker_path}")


def retry_failed_downloads(args):
    """Retry downloading tickers that failed in the previous attempt"""
    failed_file = Path(args.ticker_location).stem + "_failed_list.txt"

    if not os.path.exists(failed_file):
        print("No failed downloads to retry")
        return

    with open(failed_file, "r") as f:
        failed_tickers = [line.strip() for line in f if line.strip()]

    if not failed_tickers:
        print("No failed downloads to retry")
        return

    print(f"Retrying {len(failed_tickers)} failed downloads")

    # Remove failed tickers from main list first
    args.remove_tickers = ",".join(failed_tickers)
    remove_tickers(args)

    # Try downloading again
    download_parallel_quotes(failed_tickers, args)


def main():
    """Main function"""
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        check_arguments(args)

        if args.add_tickers:
            add_tickers(args)
        elif args.remove_tickers:
            remove_tickers(args)
        else:
            # Download all tickers from the list
            if not os.path.exists(args.ticker_location):
                print(f"Ticker file {args.ticker_location} does not exist")
                print("Use --add_tickers to add some tickers first")
                return

            tickers = gather_tickers(args.ticker_location)
            if not tickers:
                print("No tickers found in ticker file")
                print("Use --add_tickers to add some tickers first")
                return

            print(f"Downloading data for {len(tickers)} tickers")
            download_parallel_quotes(tickers, args)

            if args.multitry:
                retry_failed_downloads(args)

    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
