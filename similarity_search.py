from pymilvus import connections, Collection
import json
import numpy as np
import gensim.downloader as api
import random

# Load the Google pretrained word2vec model
model = api.load("word2vec-google-news-300")

# Connect to Milvus server
connections.connect(host='localhost', port='19530')

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
# # prinnt the sample embedding sepated by a comma
print(", ".join([str(x) for x in sample_embedding]))



# Create a collection object
collection_name = "tender_collection"
collection = Collection(collection_name)
collection.load()

print("Collection loaded successfully")

# Search for similar embeddings from the collection
# search_params = {
#     "metric_type": "L2",
#     "params": {"IVF_FLAT": "flat", "nprobe": 16},
# }


results = collection.search(
    data=sample_embedding, 
    anns_field="embedding", 
    limit=10,
    expr=None,
    param={
        "metric_type": "L2",
        "params": {"nprobe": 16}
    },
    output_fields=['idNumber'],
    # output_fields=['idNumber'],
    # consistency_level="Strong"
)


print("Search results:", results)

collection.release()
connections.disconnect()