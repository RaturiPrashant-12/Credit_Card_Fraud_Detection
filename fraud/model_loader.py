# model_loader.py
import os
from django.conf import settings
import logging
from joblib import load

logger = logging.getLogger(__name__)

MODEL_REL_PATH = os.path.join('model', 'fraud_pipeline.joblib')

def get_model():
    """
    Return the loaded model pipeline, or None if not present.
    Logs any errors and returns None on failure.
    """
    model_path = os.path.join(settings.BASE_DIR, MODEL_REL_PATH)

    if not os.path.exists(model_path):
        logger.error("Model file not found at: %s", model_path)
        return None

    try:
        model = load(model_path)
        logger.info("Model loaded from %s", model_path)
        return model
    except Exception as e:
        logger.exception("Failed to load model from %s: %s", model_path, e)
        return None
