import os
import json
import re
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import pandas as pd
from flask_cors import CORS  # Import CORS
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://autoviz-f90f7.web.app"}})

# Directory where JSON files are stored
DATA_DIR = "data"

# Load environment variables from the .env file
load_dotenv()

# Set up the client
endpoint = "https://models.github.ai/inference"
model_name = "deepseek/DeepSeek-V3-0324"
token = os.getenv('MODEL_ACCESS_TOKEN')

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

# Function to load JSON data
def load_data(file_name):
    file_path = os.path.join(DATA_DIR, file_name)

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as f:
            return json.load(f)
    return None

    

def load_prompt(context):
    prompt_file = f"general_prompt.txt"  # File name based on context (alerts, devices, clients)
    file_path = os.path.join(DATA_DIR, prompt_file)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as f:
            return f.read()  # Return the content of the text file
    return None

# API to get analyzed client data
@app.route('/analyze', methods=['POST'])
def get_analyzed_data():
    context = request.query_string.decode('utf-8')
    print(request)
    data = load_data(f"{context}.json")  # Assuming the data is in a JSON file


    if not data:
        return jsonify({"error": "Data not found"}), 404
    
    # Load the prompt for the current context
    prompt_template = load_prompt(context)

    with open('keywords.json', 'r') as file:
        all_keywords = json.load(file)

    displayedColumns = request.get_json()
    print("Analysing on these columns : ",displayedColumns)

    # Prepare the prompt by inserting the data dynamically into the prompt template
    if prompt_template:
        prompt = prompt_template.format(data=json.dumps(data, indent=2),keywords = all_keywords[context],displayedColumns = displayedColumns)  # Insert the data into the prompt
    else:
        raise ValueError(f"No prompt found for context: {context}")

    # Send the request to the model
    response = client.complete(
        messages=[{
            "role": "user",
            "content": prompt
        }],
        temperature=1.0,
        top_p=1.0,
        max_tokens=2000,
        model=model_name
    )

    # Parse and save the response
    parsed_data = json.loads(response.choices[0].message.content[7:-4])
    return parsed_data


# API to get raw alerts data
@app.route('/raw/alerts', methods=['GET'])
def get_raw_alerts():
    data = load_data("alerts.json")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    return jsonify(data)

# API to get raw devices data
@app.route('/raw/devices', methods=['GET'])
def get_raw_devices():
    data = load_data("devices.json")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    return jsonify(data)

# API to get raw clients data
@app.route('/raw/clients', methods=['GET'])
def get_raw_clients():
    data = load_data("clients.json")
    if not data:
        return jsonify({"error": "Data not found"}), 404

    return jsonify(data)

if __name__ == '__main__':
    app.run(host = '0.0.0.0',debug=True)
