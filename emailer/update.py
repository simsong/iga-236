import os
import collections
import boto3
from boto3.dynamodb.conditions import Key
from aws_lambda_powertools import Logger
import copy
import csv
import argparse
from pathlib import Path

dynamodb  = boto3.resource("dynamodb", region_name=os.getenv('AWS_REGION'))
table     = dynamodb.Table(os.getenv("TABLE_NAME","iga236-guids"))


def queryscan_table(what, kwargs):
    """Query or Scan a DynamoDB table, returning all matching items.
    :param what:  should be users_table.scan, users_table.query, etc.
    :param kwargs: should be the args that are used for the query or scan.
    """
    kwargs = copy.copy(kwargs)  # it will be modified
    items = []
    while True:
        response = what(**kwargs)
        items.extend(response.get('Items',[]))
        lek = response.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
    return items

def scan():
    for rec in queryscan_table(table.scan, {}):
        print(rec)


def update(path):
    guids = {}
    with path.open() as f:
        for row in csv.reader(f):
            (email,guid,keylen,asize) = row
            guids[guid] = row
    for rec in queryscan_table(table.scan, {}):
        if rec['guid'] in guids and 'email' not in rec:
            print("update",rec)
            (email,guid,keylen,asize) = guids[rec['guid']]
            table.update_item( Key={'guid':guid, 'sk':rec['sk']},
                               UpdateExpression="SET email=:email, keylen=:keylen, asize=:asize",
                               ExpressionAttributeValues = {':email':email,':keylen':keylen,':asize':asize})

def stats():
    hist = collections.defaultdict(int)
    for rec in queryscan_table(table.scan, {}):
        hist[rec.get('email','?')] += 1
    for (k,v) in sorted(hist.items()):
        print(k,v)

def main():
    parser = argparse.ArgumentParser(description='License Plate CLI tester',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--scan",action='store_true')
    parser.add_argument("--update",type=Path)
    args = parser.parse_args()
    if args.scan:
        scan()
    if args.update:
        update(args.update)
    stats()

if __name__=="__main__":
    main()
