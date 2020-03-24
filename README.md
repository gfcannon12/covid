# COVID-19 Growth Tables and Charts

http://graycannon.com/covid_tables.html

## Purpose
Many great dashboards exist for data related to COVID-19. This dashboard aims to specifically call out growth rates and growth factors for easy analysis.

#### Data compiled by Johns Hopkins University
https://github.com/CSSEGISandData/COVID-19

#### Inspiration - Outstanding explanation by 3Blue1Brown
https://www.youtube.com/watch?v=Kas0tIxDvrg

## Update data locally
```
# Supply your own S3 credentials in env.sh
# S3 buckets receive the data as CSVs and charts and tables as HTML
pip install -r requirements.txt
source env.sh
python __main__.py
```

## Scheduled updates on IBM Cloud
IBM Cloud Function retrieves data and constructs charts with the latest information.

#### Python environment on Docker Hub - Feel free to use
```
cd docker_runtime
./buildAndPush.sh gfcannon12/covid-runtime-1
```

#### Deploying to IBM Cloud https://cloud.ibm.com/functions/
```
ibmcloud login
ibmcloud target -g Default
ibmcloud fn property set --namespace covid
zip covid.zip covid.py make_charts.py make_table.py s3_ops.py download.js __main__.py
ibmcloud fn action create UpdateCovid --docker gfcannon12/covid-runtime-1 covid.zip
ibmcloud fn trigger create hourly --feed /whisk.system/alarms/alarm --param cron "0 * * * *"
ibmcloud fn rule create hourly_covid_update hourly UpdateCovid
ibmcloud fn action update UpdateCovid --docker gfcannon12/covid-runtime-1 covid.zip
```

#### Invoke on IBM Cloud https://cloud.ibm.com/functions/triggers
```
# Add S3 creds as trigger parameters
ibmcloud fn trigger fire hourly
ibmcloud fn activation poll UpdateCovid
ibmcloud fn activation list UpdateCovid -f -l 1 
```
