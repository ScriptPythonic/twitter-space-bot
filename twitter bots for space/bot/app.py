from flask import render_template,request,json,redirect,jsonify,send_file,Blueprint,flash
import requests
import pandas as pd
from io import BytesIO
import zipfile
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import uuid
load = Blueprint('load', __name__)
bearer_token = "YOUR BEARER TOKEN"



def search_spaces(space_title, space_state, bearer_token):
    twitter_api_url = (
        f"https://api.twitter.com/2/spaces/search?query={space_title}&"
        f"space.fields=id&state={space_state}"
    )

    headers = {
        'Authorization': f'Bearer {bearer_token}',
    }

    try:
        response = requests.get(twitter_api_url, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        space_ids = [space['id'] for space in response_data.get('data', [])]
        return space_ids[0] if space_ids else None
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
@load.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        space_id = request.form["spaceID"]
        space_type = request.form['searchOption']
        user = [space_id,space_type]
        print(user)
        
        if space_type == 'SpaceTitle':
            space = search_spaces(space_id, 'all', bearer_token)
            print(space)
            if space is None:
                flash('Failed to retrieve Space ID for the provided title', category='error')
            space = space_id
        else:
            space_id = space_id if space_type == 'SpaceIds' else None
       
    
        params = {
            "expansions": "host_ids",
            "space.fields": "created_at,invited_user_ids,participant_count,scheduled_start,started_at,title,topic_ids,updated_at",
            "user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,verified_type,withheld",
        }

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }
        
        response = requests.get(f"https://api.twitter.com/2/spaces/{space_id}", headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()

       
            space_data = data.get("data", {})

            custom_space_data = {
            'Space Title': space_data.get('title', ''),
            'Topics Ids': ', '.join(map(str, space_data.get('topic_ids', []))),
            'Topics Names': "Your Topics Names",
            'Space State': space_data.get('state', ''),
            'Updated At': space_data.get('updated_at', ''),
            'invited_user_ids': space_data.get('invited_user_ids', []),
            'Speakers Ids': ', '.join(map(str, space_data.get('speaker_ids', []))),
            'Total Speakers': len(space_data.get('speaker_ids', [])),
            'Total Moderators': "Your Total Moderators",
            'Ended At': space_data.get('ended_at', ''),
            'Language': space_data.get('lang', ''),  
            'Subscriber Count': space_data.get('participant_count', ''),
            'Rooms Duration': "Your Rooms Duration",
        }

            for key, value in custom_space_data.items():
                space_data[key] = value

            
            with open("space_data.json", "w") as space_file:
                json.dump(space_data, space_file, indent=3)

         
            space_users_data = data.get("includes", {}).get("users", [])
            space_user_fields = {
                'id': 'id',
                'name': 'name',
                'username': 'username',
                'created_at': 'created_at',
                 'location': 'location',
                'protected': 'protected',
                'public_metrics': 'public_metrics',
                'description': 'description',
                'entities': 'entities',
                'pinned_tweet_id': 'pinned_tweet_id',
                'profile_image_url': 'profile_image_url',
                'url': 'url',
                'verified': 'verified',
                'verified_type': 'verified_type',
                'withheld': 'withheld',
            }

            user_data = []
            for user in space_users_data:
                formatted_user = {}
                for user_key, user_value in space_user_fields.items():
                     if user_value not in ['url']:
                        formatted_user[user_key] = user.get(user_value, '')
                user_data.append(formatted_user)
                
            with open("space_user_data.json", "w") as space_user_file:
                json.dump(user_data, space_user_file, indent=3)
                df =pd.json_normalize(space_users_data)
                eq =pd.json_normalize(space_data)
                
                keys_to_exclude = [
                    'entities.url.urls',
                    'entities.description.mentions',
                    'entities.description.hashtags',
                    'profile_image_url',
                    'pinned_tweet_id',
                ]
                
                keys_to_exclude2 = [
                    "Speakers Ids",
                     "Total Moderators",
                    "Ended At",
                    "Rooms Duration",
                    "Topics Ids",
                ]
                
                rename_mapping = {
                    'public_metrics.followers_count':'Followers',
                     'public_metrics.following_count': 'Following',
                    'public_metrics.tweet_count': 'Tweet',
                    'public_metrics.listed_count': 'Listed',
                    'public_metrics.like_count':'Likes'
                }
    
                keys_to_expand = ['invited_user_ids', 'topic_ids', 'host_ids']
                
                desired_order_space_data = [
                    'Space Title', 'Topics Ids','Language', 'Topics Names', 'Space State',
                    'Updated At', 'invited_user_ids', 'Speakers Ids', 'Total Speakers',
                    'Total Moderators', 'Ended At', 'Subscriber Count',
                    'Rooms Duration'
                ]
                
                eq = eq[desired_order_space_data]
                
                
                desired_order_user_data = [
                'id', 'name', 'username', 'created_at', 'location', 'protected',
                'description', 'pinned_tweet_id',
                 'verified', 'verified_type',
                  'public_metrics.followers_count',
                     'public_metrics.following_count',
                    'public_metrics.tweet_count',
                    'public_metrics.listed_count',
                    'public_metrics.like_count',
            ]

                df = df[desired_order_user_data]
                
                for key in keys_to_expand:
                    if key in eq and not eq[key].empty and all(isinstance(item, list) and item for item in eq[key]):
                        new_columns = [f"{key}_{i + 1}" for i in range(len(eq[key].iloc[0]))]
                        eq[new_columns] = eq[key].apply(lambda x: pd.Series(x) if x else pd.Series([None] * len(new_columns)))
                      
                        eq = eq.drop([key], axis=1, errors='ignore')

                df.rename(columns=rename_mapping, inplace=True)


                df.replace('', None, inplace=True)


                df = df.drop(keys_to_exclude, axis=1, errors='ignore')
                
                eq=eq.drop(keys_to_exclude2, axis=1, errors='ignore')
                
                
                
                
                eq.to_csv('data.csv', index=False)
                df.to_csv('spaceData.csv', index=False)
                return redirect('/report.html')
                
        else:
            print(f"Error: {response.status_code}, {response.text}")
    
    return render_template('index.html')
@load.route('/report.html')

def report():
    return render_template('report.html')

@load.route('/get_space_data')
def get_space_data():
    with open('space_data.json', 'r') as file:
        space_data = json.load(file)
    return jsonify(space_data)

@load.route('/get_space_user_data')
def get_space_user_data():
    with open('space_user_data.json', 'r') as file:
       space_user_data = json.load(file)
    return jsonify(space_user_data)


@load.route('/space_user_dataJson')
def download_space_user():
    filename = 'space_user_data.json'  
    return send_file(filename, as_attachment=True)

@load.route('/space_user_dataCsv')
def download_space_userCsv():
    filename = 'spaceData.csv'  
    return send_file(filename, as_attachment=True)

@load.route('/space_dataJson')
def download_space():
    filename = 'space_data.json'  
    return send_file(filename, as_attachment=True)

@load.route('/space_dataCsv')
def download_spaceCsv():
    filename = 'data.csv'  
    return send_file(filename, as_attachment=True)

@load.route('/download_files')
def download_files():
    files_to_download = ['space_data.json', 'spaceData.csv', 'data.csv', 'space_user_data.json']
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        for file in files_to_download:
            zip_file.write(file)

    zip_buffer.seek(0)

    return send_file(zip_buffer, as_attachment=True, download_name='data.zip')

def update_or_create_worksheet(spreadsheet, worksheet_name, csv_contents):
        try: 
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(worksheet_name, rows=100, cols=22)
        
        worksheet.clear()

        
        values = [csv.split(',') for csv in csv_contents.split('\n')]
        worksheet.update(values=values, range_name=None)

@load.route('/upload_to_sheet')
def spreadsheets():
    scope = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('local-market-6b270-8156f3ace3a3.json', scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open("space user")

    with open('spaceData.csv', 'r', encoding="utf-8") as file1:
        csv_contents1 = file1.read()

    with open('data.csv', 'r', encoding="utf-8") as file2:
        csv_contents2 = file2.read()

    worksheet1_name = f'spaceUserdata_{uuid.uuid4().hex}'
    worksheet2_name = f'spaceData_{uuid.uuid4().hex}'

    update_or_create_worksheet(spreadsheet, worksheet1_name, csv_contents1)
    update_or_create_worksheet(spreadsheet, worksheet2_name, csv_contents2)
    
    flash('Uploaded sucessfully !!!','success')
    return redirect("/")