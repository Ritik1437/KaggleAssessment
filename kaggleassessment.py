# -*- coding: utf-8 -*-
"""kaggleAssessment.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1D3AXQbrr2LqMCIaQgQnqW2bRGl8Jag7F
"""

!pip install -q -U keras-nlp

!pip install -q -U tensorflow-hub

!pip install -q -U tensorflow-cpu

!pip install -q -U keras>=3

import os
import jax

jax.devices()

os.environ["KERAS_BACKEND"] = "jax"

import os

os.environ["KERAS_BACKEND"] = "jax"

os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = "0.9"

import keras
import keras_nlp

device_mesh = keras.distribution.DeviceMesh(
    (1, 8),
    ["batch", "model"],
    devices=keras.distribution.list_devices())

model_dim = "model"

layout_map = keras.distribution.LayoutMap(device_mesh)

# Weights that match 'token_embedding/embeddings' will be sharded on 8 TPUs
layout_map["token_embedding/embeddings"] = (model_dim, None)
# Regex to match against the query, key and value matrices in attention layers
layout_map["decoder_block.*attention.*(query|key|value)/kernel"] = (model_dim, None, None)
layout_map["decoder_block.*attention_output/kernel"] = (model_dim, None, None)
layout_map["decoder_block.*ffw_gating.*/kernel"] = (None, model_dim)
layout_map["decoder_block.*ffw_linear/kernel"] = (model_dim, None)

model_parallel = keras.distribution.ModelParallel(
    device_mesh, layout_map, batch_dim_name="batch")

keras.distribution.set_distribution(model_parallel)
gemma_lm = keras_nlp.models.GemmaCausalLM.from_preset("gemma_7b_en")

decoder_block_1 = gemma_lm.backbone.get_layer('decoder_block_1')
print(type(decoder_block_1))
for variable in decoder_block_1.weights:
  print(f'{variable.path:<58}  {str(variable.shape):<16}  {str(variable.value.sharding.spec)}')

gemma_lm.generate("Best comedy movies in the 90s ", max_length=64)

import tensorflow_datasets as tfds

imdb_train = tfds.load(
    "imdb_reviews",
    split="train",
    as_supervised=True,
    batch_size=2,
)
# Drop labels.
imdb_train = imdb_train.map(lambda x, y: x)

imdb_train.unbatch().take(1).get_single_element().numpy()

imdb_train = imdb_train.take(2000)

gemma_lm.backbone.enable_lora(rank=4)

gemma_lm.preprocessor.sequence_length = 128

optimizer = keras.optimizers.AdamW(
    learning_rate=5e-5,
    weight_decay=0.01,
)

optimizer.exclude_from_weight_decay(var_names=["bias", "scale"])

gemma_lm.compile(
    loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    optimizer=optimizer,
    weighted_metrics=[keras.metrics.SparseCategoricalAccuracy()],
)
gemma_lm.summary()
gemma_lm.fit(imdb_train, epochs=1)

gemma_lm.generate("Best comedy movies in the 90s ", max_length=64)

gemma_lm.generate("What is the meaning of life?", max_length=64)

gemma_lm = keras_nlp.models.GemmaCausalLM.from_preset("gemma_2b_en")

gemma_lm.generate("How does the brain work?", max_length=64)

gemma_lm.generate(
    ["What is the meaning of life?",
     "How does the brain work?"],
    max_length=64)

gemma_lm.compile(sampler="top_k")
gemma_lm.generate("What is the meaning of life?", max_length=64)

