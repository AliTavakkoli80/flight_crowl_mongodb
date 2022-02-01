# written by AmirHossein Mahmoodnia and Ali Tavakkoli
import requests
from bs4 import BeautifulSoup
import pymongo


def scrape_flights():
    flights = []
    markup = requests.get(f'https://sacramento.aero/smf/flight-and-travel/flight-status').text
    soup = BeautifulSoup(markup, 'html.parser')
    for item in soup.select('tbody>tr'):
        flight = {'first': item.select_one('td.first > div').get_text(),
                  'airline': item.select_one('td.airline > div').get_text(),
                  'from': item.select_one('td > div > a').get_text(),
                  'time': item.select_one('td.time > div').get_text(),
                  'status': item.select_one('td > div').get_text(),
                  'last': item.select_one('td.last > div').get_text()}
        flights.append(flight)
    return flights


flights = scrape_flights()
print(flights)
client = pymongo.MongoClient('mongodb://localhost:27017')
db = client.db.quotes
try:
    db.insert_many(flights)
    print(f'inserted {len(flights)} flights')
except:
    print('an error occurred quotes were not stored to db')

print("done")
