import numpy as np
import pandas as pd
import datetime
from matplotlib import pyplot as plt
import yfinance as yf
import os

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import tensorflow as tf
import tensorflow_probability as tfp
tfd = tfp.distributions




name = 'AAPL'

train_end_date = '2023-08-01'
name_ohlc_df = yf.download(name, start='2002-01-01', end=train_end_date)
name_ohlc_df = name_ohlc_df.reset_index()
data = {'date': name_ohlc_df.Date, 'close': name_ohlc_df.Close, 'volume': name_ohlc_df.Volume}
df = pd.DataFrame(data)

# concatenated_df = pd.concat([df1, df2], axis=0, ignore_index=True)
train_size = int(0.85 * len(df))
print('TRAIN UNTIL:',df.iloc[train_size],'\n\n\n')

sequence_length = 10
train_input = np.lib.stride_tricks.sliding_window_view(df.iloc[:train_size,1].values, (sequence_length,))
val_input = np.lib.stride_tricks.sliding_window_view(df.iloc[train_size:-1,1].values, (sequence_length,))
# train_input = train_input.reshape(len(train_input),-1,2)
# val_input = val_input.reshape(len(val_input),-1,2)
y1 = np.array(df.iloc[sequence_length:train_size+1,1]).T.astype(np.float32).reshape(-1,1)
y2 = np.array(df.iloc[sequence_length+train_size:,1]).T.astype(np.float32).reshape(-1,1)

deep_model = tf.keras.Sequential([
  tf.keras.layers.LSTM(32,activation='relu',input_shape=(sequence_length,1),return_sequences=False),
  tf.keras.layers.Dense(64,activation='relu'),
  tf.keras.layers.Dense(24,activation='relu'),
  tf.keras.layers.Dense(8,activation='relu'),
  tf.keras.layers.Dense(1+1),
  tfp.layers.DistributionLambda(
    #   lambda t: tfd.Normal(loc=t[..., :1],scale=1e-3 + tf.math.softplus(0.001*t[...,1:]))),
      lambda t: tfd.StudentT(df=4,loc=t[..., :1],scale=1e-3 + tf.math.softplus(t[...,1:])))
])




negloglik = lambda y, rv_y: -rv_y.log_prob(y) #-y_pred.log_prob(y_true)
deep_model.compile(optimizer=tf.keras.optimizers.legacy.Adam(), loss=negloglik)
history_ = deep_model.fit(train_input, y1, epochs=750, verbose=1)
model_folder = '/Users/leonbozianu/work/lightbox/models/{}'.format("model_bayes2")
if not os.path.exists(model_folder):
    os.makedirs(model_folder)
deep_model.save_weights(filepath=model_folder+'/final_weight.h5')
print("Model weights saved")



plt.figure(figsize=(4,3))

plt.plot(history_.history['loss'], label='Train loss B')
plt.plot(history_.history['val_loss'], label='Val loss B')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5),fontsize='x-small')
plt.show()


yhat = deep_model(val_input)
assert isinstance(yhat, tfd.Distribution)
