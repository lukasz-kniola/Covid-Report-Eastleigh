import json
import requests
from datetime import datetime, timedelta

def read_in_area(areaName, params):
    url = "https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla&areaName="+ areaName + "&format=json"

    metrics = "".join(["&metric="+param["code"] for param in params.values()])

    print("Downloading data...")

    request = requests.get(url+metrics)
    data = request.json()['body']

    print(data[0]["areaName"] + " loaded.")

    return data

areaName = "Eastleigh"
params = {"cases":{"code":"cumCasesBySpecimenDate",
                   "label":"Cases", "dp":False, "chg_show":True, "colors":True}, 
          "deaths":{"code":"cumDeaths28DaysByDeathDate",
                   "label":"Deaths", "dp":False, "chg_show":True, "colors":True}, 
          "vacc1":{"code":"cumVaccinationFirstDoseUptakeByVaccinationDatePercentage",
                   "label":"1st Vaccine", "dp":True, "chg_show":False, "colors":False},
          "vacc2":{"code":"cumVaccinationSecondDoseUptakeByVaccinationDatePercentage",
                   "label":"2nd Vaccine", "dp":True, "chg_show":False, "colors":False},}

source = read_in_area(areaName, params)


# All days
fst_record = datetime.strptime("2020-01-01", '%Y-%m-%d')
lst_record = max([datetime.strptime(x["date"], '%Y-%m-%d') for x in source])
span = lst_record - fst_record
days = [(fst_record + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(span.days + 1)]

print("Last update: "+str(lst_record)[0:10])


# Table shell
data = {day: {param: -1 for param in params} for day in days}

# Update table with data
for x in source:
    for k,v in params.items():
      data[x["date"]][k] = x[v["code"]] if x[v["code"]] else 0

# LOCF
locf = {param: 0 for param in params.keys()}

for day in days:
	for param in params.keys():
		if data[day][param] == 0:
			data[day][param] = locf[param]
		else:
			locf[param] = data[day][param]


def offset(dtc, offset):
	return (datetime.strptime(dtc, '%Y-%m-%d') +
	        timedelta(days=offset)).isoformat()[:10]

def present(num,chg,dp,chg_show,colors):
    tx = f'{num:9.2f}' if dp else f'{num:9.0f}'
    
    if chg_show:
        tx = tx + ("(" + str(chg) + ")").rjust(6)
    else:
        tx = "   " + tx + "   "

    if colors:
        if chg == 0:
            tx = "\33[94m" + tx + "\033[0m"
        elif chg <= 10:
            tx = "\33[92m" + tx + "\033[0m"
        elif chg <= 20:
            tx = "\33[93m" + tx + "\033[0m"
        elif chg <= 40:
            tx = "\33[33m" + tx + "\033[0m"
        else:
            tx = "\33[91m" + tx + "\033[0m"
    
    return(tx)


def report(days):
	print("\n\nDate".ljust(15), end='')
	print(" ".join([i["label"].center(15, ' ') for i in params.values()]))

	for _date in list(data.keys())[-days:]:
		print(_date.ljust(11), end='')
		for k,v in params.items():
			_num = data[_date][k]

			_prev = data[offset(_date, -1)][k]			
			_chg = _num - _prev

			print(present(_num,_chg,v["dp"],v["chg_show"],v["colors"]), end=' ')

		print()

def project(param, interval):
    print(params[param]['label']+' will achieve:')
    today = str(lst_record)[0:10]
    val1 = data[offset(today,-interval)][param]
    val2 = data[today][param]
    for i in range(0,101,5):
        if val2 < i:
            increase = (val2 - val1)/interval
            tte = round((i-val2)/increase)
            print('  '+str(i) + ' on ' + offset(today,tte) + ' ('+ str(tte) +' days)')
    print()

report(28)
project("vacc1",7)
project("vacc2",7)

while True:
	show_days = input("\nHow many days back? ")
	if show_days == "":
		break
	report(int(show_days))

