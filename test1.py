from google import genai
import os
from dotenv import load_dotenv
import numpy as np
from sklearn.decomposition import PCA
import joblib
import time
import pickle


def _read_bool_arr():
    with open("bool_array.pkl", "rb") as f:
        loaded_array = pickle.load(f)
    return loaded_array


bool_array = _read_bool_arr()
for i in range(len(bool_array)):
    if bool_array[i]:
        print(i)
