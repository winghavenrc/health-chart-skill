from mycroft import MycroftSkill, intent_file_handler

# import os
# import openai


import json
import datetime
import requests


class HealthChart(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('chart.health.intent')
    def handle_chart_health(self, message):
        self.speak_dialog('chart.health')

        self.visit_types = ['health concern', 'wellness exam',
                            'vaccination', 'screening mammography']

        self.speak_dialog('visit.type', wait=False)

        visit_type = self.ask_selection(self.visit_types, min_conf=.4)


#        visit_type = self.get_response('visit.type')
#        self.speak_dialog('confirm.visit.type', {'visit': visit_type})

        confirmed = self.ask_yesno('confirm.visit.type', {'visit': visit_type})
        if confirmed in ["n", "no", "nope"]:
            self.speak_dialog('main.menu', expect_response=False)
# Opening JSON file
        else:

            if get_care_team(self) is True:

                self.log.info(self.provider_list)
                self.speak_dialog(
                    "<speak>I can schedule with any of your currently active providers. <break time='.3s' />Which one of these do you want to schedule with? </speak>", wait=False)

                selected = self.ask_selection(self.provider_list,min_conf=0.5)
                self.log.info(selected)
                self.speak_dialog('get.provider', data={"provider": selected}, expect_response=True, wait=False)

#               find first appointments available from today
                availableSlots = find_first(self)
                self.speak_dialog('speak.times', data={"total": len(availableSlots["time"]), "date": availableSlots["date"]}, expect_response=False, wait=False)
                visit_time = self.ask_selection(availableSlots["time"], min_conf=.6, numeric=False)

#                for index in range(0, len(timeSlots)):
#                    self.speak_dialog('speak.timeslots', data={"slot": timeSlots[index]["start"]}, expect_response=False, wait=False)

    def stop(self):
        pass


def get_care_team(self):
  
  self.provider_list = []

  self.log.info(self.file_system.path)
  self.log.info(self.root_dir)
  file = self.root_dir+"/data/care_team.json"
#  with self.file_system.open(self.root_dir+'care_team.json', "r") as care_team_file:
  with open(file, "r") as care_team_file:

# returns JSON object as
# a dictionary
    care_team = json.load(care_team_file)

#            (data['people1'][0]
# Iterating through the json
# list

# for printing the key-value pair of
# nested dictionary for loop can be used

    for provider in care_team['entry']:
      self.log.info(provider)
      name = provider['name']

      name_dct = dict(name[0])
      specialty = provider['specialty']
#      self.log.info(name)
#      self.log.info(name_dct)
#      self.log.info(specialty)

      lastname = name_dct['family']
#      self.log.info(lastname)
      firstname = name_dct['given'][0]
#      self.log.info(firstname)
      fullname = firstname + " " + lastname + ", " + specialty;

      self.log.info(fullname)

      self.provider_list.append(fullname)
#      self.provider_list.append(firstname)
#     self.provider_list.append(lastname)
#      self.provider_list.append(specialty)

    care_team_file.close()
    return True

  return False


def find_first(self):

    # get the current date and time
    today = datetime.date.today()

    tomorrow = datetime.date(today.year, today.month, today.day+1)

    self.log.info(today)
    self.log.info(tomorrow)

    searchDate = today

    for day in range(1, 5):

        availableSlots = mt_find_available_appts(self, searchDate, 'pm', 'America/Chicago')
        if len(availableSlots["time"]) > 0:
            self.log.info(availableSlots["date"])
#               meditech.revokeToken(handlerInput); // see revokeToken for why to call this now
            break

        searchDate = datetime.date(searchDate.year, searchDate.month, searchDate.day+1)

    return availableSlots


def mt_find_available_appts(self, searchDate, ampm, userTimezone):

    # for a given searchDate

#    availableTimes = []
    availableSlots = {"date": "", "time": [], "id": []}

    # Get a Meditech token

    BASE_HOST = 'https://greenfield-apis.meditech.com'
    IMPLEMENTATION_VERSION = '/v1/argoScheduling/STU3'
    OAUTH_AUTHORIZE = '/oauth/authorize'
    OAUTH_TOKEN = '/oauth/token'
    CLIENT_ID = 'Voxhealth@8c76706c946d4426a648b5c2789cd7e1'
    CLIENT_SECRET = 'gT_463aNSJiGJA7jvsCM4g=='
    GRANT_TYPE = 'client_credentials'
    SCOPE = 'patient/ArgoScheduling.* patient/ArgoScheduling.read'
    BASE_APPOINTMENT = '/Appointment'
    FIND_APPOINTMENTS = '/$find'
    HOLD_APPOINTMENT = '/$hold'
    BOOK_APPOINTMENT = '/$book'


# Define the OAuth2 client ID and secret
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

# Define the OAuth2 token endpoint
    token_url = BASE_HOST + OAUTH_TOKEN

# Request an access token

    token_req_payload = {'grant_type': 'client_credentials',
                         'scope': 'patient/ArgoScheduling.* patient/ArgoScheduling.read'}

    response = requests.post(token_url, data=token_req_payload, verify=False,
                             allow_redirects=False, auth=(client_id, client_secret))

#  response = requests.post(token_url, data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret })
    self.log.info(response)

# Parse the JSON response
    response_data = json.loads(response.text)

# Extract the access token from the response
    access_token = response_data["access_token"]

# Define the API endpoint
    url = BASE_HOST + IMPLEMENTATION_VERSION + BASE_APPOINTMENT + FIND_APPOINTMENTS

# Set the Authorization header with the access token as a bearer token
    headers = {
        "Authorization": "Bearer " + access_token
    }

    begin = searchDate
    end = datetime.date(searchDate.year, searchDate.month, searchDate.day+1)

# Define the parameters as a dictionary
    params = {
        "practitioner": '5563b254-66b1-5203-80e3-bef0be824970',  # Meehan
        "location": '1b2332fb-8906-5264-86e0-df72e983f350',  # Cardiology
          'service-type': '257585005',  # ECHO
          "start": begin,
          "end": end
    }

# Make a GET request to the API
    response = requests.get(url, headers=headers, params=params)

# Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON data returned by the API
        apptSlots = response.json()
        self.log.info(apptSlots)

        total = apptSlots["total"]
        if total == 0:
            # means there's no appointments available
            return availableSlots

        time = []
        id = []
        date = ""

        for index in range(0, total):

            self.log.info(apptSlots["entry"][index]["resource"])

            localStart_dt = datetime.datetime.strptime(apptSlots["entry"][index]["resource"]["start"], "%Y-%m-%dT%H:%M:%S%z")
            self.log.info(localStart_dt)
            meridien = localStart_dt.strftime("%p")
            localStart_str = datetime.datetime.strftime(localStart_dt, "%A %B %-d %-I:%-M %p")
            date = datetime.datetime.strftime(localStart_dt, "%A %B %-d")
            start = datetime.datetime.strftime(localStart_dt, "%-I:%-M %p")

            save = False

            if ampm in ["am", "AM", "MO", "morning"]:
                if meridien == "AM":
                    save = True
            elif ampm in ["pm", "PM", "AF", "afternoon"]:
                if meridien == "PM":
                    save = True
            if save == True:
                time.append(start)
                id.append(apptSlots["entry"][index]["resource"]["id"])
#                slot = {"start": localStart_str, "id": apptSlots["entry"][index]["resource"]["id"]}
#                availableTimes.append(slot)

        availableSlots = { "date": date, "time": time, "id": id }
        self.log.info(availableSlots)

    else:
        # Handle error
        self.log.info(response.status_code)

    return availableSlots


def create_skill():
    return HealthChart()
