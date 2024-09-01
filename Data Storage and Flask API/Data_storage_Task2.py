import pymongo
import json
import os
import certifi
from pymongo.server_api import ServerApi

# The connection string that connects this code with MongoDB Atlas
uri = "mongodb+srv://hamadanihadi04:Hadi_1233@datascience.ojdba.mongodb.net/?retryWrites=true&w=majority&appName=DataScience"

# Create a new client and connect to the server, specifying the certifi path for SSL certificates
client = pymongo.MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

# The name of the database at MongoDB Atlas
db = client["Al_Mayadeen"]

# The name of the collection in the database
collection = db["Articles"]

# The directory containing the saved JSON articles
directory = r'C:\Users\AUTO SERVICE\PycharmProjects\Web_Scarper_Task\articles'

# Iterate over all JSON files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.json'):
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                # Ensure data is a list of dictionaries
                if isinstance(data, list):
                    collection.insert_many(data)
                    print(f"{filename} inserted successfully!")
                else:
                    print(f"{filename} is not a valid JSON array. Skipping...")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("All data inserted successfully!")
