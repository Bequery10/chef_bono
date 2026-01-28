from google import genai
import os
from dotenv import load_dotenv
import numpy as np
from sklearn.decomposition import PCA
import joblib
import time


def _init_gemini(name, key_index=0):
    load_dotenv()
    API_KEY = os.getenv("GOOGLE_API_KEY" + str(key_index))
    client = genai.Client(api_key=API_KEY)
    model_name = name
    models_list = client.models.list(config={"page_size": 5})
    model = None
    for model1 in models_list:
        if model1.name == "models/" + model_name:
            model = model1
            break
    return client, model


def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def fit_and_save_pca(embeddings, n_components=4, filename="pca_model.joblib"):
    pca = PCA(n_components=n_components)
    pca.fit(embeddings)
    joblib.dump(pca, filename)
    return pca


def load_pca(filename="pca_model.joblib"):
    return joblib.load(filename)


def transform_embedding_pca(pca, embedding):
    return pca.transform([embedding])[0]


model_name = "gemini-embedding-001"
client, model = _init_gemini(model_name, 0)

name_list = [
    "24 HOUR COLE SLAW",
    "GOOEY BUTTER CAKE",
    "COCOA BREAD",
    "MONKEY BREAD",
    "CHOCOLATE CHIP COOKIES",
    "SPAGHETTI CARBONARA",
    "VEGAN CHILI",
    "TOMATO SOUP",
    "GRILLED CHEESE SANDWICH",
    "BANANA BREAD",
]
embeddings_list = []
start_time = time.time()
for name in name_list:
    embedding_obj = client.models.embed_content(
        model=model_name, contents=name
    ).embeddings
    embedding = embedding_obj[0].values
    embeddings_list.append(embedding)

embeddings = np.stack(embeddings_list)

# Fit PCA on your dataset and save it
n_components = len(name_list)
pca = fit_and_save_pca(
    embeddings, n_components=n_components, filename="pca_model.joblib"
)
end_time = time.time()
print(f"Time taken to fit PCA: {end_time - start_time} seconds")
exit(0)

# Later, load PCA and transform a new embedding
pca_loaded = load_pca("pca_model.joblib")
new_phrase = "I want a sweet bread."
new_embedding_obj = client.models.embed_content(
    model=model_name, contents=new_phrase
).embeddings
new_embedding = new_embedding_obj[0].values
reduced_new_embedding = transform_embedding_pca(pca_loaded, new_embedding)

similarities = [
    (i, cosine_similarity(new_embedding, embedding))
    for i, embedding in enumerate(embeddings_list)
]

# Sort by similarity, descending
similarities.sort(key=lambda x: x[1], reverse=True)

# Print top 5 matches
for idx, sim in similarities[:5]:
    print(
        f"Original cosine similarity between '{new_phrase}' and '{name_list[idx]}' embedding: {sim}"
    )
