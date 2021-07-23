import requests, smtplib, configparser
from datetime import datetime
from pymongo import MongoClient
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Pulls data from configuration file
config = configparser.ConfigParser()
config.read('pb.ini')
from_mail = config['email']['from']
to_mail = config['email']['to']
mail_pass = config['email']['mail_pass']
pb_api_key = config['secrets']['api_key']
mongo_login = config['secrets']['mongodb']

headers = {
    'accept': 'application/json',
    'api-key': pb_api_key,
    'X-Fields': 'total{value}, hits{id, headline, employer{name}, application_deadline, webpage_url, workplace_address{coordinates}, duration{label}, working_hours_type{label}, employment_type{label}}',
}

## API params can be found here: https://raw.githubusercontent.com/JobtechSwe/elastic-importers/develop/importers/taxonomy/resources/taxonomy_to_concept.json
params = (
#    ('region', 'NvUF_SP1_1zo'),        ### Shows results for Västernorrland, does however overwrite Sundsvall below
    ('municipality', 'dJbx_FWY_tK6'),        ### Shows results for Sundsvall
    ('occupation-field', 'apaJ_2ja_LuF'),   ### Shows results from the category "DATA/IT"
    ('employment-type', 'PFZr_Syz_cUq'),
    ('limit', '70'),
)

# data
response = requests.get('https://jobsearch.api.jobtechdev.se/search', headers=headers, params=params)
data = response.json()
jobs = data["hits"]
date = str(datetime.date(datetime.now()))
client = MongoClient(mongo_login)
db = client.jobsearch

# Write to database
def job_print():
    dicts = []
    for i in jobs:
        output = {
            'ID': i['id'],
            'Title': i['headline'],
            'Employer' : i['employer']['name'],
            'Employment_type' : i['employment_type']['label'],
            'Fulltime' : i['duration']['label'],
            'Deadline' : i['application_deadline'].replace('T23:59:59', ''),
            'Link' : i['webpage_url'],
            'Date_added' : date
        }

        db.jobs.create_index([('ID', 1)], unique=True)
        dicts.append(output)
    try:
        db.jobs.insert_many(dicts, ordered=False)
    except Exception:
        pass

# Send new jobs as an email
def email_jobs():
    mail_cont = []
    item_date = ""
    count = 0
    info = db.jobs.find()
    for item in info:
        item_date = item["Date_added"]
        if item_date == date:
            mail_cont.extend((
                '<div style="background-color:#1D1F28; padding: 10px 10px 15px 20px; width:50%;margin:0px auto 0px auto; border-radius: 25px; border-style: outset; border-color:#8999F1; font-family: Bahnschrift;">' + 
                '<font color=#f18098 size="5"><b><u>' + item["Title"] + '</b></u></font><br>',
                '<font color=#C477DB>' + '<b>Företag: </b>' + '<font color=#7EE6F2>' + item["Employer"] + '</font><br>',
                '<font color=#C477DB><b>Typ av anställning: </b></font>' + '<font color=#7EE6F2>' + item["Employment_type"] + '</font><br>',
                '<font color=#C477DB><b>Heltid eller deltid: </b></font>' + '<font color=#7EE6F2>' + item["Fulltime"] + '</font><br>',
                '<font color=#C477DB><b>Senaste ansökningsdag: </b></font>' + '<font color=#7EE6F2>' + item["Deadline"] + '</font><br>',
                '<font color=#C477DB><b>Länk: </b></font>' + '<a style="text-decoration:none;" href="' + item["Link"] + '"><font color=#7EE6F2>Click me!</font></a></div><br><br>'
                ))
            count += 1

    if mail_cont != []:
        email = MIMEMultipart('alternative')
        email['from'] = 'I\'m a little teacup' # PUT YOUR NAME HERE
        email['to'] = to_mail
        email['subject'] = f'Vi hittade {count} stycken nya jobb inom DATA/IT i Sundsvall!' # PUT YOUR MAIL TITLE HERE
        part1 = MIMEText(
                    str(mail_cont).replace("['", "").replace("', '", "").replace("']", ""), 'html'
                    )
        email.attach(part1)
        with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(from_mail, mail_pass)
            smtp.send_message(email)

# Cleans out expired jobs from the database
def cleanup():
    info = db.jobs.find()
    item_deadline = ''
    for i in info:
        item_deadline = i["Deadline"]
        if item_deadline < date:
            db.jobs.delete_one(i)

def main():
    job_print()
    email_jobs()
    cleanup()

if __name__ == '__main__':
	main()