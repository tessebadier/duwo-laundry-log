# what is this

2-evening-long project to log the number of available laundry machines in my building. very basic scraping of the website, and a very basic front end to see the numbers. might add better views if I'm bored again. 

# Requirements

docker installed on the system

# Install

setup your credentials in your .env file (in clear I know :s)
```
EMAIL=email@email.com
PWD=Swordfish
```

run a `docker compose --build` at the root of repo. add a `-d` to run in the background. 

The init.sql doesn't seem to be running with my current setup, enter the sql container with `docker exec -t -i laundry-db /bin/bash -c "mysql -p"` and manually run the contents of `init.sql`.

# other

Python formatted with ruff

The certificate is the chain certificate of the website downloaded from my browswer (firefox) (from 15/12/2025)

`main.py` loops indefinitely to query the number of machines available and stores them. `dashboard.py` is the very half assed front end. 

To access the sql container:
`docker exec -t -i laundry-db /bin/bash -c "mysql -p"` 
type in password 'example'

```sql
use laundry_data;
select * from scrape limit 10;
-- average per hour example query
select hour(CONVERT_TZ(scrape_ts, 'UTC', 'Europe/Amsterdam')) "hour", avg(washing) "washing", avg(dryer) "dryer" from scrape group by hour;
```
