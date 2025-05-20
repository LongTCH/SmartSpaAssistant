import json
import os
import random
import uuid

import requests
from faker import Faker

fake = Faker("vi_VN")  # Tiếng Việt


def generate_sample_customer():
    gender = random.choice(["male", "female"])
    name = fake.name_male() if gender == "male" else fake.name_female()
    id = str(uuid.uuid4())
    random_image = fake.image_url(width=200, height=200)
    # download image from random_image and save to /static/images
    save_path = os.path.join(
        os.path.abspath(os.getcwd()), "static", "images", f"{id}.jpg"
    )
    with open(save_path, "wb") as f:
        f.write(requests.get(random_image).content)
    # Lấy đường dẫn của ảnh đã tải xuống
    host = "http://longtch.id.vn"
    image_path = f"{host}/static/images/{id}.jpg"

    return {
        # Trường này sẽ là Guest.id và cũng dùng để liên kết GuestInfo.guest_id
        "id": id,
        # Các trường cho Guest model
        "provider": random.choice(["messenger", "web"]),
        "account_id": str(fake.random_number(digits=15, fix_len=True)),
        "account_name": fake.user_name(),
        "avatar": image_path,
        "assigned_to": random.choice(["ai", "me"]),
        "info": {
            "fullname": name,
            "gender": gender,
            "birthday": fake.date_of_birth(minimum_age=20, maximum_age=40).strftime(
                "%Y-%m-%d"
            ),
            "phone": fake.phone_number(),
            "email": fake.email(),
            "address": fake.address().replace("\n", ", "),
        },
    }


# Tạo danh sách 100 khách hàng
sample_customers = [generate_sample_customer() for _ in range(100)]

# In ra kết quả vào file customers.json
output_filename = os.path.join(os.path.dirname(__file__), "customers.json")
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(sample_customers, f, ensure_ascii=False, indent=2)

print(
    f"'{output_filename}' generated successfully with {len(sample_customers)} customers."
)
