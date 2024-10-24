import pandas as pd # type: ignore
from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS
import hashlib ,os
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
CORS(app)

DB = os.getenv("db")
client = MongoClient(DB)  
db = client["ESMS"]  # Database name
collection = db["Users"]     # Collection name

# Base Slack invite link
BASE_SLACK_LINK = "https://join.slack.com/t/portailhq/shared_invite/zt-2t6cxgdma-4MiaIHE9Y8eqZqQoQ9cxzQ"

def generate_unique_key(email):
    """Create a unique key based on the email."""
    return hashlib.md5(email.encode()).hexdigest()

@app.route('/import-emails', methods=['POST'])
def import_emails():
    """Read emails from CSV, generate links, and write them to MongoDB."""
    # Load emails from the CSV file
    print("Received POST request to /import-emails") 
    try:
      df = pd.read_csv('emails.csv').dropna()  # Drop rows with NaN values
      df['email'] = df['email'].str.strip()  # Remove leading/trailing whitespace

    except Exception as e:
      return jsonify({"error": str(e)}), 500

    links = []
    
    for index, row in df.iterrows():
        email = row['email']
        unique_key = generate_unique_key(email)
        one_time_link = f"{BASE_SLACK_LINK}{unique_key}"

        # Create the document to be inserted
        invite_data = {
            'email': email,
            'invite_link': one_time_link,
            'used': False
        }

        # Insert into MongoDB
        result = collection.insert_one(invite_data)
        print(f"Inserted ID: {result.inserted_id}")
        links.append(invite_data)

    return jsonify(links)


@app.route('/get-invite-link', methods=['GET'])
def get_invite_link():
    email = request.args.get('email').lower()

    # Find the invite by email
    invite = collection.find_one({'email': email})

    if invite:
        if invite['used']:
            return jsonify({"message": "This invite link has already been used."}), 400
        else:
            # Return the invite link if it's not used
            collection.update_one({'email': email}, {'$set': {'used': True}})
            return jsonify({"invite_link": invite['invite_link']}), 200
    else:
        return jsonify({"message": "No invite link found for this email."}), 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
    
#if the email is there
#compare lowercase