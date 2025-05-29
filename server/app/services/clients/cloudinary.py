import cloudinary
import cloudinary.uploader
from app.configs import env_config

# Configuration
cloudinary.config(
    cloud_name=env_config.CLOUDINARY_CLOUD_NAME,
    api_key=env_config.CLOUDINARY_API_KEY,
    api_secret=env_config.CLOUDINARY_API_SECRET,
    secure=True,
)


async def upload_image(file: bytes) -> str:
    """
    Upload an image to Cloudinary.
    """
    upload_result = cloudinary.uploader.upload(file)
    return upload_result["secure_url"]
