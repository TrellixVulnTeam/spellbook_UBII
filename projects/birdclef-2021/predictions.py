import pandas as pd
import numpy as np
import librosa
import matplotlib.pyplot as plt
import librosa.display
import os
import tensorflow_addons as tfa
import tensorflow as tf
from keras.models import load_model
from itertools import chain
from skimage.io import imread

# Global vars
RANDOM_SEED = 1337
SAMPLE_RATE = 32000
SIGNAL_LENGTH = 5 # seconds
SPEC_SHAPE = (128, 256) # height x width
FMIN = 500
FMAX = 12500

def find5largest(arr, n):
    arr = sorted(arr) # It uses Tuned Quicksort with
                      # avg. case Time complexity = O(nLogn)
    
    largest = []
    check = 0
    count = 1
 
    for i in range(1, n + 1):
 
        if(count < 6):
            if(check != arr[n - i]):
                 
                # to handle duplicate values
                largest.append(arr[n - i])
                check = arr[n - i]
                count += 1
        else:
            break
    
    return largest

# Labels to digits
TRAIN_META = pd.read_csv('datasets/train/0garbage/train_metadata.csv')
labels = TRAIN_META['primary_label'].unique()

label_to_digit = {k: v for v, k in enumerate(labels)}

# Model
bird_model = load_model('bird_bce_val_acc.h5')

path_audio = 'datasets/train/0garbage/train_soundscapes/20152_SSW_20170805.ogg'
file = '20152_SSW_20170805'
fileinfo = file.split(os.sep)[-1].rsplit('.', 1)[0].split('_')

audio, _ = librosa.load(path_audio, sr=SAMPLE_RATE)

pred = {'row_id': [], 'birds': []}

second = 5
for i in range(0, len(audio), int(5 * 32000)):

    split = audio[i:i + int(5 * 32000)]

    # Create melspectogram of 5 second split
    hop_length = int(SIGNAL_LENGTH * SAMPLE_RATE / (SPEC_SHAPE[1] - 1))
    mel_spec = librosa.feature.melspectrogram(y=split,
                                                sr=SAMPLE_RATE,
                                                n_fft=1024,
                                                hop_length=hop_length,
                                                n_mels=SPEC_SHAPE[0],
                                                fmin=FMIN,
                                                fmax=FMAX)

    mel_spec = librosa.power_to_db(mel_spec, ref=np.max)

    mel_spec -= mel_spec.min()
    mel_spec /= mel_spec.max()
    if not mel_spec.max() == 1.0 or not mel_spec.min() == 0.0:
        continue
    
    mel_spec = np.expand_dims(mel_spec, 0)
    
    mel_spec = np.repeat(mel_spec[..., np.newaxis], 3, -1)
    
    #spec = np.array([imread('datasets/train/collapsed_train_melspecs_full/daejun_159.png')], dtype='float32')/255.0
    #spec_rgb = np.repeat(spec[..., np.newaxis], 3, -1)
    
    prediction = bird_model.predict(mel_spec, batch_size=1)
    prediction = list(chain.from_iterable(prediction))
    prediction = [ -x for x in prediction]
    prediction = list(1/(1 + np.exp(prediction)))
    #prediction_bool = prediction > 0.25
    #print(prediction_bool)
    
    largest = find5largest(prediction, len(prediction))
    largest_idx = []
    
    row_id = fileinfo[0] + '_'  + fileinfo[1] + '_'  + str(second)
    
    pred_5sec = []
    for idx, val in enumerate(largest):
        
        largest_idx.append(prediction.index(val))
    
        for key, value in label_to_digit.items():
            if largest_idx[idx] == value:
                if val < 0.6:
                    if idx == 4 and len(pred_5sec) == 0:
                        pred_5sec.append('nocall')
                    else:
                        continue
                else:
                    pred_5sec.append(key)
    
    pred_5sec = ' '.join(pred_5sec)
                    
    pred['birds'].append(pred_5sec)
    pred['row_id'].append(row_id)
    
    if second == 100:
        break
    
    second += 5
print(pred)