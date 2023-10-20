import requests
import json
import utils
import time
import sqlite3
from selenium import webdriver

user_prompt = int(input("Choose an option from the following: (By number)\n1) Parse\n2) View Flippable Cars from Database\n3) Clear Database\n"))


if user_prompt == 1:
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    #===================== GLOBAL VARIABLES ====================#
    websites = settings['websites']
    radius = settings['radius']
    zipcode = settings['zipcode']
    resultsPerPage = settings['resultsPerPage']
    tokens = settings['tokens']
    #============================================================#

    # Create an instance of Chrome WebDriver
    driver = webdriver.Chrome()

    db_connection = sqlite3.connect('vehicles.db')
    db = db_connection.cursor()
    db.execute('''CREATE TABLE IF NOT EXISTS cars
                (vin TEXT PRIMARY KEY,
                err BOOL, 
                car_title TEXT, 
                price REAL,
                est_price REAL, 
                mileage REAL, 
                details TEXT,
                url TEXT)''')

    for website, token in zip(websites, tokens):
        page_number = 0
        while True:
            page_number+=1
            url = f"https://www.autotempest.com/queue-results?radius={radius}&originalradius={radius}&zip={zipcode}&sort=price_asc&sites={website}&deduplicationSites=te%7Ccm%7Ccs%7Ccv%7Ceb%7Ctc%7Cot%7Cfbm%7Cst&rpp={resultsPerPage}&page={page_number}&token={token}"
            response = requests.get(url).json()
            if response.get("status", None) == -2: break #Check if this page doesn't exist
            data = response.get("results", None)
            if not data: 
                print("Failed to retrieve results")
                continue
            for result in data:
                vin = result['vin']
                #Check for vin in Database, if found then continue
                if utils.vinExists(db, vin): continue
                name = result['title']
                list_price = int(result['price'].replace('$', '').replace(',', ''))
                car_url = result['url']
                if result.get("details", None):
                    desc = result['details']
                elif result.get("detailsShort", None) and result.get("detailsMid") and result.get("detailsLong", None):
                    desc = result['detailsShort'] + result['detailsMid'] + result['detailsLong']
                res = utils.getVehicleEstimate(vin, desc, driver)
                if res: 
                    print(res, list_price, name)
                    est_price, odometer, condition = res
                    utils.appendToDB(db, db_connection, (vin, False, name, list_price, est_price, odometer, desc, car_url))
                else:
                    utils.appendToDB(db, db_connection, (vin, True, None, None, None, None, None, car_url))
    db_connection.close()

elif user_prompt == 2:
    #TODO Add the logic to distinguish a good flippable car
    rows = utils.loadDB()
    for row in rows:
        price, estimate, mileage = row[3], row[4], row[5]
        
elif user_prompt == 3:
    validate = input("Are you sure you want to clear the Database? (Type: I agree)\n*")
    if validate == "I agree":
        # Connect to the database
        conn = sqlite3.connect('vehicles.db')
        cursor = conn.cursor()

        # Clear the 'cars' table
        cursor.execute("DELETE FROM cars")
        conn.commit()

        # Close the connection
        conn.close()
        print("Database Cleared Successfully")
    else:
        print("Database not cleared")