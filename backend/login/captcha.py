import random
import string
import base64
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from .database import get_db
from .models import Captcha
from . import models, schemas
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import delete
# In-memory storage for captchas (in production, use Redis or database)
# captcha_storage = {}

def generate_captcha(width=200, height=80, db: Session = Depends(get_db)):
    # Generate random text (6 characters)
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Create image
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Use a truetype font if available
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Draw text with random positioning and rotation
    for i, char in enumerate(captcha_text):
        draw.text(
            (20 + i * 30 + random.randint(-5, 5), 20 + random.randint(-5, 5)),
            char,
            font=font,
            fill=(random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))
        )
    
    # Add noise
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    # Generate unique ID
    captcha_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    # Store captcha with expiration (5 minutes)
    # captcha_storage[captcha_id] = {
    #     'text': captcha_text,
    #     'expires': datetime.now() + timedelta(minutes=5)
    # }
    
    # Convert image to base64
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    db.add(Captcha(id=captcha_id, captcha=captcha_text, expire_time=300+int(time.time())))
    db.commit()
    return {
        'captcha_id': captcha_id,
        'captcha_image': img_str
    }

def validate_captcha(captcha_id: str, user_input: str, db: Session) -> bool:
    # if captcha_id not in captcha_storage:
    #     return False
    
    captcha_data = db.query(Captcha).filter(Captcha.id == captcha_id).first()
    if captcha_data is None:
        return False
    # Check expiration
    if time.time() > captcha_data.expire_time:
        db.delete(captcha_data)
        db.execute(
            delete(Captcha).where(Captcha.expire_time < time.time())
        )
        db.commit()
        return False
    
    # Validate input (case insensitive)
    is_valid = user_input.upper() == captcha_data.captcha.upper()
    
    # Remove captcha after validation (one-time use)
    db.delete(captcha_data)
    db.execute(
        delete(Captcha).where(Captcha.expire_time < time.time())
    )
    db.commit()
    return is_valid
