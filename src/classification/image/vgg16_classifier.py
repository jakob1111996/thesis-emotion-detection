""" This file contains the VGG16 facial emotion classifier """

import os
from typing import Dict

import numpy as np
import tensorflow as tf

from src.classification.image.image_emotion_classifier import (
    ImageEmotionClassifier,
)
from src.data.data_reader import Set
from src.utils import logging, training_loop


class VGG16Classifier(ImageEmotionClassifier):
    """
    Class that implements an emotion classifier using VGG16
    """

    def __init__(self, parameters: Dict = None) -> None:
        """
        Initialize the VGG16 emotion classifier

        :param parameters: Some configuration parameters for the classifier
        """
        super().__init__("vgg16", parameters)
        tf.get_logger().setLevel("ERROR")
        self.model = None
        self.logger = logging.KerasLogger()
        self.logger.log_start({"init_parameters": parameters})

    def initialize_model(self, parameters: Dict) -> None:
        """
        Initializes a new and pretrained version of the VGG16Classifier model

        :param parameters: Parameters for initializing the model.
        """
        l1 = parameters.get("l1", 0.0)
        l2 = parameters.get("l2", 0.0)
        dropout = parameters.get("dropout", 0.0)
        input_tensor = tf.keras.layers.Input(
            shape=(48, 48, 3), dtype=tf.float32, name="image"
        )
        input_tensor = tf.keras.applications.vgg16.preprocess_input(
            input_tensor
        )

        model = tf.keras.applications.VGG16(
            include_top=False,
            weights="imagenet",
            input_tensor=input_tensor,
            input_shape=(48, 48, 3),
        )
        for layer in model.layers[: parameters.get("frozen_layers", -4)]:
            layer.trainable = False
        out = model(input_tensor)

        out = tf.keras.layers.Flatten()(out)
        if parameters.get("deep", True):
            out = tf.keras.layers.Dense(
                4096,
                activation="relu",
                kernel_regularizer=tf.keras.regularizers.L1L2(l1=l1, l2=l2),
            )(out)
            if dropout:
                out = tf.keras.layers.Dropout(dropout)(out)
            out = tf.keras.layers.Dense(
                4096,
                activation="relu",
                kernel_regularizer=tf.keras.regularizers.L1L2(l1=l1, l2=l2),
            )(out)
            if dropout:
                out = tf.keras.layers.Dropout(dropout)(out)
        out = tf.keras.layers.Dense(
            1000,
            activation="relu",
            kernel_regularizer=tf.keras.regularizers.L1L2(l1=l1, l2=l2),
        )(out)
        if dropout:
            out = tf.keras.layers.Dropout(dropout)(out)
        top = tf.keras.layers.Dense(
            7, activation="softmax", name="classifier"
        )(out)
        self.model = tf.keras.Model(input_tensor, top)

    def train(self, parameters: Dict = None, **kwargs) -> None:
        """
        Training method for VGG16Classifier model

        :param parameters: Parameter dictionary used for training
        :param kwargs: Additional kwargs parameters
        """
        parameters = self.init_parameters(parameters, **kwargs)
        self.logger.log_start({"train_parameters": parameters})
        epochs = parameters.get("epochs", 20)

        if not self.model:
            self.initialize_model(parameters)
        self.prepare_training(parameters)

        self.model.compile(
            optimizer=self.optimizer, loss=self.loss, metrics=self.metrics
        )
        self.prepare_data(parameters)

        history = self.model.fit(
            x=self.train_data,
            validation_data=self.val_data,
            epochs=epochs,
            callbacks=[self.callback],
            class_weight=self.class_weights,
        )
        self.logger.log_end({"history": history})
        self.is_trained = True

    def load(self, parameters: Dict = None, **kwargs) -> None:
        """
        Loading method that loads a previously trained model from disk.

        :param parameters: Parameters required for loading the model
        :param kwargs: Additional kwargs parameters
        """
        parameters = self.init_parameters(parameters, **kwargs)
        save_path = parameters.get("save_path", "models/image/vgg16")
        self.model = tf.keras.models.load_model(save_path)

    def save(self, parameters: Dict = None, **kwargs) -> None:
        """
        Saving method that saves a previously trained model on disk.

        :param parameters: Parameters required for storing the model
        :param kwargs: Additional kwargs parameters
        """
        if not self.is_trained:
            raise RuntimeError(
                "Model needs to be trained in order to save it!"
            )
        parameters = self.init_parameters(parameters, **kwargs)
        save_path = parameters.get("save_path", "models/image/vgg16")
        self.model.save(save_path, include_optimizer=False)
        self.logger.save_logs(save_path)

    def classify(self, parameters: Dict = None, **kwargs) -> np.array:
        """
        Classification method used to classify emotions from images

        :param parameters: Parameter dictionary used for classification
        :param kwargs: Additional kwargs parameters
        :return: An array with predicted emotion indices
        """
        parameters = self.init_parameters(parameters, **kwargs)
        which_set = parameters.get("which_set", Set.TEST)
        batch_size = parameters.get("batch_size", 64)
        dataset = self.data_reader.get_emotion_data(
            self.emotions, which_set, batch_size, parameters
        ).map(lambda x, y: (tf.image.grayscale_to_rgb(x), y))

        if not self.model:
            raise RuntimeError(
                "Please load or train the model before inference!"
            )
        results = self.model.predict(dataset)
        return np.argmax(results, axis=1)


def _main():  # pragma: no cover
    classifier = VGG16Classifier()
    parameters = {
        "epochs": 30,
        "batch_size": 64,
        "patience": 8,
        "learning_rate": 0.0001,
        "deep": True,
        "dropout": 0.4,
        "frozen_layers": 0,
        "l1": 0,
        "l2": 1e-05,
        "augment": True,
        "weighted": False,
        "balanced": False,
    }
    save_path = os.path.join("models", "image", "vgg16")
    training_loop(classifier, parameters, save_path)


if __name__ == "__main__":  # pragma: no cover
    _main()
