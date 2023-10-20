import requests
import json
import openai
import sqlite3
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

with open('settings.json', 'r') as f:
    settings = json.load(f)

openai.api_key = "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"
    
def getVehicleEstimate(vin, desc, driver):
    url = 'https://www.carfax.com/value/'
    driver.get(url)
    zip_input = driver.find_element(By.NAME, "zip")
    zip_input.send_keys(settings['zipcode']) 
    vin_input = driver.find_element(By.NAME, "vin")
    vin_input.send_keys(vin)
    checkBox = driver.find_element(By.CLASS_NAME, "checkbox-input_box")
    checkBox.click()
    submit_button = driver.find_element(By.CLASS_NAME, "vehicle-input-form__input__submit")
    submit_button.click()
    time.sleep(2)

    #Check if the form was submitted successfully
    try:
        driver.find_element(By.CLASS_NAME,"vif__input--error")
        return False
    except: pass

    #Retrieve Results
    wait = WebDriverWait(driver, 10)  # Wait for a maximum of 10 seconds
    # Find the main container that holds the prices
    prices_container = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'results__prices__list')))
    #Get the condition from ChatGPT
    if desc: 
        prompt = [{"role": "system", "content": f"Tell me the condition of this car from only these conditions (Fair, Good, Excellent, Parts) where Fair means the car has cosmetic flaws and/or mechanical issues that may need to be repaired or replaced, 'Good' means the car has no major mechanical problems and only minor cosmetic flaws, 'Excellent' means the car is as good as new with no cosmetic or mechanical flaws and 'Parts' means the car is only listed for its parts, so it's not running. Here's the car's description: {desc}. If the description is empty or doesn't contain any flaws or doesn't say anything about the car, just put the condition as Excellent. your response message should ONLY contain (Fair, Good, Excellent, Parts), don't include anything else in your response"}]
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=prompt
        )
        reply = chat.choices[0].message.content
        condition = "Good"
        if "Fair" in reply: driver.find_element(By.ID, "condition-slider__custom-placeholder-1").click(); condition="Fair"
        elif "Excellent" in reply: driver.find_element(By.ID, "condition-slider__custom-placeholder-3").click(); condition="Excellent"
        elif "Parts" in reply: condition = "Parts"
        else: pass
    if condition in ["Fair", "Excellent"]: time.sleep(2.1)
    else: time.sleep(1)
    estimated_price = int(prices_container.find_element(By.CLASS_NAME, 'results__prices__list-item__price').text.replace('$', '').replace(',', ''))
    odometer = driver.find_element(By.NAME, "odometer").get_attribute("value")
    return (estimated_price, odometer, condition)


def vinExists(db, vin):
    # Check if the VIN exists in the database
    db.execute("SELECT * FROM cars WHERE vin=?", (vin,))
    row = db.fetchone()
    if row: return True  # Return the row if the VIN exists
    return False  # Return False if the VIN doesn't exist

def appendToDB(db, dbconn, data):
    db.execute("SELECT * FROM cars WHERE vin=?", (data[0],))
    if db.fetchone(): return
    query = "INSERT INTO cars (vin, err, car_title, price, est_price, mileage, details, url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    db.execute(query, data)
    dbconn.commit()

def loadDB():
    db_connection = sqlite3.connect("vehicles.db")
    db = db_connection.cursor()
    db.execute("SELECT * FROM cars WHERE err=0 AND price>1000 AND (price/est_price)<0.8")
    return db.fetchall()

def viewDB():
    db_connection = sqlite3.connect('vehicles.db')
    db = db_connection.cursor()
    db.execute("SELECT * FROM cars")
    rows = db.fetchall()

    # Print the data
    for row in rows:
        print(row)
    db.close()
    quit()