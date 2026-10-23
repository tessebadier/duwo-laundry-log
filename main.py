import logging
import os
import time
import re

import mysql.connector
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="[%(levelname)s] %(asctime)s %(message)s", level=logging.INFO
)
logger = logging.getLogger("laundry-request.service")

email = os.getenv("EMAIL")
pwd = os.getenv("PWD")

# docker exec -t -i laundry-db /bin/bash -c "mysql -p"
# example
# use laundry_data;
# select * from scrape limit 10;
db = mysql.connector.connect(
    host="laundry-db", user="root", password="example", database="laundry_data"
)
cursor = db.cursor()


def get_machine_count(email, pwd):
    session = requests.Session()
    session.verify = "multiposs-nl-chain.pem"
    url = "https://duwo2.multiposs.nl/login/submit.php"
    data = {"UserInput": email, "PwdInput": pwd}
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://duwo2.multiposs.nl",
        "Connection": "keep-alive",
        "Referer": "https://duwo2.multiposs.nl/login/index.php",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=4",
    }

    # get a session cookie by authentificating
    logger.info("POST to login")
    response = session.post(url, headers=headers, data=data)
    assert response.status_code == 200
    ID = str(response.content).split("ID=")[1][:21]
    assert ID

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://duwo2.multiposs.nl",
        "Connection": "keep-alive",
        "Referer": "https://duwo2.multiposs.nl/index.html",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=4",
    }
    logger.info("StartSite.php...")
    response = session.get(
        f"https://duwo2.multiposs.nl/StartSite.php?ID={ID}&UserID={email}",
        headers=headers,
    )
    assert response.status_code == 200

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://duwo2.multiposs.nl",
        "Connection": "keep-alive",
        "Referer": "https://duwo2.multiposs.nl/main.php",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    logger.info("MachineAvailability.php...")
    response = session.get(
        "https://duwo2.multiposs.nl/MachineAvailability.php", headers=headers
    )
    response.raise_for_status()
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    washing_count = dryer_count = 0
    for row in soup.select("#MachineAvailabilityTable tr"):
        tds = row.find_all("td")
        if len(tds) != 3:
              continue  # header row
        machine = tds[1].get_text(strip=True).lower()
        # e.g. <p class='TxtAvailable'>2 available</p>; absent when none are free
        available = tds[2].find("p", class_="TxtAvailable")
        if available is None:
            continue
        match = re.search(r"\d+", available.get_text(strip=True))
        count = int(match.group()) if match else 0
        if machine.startswith("washing"):
            washing_count = count
        elif machine.startswith("dryer"):
            dryer_count = count

    return washing_count, dryer_count


while True:
    try:
        w, d = get_machine_count(email, pwd)
        logger.info(f"Response: {w}, {d}")
        cursor.execute(f"INSERT INTO scrape (washing, dryer) VALUES ({w}, {d})")
        db.commit()
        logger.info("Wrote data")
    except KeyboardInterrupt:
        break
    except Exception as e:
        logger.info(e)
    logger.info("Sleeping for 600s")
    time.sleep(600)
