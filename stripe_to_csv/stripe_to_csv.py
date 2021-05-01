from datetime import date, datetime
import os
import csv
from decimal import Decimal

import dateparser
import stripe
TWO_PLACES = Decimal('0.01')


def get_dates(start=None, end=None):
    # set the time to 0:00
    min_time = {'hour': 0,
                'minute': 0,
                'second': 0,
                'microsecond': 0}

    # set default dates
    now = datetime.today()
    start_of_month = now.replace(day=1, **min_time)

    # create start and end date - default to start of month -> now
    start = dateparser.parse(start) if start else start_of_month
    end = dateparser.parse(end) if end else now

    return start, end


def set_stripe_api_key(stripe_api_key=None):
    # attach Stripe API key
    stripe.api_key = stripe_api_key


def get_transactions(currency='USD', start=None, end=None):
    """Get a list of Stripe transactions"""

    # call Stripe, and get transactions
    results = stripe.BalanceTransaction.list(
        currency=currency,
        created={
            'gte': int(start.timestamp()),
            'lt': int(end.timestamp()),
        }
    )

    # return start, end and results
    return results


def get_charges(start=None, end=None):
    # call Stripe, and get transactions
    results = stripe.Charge.list(
        created={
            'gte': int(start.timestamp()),
            'lt': int(end.timestamp()),
        }
    )
    return results


def get_refunds(start=None, end=None):
    # call Stripe, and get transactions
    results = stripe.Event.list(
        created={
            'gte': int(start.timestamp()),
            'lt': int(end.timestamp()),
        },
        type='charge.refunded'
    )
    return results


def write_csv_file(file, start, end, currency, transactions=None, charges=None, refunds=None):
    """Write results file to .csv"""

    # set default file name
    start_formatted = start.strftime('%Y_%m_%d')
    end_formatted = end.strftime('%Y_%m_%d')
    file = file or "output/{}-{}-{}.csv".format(
        currency, start_formatted, end_formatted
    )

    # create dir if it doesn't already exist
    dirname = os.path.dirname(file)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

    try:
        open(file, 'r')
        print("File %s already exists!", file)
        raise FileExistsError
    except FileNotFoundError:
        pass

    # open the file as writable
    with open(file, 'w', newline='') as csvfile:

        rows = {}
        # cycle through transactions
        for transaction in transactions.auto_paging_iter():
            if transaction['type'] == 'payout_failure':
                continue

            # Xero format for dates
            created = date.fromtimestamp(transaction['created']).strftime('%d/%m/%y')

            # transaction amount
            transaction_amount = Decimal(transaction['amount'] / 100).quantize(TWO_PLACES)

            reference = transaction['source'] if transaction['source'] else transaction['id']
            rows[reference] = {
                '*Date': created,
                '*Amount': transaction_amount,
                'Payee': '',
                'Description': transaction['description'],
                'Reference': reference,
                'Timestamp': datetime.fromtimestamp(transaction['created']).isoformat(),
            }

            # cycle through fees and create separate rows
            fee_count = 0
            for fee in transaction.fee_details:
                fee_count += 1
                # fee amount
                fee_amount = -Decimal(fee['amount'] / 100).quantize(TWO_PLACES)

                reference = transaction['id'] + '-fee-' + str(fee_count)
                rows[reference] = {
                    '*Date': created,  # same date
                    '*Amount': fee_amount,
                    'Payee': '',
                    'Description': fee['description'],
                    'Reference': transaction['id'],
                    'Timestamp': datetime.fromtimestamp(transaction['created']).isoformat(),
                }

        for charge in charges.auto_paging_iter():
            idnum = charge['id']
            if idnum in rows:
                if 'name' in charge['source']:
                    rows[idnum]['Payee'] = charge['source']['name']

        for refund in refunds.auto_paging_iter():
            idnum = refund['data']['object']['refunds']['data'][0]['id']
            if idnum in rows:
                rows[idnum]['Payee'] = refund['data']['object']['source']['name']

        # create CSV writer, with column names
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                '*Date',
                '*Amount',
                'Payee',
                'Description',
                'Reference',
                'Timestamp',
            ]
        )

        # write header
        writer.writeheader()

        # and finally, write all the rows
        writer.writerows(rows.values())

    #  done!
    print("written to {}".format(file))
