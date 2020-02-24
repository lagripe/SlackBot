from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)
'''
1 -Bot Token
2- Targeted Channel
3- Targeted Content
'''
Bot_TOKEN = 'xoxb-752603781431-789252497490-l3wFpnDgzI9ILSe8UatfEIxZ'


# --------- DONT CHANGE----
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Bearer {}'.format(Bot_TOKEN)
}
# ------------------------


def forwardessage(message):
    payload = {
        "channel": getConfigAttribute('Target'),
        "text": message
    }
    response = requests.post('https://slack.com/api/chat.postMessage',
                             data=payload, headers=headers)
    response = response.json()
    if response['ok'] == False:
        print('Message was not sent, Error {}'.format(response['error']))


def updateJson(key, val):
    with open('config.json', 'r') as jsonF:
        data = json.loads(jsonF.read())
    # --- Update ---
    if type(val) is not list:
        data[key] = val.strip()
    else:
        data[key] = val
    # --------------
    with open('config.json', 'w') as jsonF:
        jsonF.write(json.dumps(data))


def getConfigData():
    with open('config.json', 'r') as jsonF:
        data = json.loads(jsonF.read())
    return '\n'.join([key + ' : ' + '<None>'
                      if data[key] == ''
                      else key + ' : [' + ','.join(data[key]) +']'
                        if type(data[key]) is list 
                        else key + ' : '  + data[key]
                      for key in data.keys()])


def getConfigAttribute(key):
    with open('config.json', 'r') as jsonF:
        data = json.loads(jsonF.read())
    return data[key]


def shareEmail(event):
    file = event['files'][0]
    payload = {
        "channel": getConfigAttribute('Target'),
        "text":"""
 :100: :email: Email found in <#{}> sent by `<@{}>`
 *Subject : {}*
 <{}| Email Preview>
        """.format(event['channel'],file['user'],file['subject'],file['permalink'])
    }
    response = requests.post('https://slack.com/api/chat.postMessage',
                             data=payload, headers=headers)
    response = response.json()
    if response['ok'] == False:
        print('Message was not sent, Error {}'.format(response['error']))


@app.route('/botAPI', methods=['POST'])
def index():

    # Get Event Content
    data = request.get_json()
    # ----- CHECK IF THE EVENT CAME FROM THE ORIGIN CHANNEL
    if data['event']['channel'] != getConfigAttribute('Origin'):
        return ''
    
    #print(data)
    
    if data['event'] is None:
        return ''
    
    # Skip loop created by the bot post
    if 'subtype' in data['event'].keys():
        if data['event']['subtype'] == 'bot_message' or data['event']['files'] is None:
            return ''

    # ------- CHECK IF EVENT IS A NORMAL MESSAGE ---------
    if 'subtype' not in data['event'].keys():
        print("########################## NORMAL MESSAGE #########################")
        # GET Text Message
        message = data['event']['text'].lower()
        keyword = getConfigAttribute('searchMsg')
        # Forward Message If matchs the criteria
        if message.__contains__(keyword.lower()) and keyword != '':
            forwardessage(message)
        return ''

    # ------- CHECK IF EVENT IS AN EMAIL ---------
    if 'subtype' in data['event'].keys():
        if data['event']['files'][0]['filetype'] == 'email':
            print("########################## EMAIL " +
                  data['event']['files'][0]['id']+"#########################")
            keywordEmailAd = getConfigAttribute('searchEmail')
            keywordEmailSubject = getConfigAttribute('searchSubject')
            keywordEmailBody = getConfigAttribute('searchBody')
            
            cons = {key : False for key in getConfigAttribute('emailConstraints')}
            found = False
            # ---- SEARCH IN SENDER EMAIL
            if data['event']['files'][0]['from'][0]['address'].lower().__contains__(keywordEmailAd.lower()) and keywordEmailAd != '':
                if 'AD' in cons.keys():
                   cons['AD']  = True
                found = True
            print(data['event']['files'][0]['subject'].lower())
            # ---- SEARCH IN EMAIL SUBJECT
            if data['event']['files'][0]['subject'].lower().__contains__(keywordEmailSubject.lower()) and keywordEmailSubject != '':
                if 'SUB' in cons.keys():
                    cons['SUB']  = True
                found = True
            # ---- SEARCH IN EMAIL BODY
            if data['event']['files'][0]['plain_text'].lower().__contains__(keywordEmailBody.lower()) and keywordEmailBody != '':
                if 'BODY' in cons.keys():
                    cons['BODY']  = True
                found = True
            if len(cons.keys()) == 0:
                if found:
                    shareEmail(data['event'])
            else:
                if len([key for key in cons.keys() if cons[key] == False]) == 0:
                    shareEmail(data['event'])
    return ''


@app.route('/help', methods=['POST'])
def help():
    return """
/sourcechannel [CHANNELID] - allows the user to enter the channel id of the sourcechannel
/targetchannel [CHANNELID] - allows the user to enter the channel id of the targetchannel
/searchemailaddress [keyword]- allows the user to enter the keyword to search of the email address sent to the source channel
/searchemailsubject [keyword] - allows the user to enter the keyword to search of the email subject sent to the source channel
/searchemailbody [keyword] - allows the user to enter the keyword to search of the email body sent to the source channel
/searchmessage [keyword] - allows the user to enter the keyword to search in the normal messages that has been sent to the source channel
/searchmessage [C1,C2,C3] - allows the user to enter the required parts for a keyword to exist in order to forward the email (AD : email address, SUB: email subject, BODY: email body)
/config - command for the user to be presented with a list of all the configurations he has done: source channel, target channel, any keywords along with the specific fields which will be searched
            """


@app.route('/sourcechannel', methods=['POST'])
def setSource():
    # Get Event Content
    channel = request.form['text'].strip()
    updateJson('Origin', channel)
    return 'Source Channel has been set to <{}>'.format(channel)


@app.route('/targetchannel', methods=['POST'])
def setTarget():
    # Get Event Content
    channel = request.form['text'].strip()
    updateJson('Target', channel)
    return 'Target Channel has been set to <{}>'.format(channel)


@app.route('/searchemailaddress', methods=['POST'])
def setKeywordEmailAddress():
    keyword = request.form['text'].strip()
    print(keyword)
    updateJson('searchEmail', keyword)
    return 'Keyword for email address has been set to <{}>'.format(keyword)


@app.route('/searchemailsubject', methods=['POST'])
def setKeywordEmailSubject():
    keyword = request.form['text'].strip()
    updateJson('searchSubject', keyword)
    return 'Keyword for email subject has been set to <{}>'.format(keyword)


@app.route('/searchemailbody', methods=['POST'])
def setKeywordEmailBody():
    keyword = request.form['text'].strip()
    updateJson('searchBody', keyword)
    return 'Keyword for email content has been set to <{}>'.format(keyword)


@app.route('/searchmessage', methods=['POST'])
def setKeywordMessage():
    keyword = request.form['text'].strip()
    updateJson('searchMsg', keyword)
    return 'Keyword for message content has been set to <{}>'.format(keyword)

@app.route('/setConstraintEmails', methods=['POST'])
def setConstraintEmails():
    constraints = request.form['text'].strip()
    updateJson('emailConstraints', [] if constraints == '' else constraints.split(''))
    return 'Constraints for emails have been set to <{}>'.format(constraints)

@app.route('/config', methods=['POST'])
def getConfig():
    return """
#######################
#\t\tBot Configuration:\t\t#
#######################

{}
""".format(getConfigData())








'''
Uncomment this section and comment the above to add the confirm the end point in bot creation phase
'''

'''
# --------- Activation
@app.route('/botAPI', methods=['POST'])
def index():

    # Get Event Content
    data = request.get_json()
    print(data)
    return data['challenge']
'''

if __name__ == '__main__':
    app.run(port=8000)
