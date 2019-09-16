import argparse
import stripe_to_csv


if __name__ == "__main__":
    """Get Stripe transactions on CLI args"""

    # create CLI args
    parser = argparse.ArgumentParser()

    # API key
    parser.add_argument(
        '-k',
        '--api-key',
        help='Stripe API key',
        required=True
    )

    parser.add_argument(
        '-c',
        '--currency',
        default='USD',
        help='Currency'
    )

    parser.add_argument(
        '-s',
        '--start',
        help='Transaction start date'
    )
    parser.add_argument(
        '-e',
        '--end',
        help='Transaction end date'

    )
    parser.add_argument(
        '-o',
        '--output',
        help='Output file name'
    )

    # parse arguments
    args = parser.parse_args()

    stripe_to_csv.set_stripe_api_key(args.api_key)
    start, end = stripe_to_csv.get_dates(args.start, args.end)

    # retrieve Stripe transactions
    transactions = stripe_to_csv.get_transactions(
        currency=args.currency,
        start=start,
        end=end,
    )

    charges = stripe_to_csv.get_charges(
        start=start,
        end=end,
    )

    refunds = stripe_to_csv.get_refunds(
        start=start,
        end=end,
    )

    # write to .csv file
    stripe_to_csv.write_csv_file(
        file=args.output,
        start=start,
        end=end,
        currency=args.currency,
        transactions=transactions,
        charges=charges,
        refunds=refunds
    )
