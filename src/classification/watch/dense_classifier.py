""" This file implements a Fully Connected classifier for the watch data. """

import os
from typing import Dict

import tensorflow as tf

from src.classification.watch.nn_classifier import WatchNNBaseClassifier
from src.utils import cv_training_loop


class WatchDenseClassifier(WatchNNBaseClassifier):
    """
    Classifier consisting of Dense layers only.
    """

    def __init__(self, parameters: Dict = None):
        """
        Initialize the Watch-Dense emotion classifier

        :param parameters: Some configuration parameters for the classifier
        """
        super().__init__("watch_dense", parameters)

    def initialize_model(self, parameters: Dict) -> None:
        """
        Initializes a new and pretrained version of the Watch-Dense model

        :param parameters: Parameters for initializing the model.
        """
        dense_units = parameters.get("dense_units", 512)
        dropout = parameters.get("dropout", 0.2)
        input_size = self.data_reader.get_input_shape(parameters)
        hidden_layers = parameters.get("hidden_layers", 2)
        input_tensor = tf.keras.layers.Input(
            shape=(*input_size,), dtype=tf.float32, name="raw"
        )
        flat = tf.keras.layers.Flatten()(input_tensor)
        hidden = tf.keras.layers.Dense(dense_units)(flat)
        hidden = tf.keras.layers.Dropout(dropout)(hidden)
        for layer_id in range(hidden_layers - 1):
            hidden = tf.keras.layers.Dense(dense_units)(hidden)
            hidden = tf.keras.layers.Dropout(dropout)(hidden)
        out = tf.keras.layers.Dense(7, activation="softmax")(hidden)
        self.model = tf.keras.Model(input_tensor, out)


def _main():  # pragma: no cover
    classifier = WatchDenseClassifier()
    parameters = {
        "epochs": 1000,
        "patience": 100,
        "batch_size": 64,
        "window": 20,
        "hop": 2,
        "balanced": True,
        "label_mode": "both",
        "learning_rate": 0.0003,
        "dense_units": 4096,
        "dropout": 0.2,
        "hidden_layers": 2,
    }
    save_path = os.path.join("models", "watch", "watch_dense")
    cv_training_loop(classifier, parameters, save_path)


if __name__ == "__main__":  # pragma: no cover
    _main()
