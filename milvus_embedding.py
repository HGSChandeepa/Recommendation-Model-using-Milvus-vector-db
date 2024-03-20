from pymilvus import connections, DataType, CollectionSchema, FieldSchema, Collection
import json
import numpy as np
import gensim.downloader as api
import random

# Load the Google pretrained word2vec model
model = api.load("word2vec-google-news-300")

# Load the data from the JSON file
json_file_path = "data.json"
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

idNumbers = []
# for all the data create a unique idNumber
for i in range(len(data)):
    idNumbers.append(random.randint(100000, 999999))
    # also update the json data with the idNumber
    data[i]['idNumber'] = idNumbers[i]

print(len(idNumbers), "idNumbers created successfully")

# Function to calculate average vector for text
def calculate_average_vector(text):
    tokens = text.split()
    vectors = [model[token] for token in tokens if token in model]
    if vectors:
        return np.mean(vectors, axis=0)
    else:
        return np.zeros(model.vector_size)

# Function to process data and store embeddings
def process_and_store_embeddings(data):
    embeddings = []
    for value in data:
        title_vector = calculate_average_vector(value.get('title', ''))
        description_vector = calculate_average_vector(value.get('description', ''))
        combined_vector = np.concatenate([title_vector, description_vector])
        embeddings.append(combined_vector)
    return embeddings

# Call the function to process data and store embeddings
embeddings = process_and_store_embeddings(data)
print(len(embeddings), "embeddings created successfully")

# Connect to Milvus server
connections.connect(host='localhost', port='19530')

# create the fieldSchema for the collection
schema = CollectionSchema(fields=[
    FieldSchema(name="idNumber", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=600)  # Corrected dimension to match embeddings
])

# Create a collection in Milvus
collection_name = "tender_collection"
collection = Collection(
    name=collection_name,
    schema=schema,
    consistency_level="Strong"
)

# Specify the index type and parameters
index = {
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 128},
}
collection.create_index("embedding", index)

# Insert embeddings into the collection
insert_result = collection.insert([
    {"idNumber": idNumbers[i], "embedding": embedding.tolist()} 
    for i, embedding in enumerate(embeddings)
])

# After final entity is inserted, it is best to call flush to have no growing segments left in memory
collection.flush() 

# Disconnect from Milvus server
connections.disconnect(alias='default')
print("Data and embeddings stored successfully in Milvus")


from pymilvus import MilvusClient

# Set your cluster endpoint and token
CLUSTER_ENDPOINT = "YOUR_CLUSTER_ENDPOINT"  # Replace with your cluster endpoint
TOKEN = "YOUR_API_KEY"  # Replace with your API key

# Initialize a MilvusClient instance
client = MilvusClient(
    uri=CLUSTER_ENDPOINT,
    token=TOKEN
)

# Create a collection
collection_name = "tender_collection"
collection_param = {
    "fields": [
        {"name": "idNumber", "type": DataType.INT64},
        {"name": "embedding", "type": DataType.FLOAT_VECTOR, "params": {"dim": 600}}
    ],
    "segment_row_limit": 4096000,
    "auto_id": False
}

client.create_collection(collection_name, collection_param)

# Insert embeddings into the collection
entities = [
    {"name": "idNumber", "type": DataType.INT64},
    {"name": "embedding", "type": DataType.FLOAT_VECTOR, "values": embeddings}
]

client.insert(collection_name, entities)
