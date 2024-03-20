from flask import Flask, request, jsonify
from pymilvus import connections, Collection
import json
import numpy as np
import gensim.downloader as api

# Load the Google pretrained word2vec model
model = api.load("word2vec-google-news-300")

# Connect to Milvus server
connections.connect(host='localhost', port='19530')

# Create a Flask application
app = Flask(__name__)

# Function to calculate average vector from text
def calculate_average_vector(text):
    tokens = text.split()
    vectors = [model[token] for token in tokens if token in model]
    if vectors:
        return np.mean(vectors, axis=0)
    else:
        return np.zeros(model.vector_size)

# Function to process data and store embeddings
def process_and_store_embeddings(data):
    title_vector = calculate_average_vector(data.get('title', ''))
    description_vector = calculate_average_vector(data.get('description', ''))

    combined_vector = np.concatenate([title_vector, description_vector])
    
    return combined_vector

# Load the sample data from a JSON file
json_file_path = "sample.json"
with open(json_file_path, 'r', encoding='utf-8') as f:
    sample_data = json.load(f)

# Process and store the embeddings for the sample data
sample_embedding = process_and_store_embeddings(sample_data)

# Create a collection object
collection_name = "tender_collection"
collection = Collection(collection_name)
collection.load()

# Route to handle GET requests for similarity search
@app.route('/api/search', methods=['GET'])
def search():
    # Get idNumber from query parameter
    id_number = request.args.get('idNumber')

    # Retrieve data associated with idNumber from your database or storage
    # Assuming here that you have a function to retrieve data by idNumber
    data = retrieve_data_by_id(id_number)

    # Process data and calculate embeddings
    input_embedding = process_and_store_embeddings(data)

    # Search for similar embeddings from the collection
    search_params = {
        "metric_type": "L2",
        "params": {"IVF_FLAT": "flat", "nprobe": 16},
    }

    results = collection.search(
        data=input_embedding, 
        anns_field="embedding", 
        limit=10,
        expr=None,
        param=search_params
    )

    # Prepare response
    response = {
        "ids": results[0].ids,
        "distances": results[0].distances
    }

    return jsonify(response)

# Dummy function to retrieve data by idNumber
def retrieve_data_by_id(id_number):
    # Assuming here that you have a database or storage where you can retrieve data by idNumber
    # For simplicity, returning sample data
    return sample_data

if __name__ == '__main__':
    app.run(debug=True, port=9000)

# Disconnect Milvus connections
collection.release()
connections.disconnect()
