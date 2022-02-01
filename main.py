# written by AmirHossein Mahmoodnia and Ali Tavakkoli

import csv
import datetime
import json

import requests
from pymongo import MongoClient
from pymongo.server_api import ServerApi


def response_from_flight(fly_from, fly_to, date_from, date_to, limit=10000):
    url = 'https://tequila-api.kiwi.com/v2/search'
    headers = {
        'accept': 'application/json',
        'apikey': 'TCsaXGYOuf3a4MHb6p9gGAnvuzbpUeV8',
    }
    params = (
        ('fly_from', fly_from),
        ('fly_to', fly_to),
        ('date_from', date_from),
        ('date_to', date_to),
        ('flight_type', 'oneway'),
        ('vehicle_type', 'aircraft'),
        ('limit', str(limit))
    )
    response = requests.get(url, headers=headers, params=params)
    return response


def exchange(from_, to):
    if from_ == to:
        return 1
    try:
        api_key = '6e047d199799e036a914e896'
        url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'
        response = requests.get(url)
        text = response.text
        json_out = json.loads(text)
        f = json_out['conversion_rates'][from_]
        t = json_out['conversion_rates'][to]
        if from_ == 'USD':
            return t
        if to == 'USD':
            return 1/f
        return t/f

    except KeyError:
        return 1


def change_curr_toUSD(json_file, rate):
    for el in json_file:
        el['price'] = rate*el['price']


def get_all_fly_in(day, collection):
    ls = []
    for doc in collection.find():
        d = doc['route'][0]['utc_arrival'][:10]
        if d == day:
            ls.append(doc)
    return ls


def search_by_cost_inUSD(cost_from, cost_to, collection):
    ls = []
    for doc in collection.find():
        d = doc['price']
        if d >= cost_from and d <= cost_to:
            ls.append(doc)
    return ls


def max_min_from_to(from_, to, collection):
    ls = []
    for doc in collection.find():
        c1 = doc["countryFrom"]["code"]
        n1 = doc["countryFrom"]["name"]
        c2 = doc["countryTo"]["code"]
        n2 = doc["countryTo"]["name"]
        if (c1 == from_ and c2 == to) or (n1 == from_ and n2 == to):
            ls.append(doc['price'])
    return (max(ls), min(ls))


def avg_sum_from_to(from_, to, collection):
    ls = []
    for doc in collection.find():
        c1 = doc["countryFrom"]["code"]
        n1 = doc["countryFrom"]["name"]
        c2 = doc["countryTo"]["code"]
        n2 = doc["countryTo"]["name"]
        if (c1 == from_ and c2 == to) or (n1 == from_ and n2 == to):
            ls.append(doc['price'])
    sum_ = sum(ls)
    len_ = len(ls)
    return (sum_/len_, sum_)


def get_all_by_fare_class(fare_class, day, collection):
    ls2 = []
    ls = get_all_fly_in(day, collection)
    for doc in ls:
        if doc['route'][0]["fare_classes"] == fare_class:
            ls2.append(doc)
    return ls2


def search_by_cost_and_fare_class(fare_class, cost_from, cost_to, collection):
    ls2 = []
    ls = search_by_cost_inUSD(cost_from, cost_to, collection)
    for doc in ls:
        if doc['route'][0]['fare_classes'] == fare_class:
            ls2.append(doc)
    return ls2


def min_max_from_to_by_fare_class(fare_class, from_, to, collection):
    ls = []
    for doc in collection.find():
        c1 = doc["countryFrom"]["code"]
        n1 = doc["countryFrom"]["name"]
        c2 = doc["countryTo"]["code"]
        n2 = doc["countryTo"]["name"]
        if (doc['route'][0]["fare_classes"] == fare_class) and \
                ((c1 == from_ and c2 == to) or (n1 == from_ and n2 == to)):
            ls.append(doc['price'])
    return(min(ls), max(ls))


def avg_sum_from_to_by_fare_class(fare_class, from_, to, collection):
    ls = []
    for doc in collection.find():
        c1 = doc["countryFrom"]["code"]
        n1 = doc["countryFrom"]["name"]
        c2 = doc["countryTo"]["code"]
        n2 = doc["countryTo"]["name"]
        if (doc['route'][0]["fare_classes"] == fare_class) and \
                ((c1 == from_ and c2 == to) or (n1 == from_ and n2 == to)):
            ls.append(doc['price'])
    sum_ = sum(ls)
    len_ = len(ls)
    return (sum_/len_, sum_)


def from_to_cost_range_cheapest(from_, to, cost_from, cost_to, collection):
    ls = []
    cheapest_flight = None
    cheapest_cost = 100000000
    for doc in collection.find():
        c1 = doc['countryFrom']['code']
        n1 = doc['countryFrom']['name']
        c2 = doc['countryTo']['code']
        n2 = doc['countryTo']['name']
        d = doc['price']
        if ((c1 == from_ and c2 == to) or (n1 == from_ and n2 == to)) and \
                (d >= cost_from and d <= cost_to):
            ls.append(doc)
        if d < cheapest_cost:
            cheapest_flight = doc
            cheapest_cost = d
    return (cheapest_flight, ls)


ff = []
with open('co.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['Name'] != "Iran, Islamic Republic of":
            ff.append(row['Code'])
ff = ','.join(ff)

now = datetime.date.today()
now_str = now.strftime("%d/%m/%Y")
next_7 = (now + datetime.timedelta(days=7)).strftime("%d/%m/%Y")

r1 = response_from_flight('IR', ff, now, next_7)
r2 = response_from_flight(ff, 'IR', now, next_7)

json1 = json.loads(r1.text)
json2 = json.loads(r2.text)
cur1 = json1['currency']
cur2 = json2['currency']
if cur1 != 'USD':
    change_curr_toUSD(json1['data'], exchange(cur1, 'USD'))
if cur2 != 'USD':
    change_curr_toUSD(json2['data'], exchange(cur1, 'USD'))
ls1 = json1['data']
ls2 = json2['data']


try:
    conn_str = "mongodb://localhost:27017"
    client = MongoClient(conn_str, server_api=ServerApi('1'),
                         serverSelectionTimeoutMS=5000)
    print(client.server_info())
except Exception:
    print('Unable to connect to the server.')

db = client['flight-db']
collection = db['flight-collect']
collection.insert_many(ls1)
collection.insert_many(ls2)
# print(get_all_fly_in('2022-02-02', collection))
# print(search_by_cost_inUSD(10, 100, collection))
# print(max_min_from_to('TR', 'IR', collection))
# print(avg_sum_from_to('TR', 'IR', collection))

#     Y: Full-fare economy-class ticket.
#     J: Full-fare business-class ticket.
#     F: Full-fare first-class ticket.
#     F and A: first class.
#     C, J, R, D and I: business class.
#     W and P: premium economy.
#     Y, H, K, M, L, G, V, S, N, Q, O and E: economy.
#     B: basic economy.

# print(get_all_by_fare_class('G', '2022-02-02', collection))
# print(search_by_cost_and_fare_class('G', 10, 100, collection))
# print(min_max_from_to_by_fare_class('G', 'TR', 'IR', collection))
# print(avg_sum_from_to_by_fare_class('G', 'IR', 'TR', collection))
print(from_to_cost_range_cheapest('IR', 'TR', 10, 100, collection))
