import cohere
from app.configs import env_config

cohere_client = cohere.Client(env_config.COHERE_API_KEY)
