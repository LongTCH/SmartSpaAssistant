import json
import os
import random
import uuid

from faker import Faker

fake = Faker("vi_VN")  # Tiếng Việt

avatar_urls = [
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501605/cld-sample.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501606/cld-sample-2.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501605/cld-sample-3.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501606/cld-sample-4.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501606/cld-sample-5.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501605/samples/woman-on-a-football-field.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501605/samples/dessert-on-a-plate.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501605/samples/upscale-face-1.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501604/samples/cup-on-a-table.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501604/samples/coffee.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501604/samples/man-portrait.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501604/samples/chair-and-coffee-table.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501604/samples/man-on-a-street.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501604/samples/man-on-a-escalator.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501604/samples/outdoor-woman.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501604/samples/look-up.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501603/samples/breakfast.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501603/samples/smile.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501602/samples/balloons.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501601/samples/shoe.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501600/samples/two-ladies.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501598/samples/animals/kitten-playing.gif",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501598/samples/landscapes/nature-mountains.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501598/samples/cloudinary-group.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501597/samples/food/spices.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501597/samples/imagecon-group.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501597/samples/ecommerce/accessories-bag.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501597/samples/ecommerce/leather-bag-gray.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501597/samples/people/bicycle.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501597/samples/ecommerce/car-interior-design.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501597/samples/landscapes/beach-boat.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501597/samples/landscapes/architecture-signs.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/animals/three-dogs.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/bike.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/people/jazz.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/people/boy-snow-hoodie.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/landscapes/girl-urban-view.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/sheep.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501596/samples/people/smiling-man.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501595/samples/food/pot-mussels.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501595/samples/animals/reindeer.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501595/samples/food/fish-vegetables.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501595/samples/people/kitchen-bar.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501595/samples/food/dessert.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501595/samples/animals/cat.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501595/samples/ecommerce/analog-classic.jpg",
    "https://res.cloudinary.com/dgmopesja/image/upload/v1748501594/sample.jpg",
]


def generate_sample_customer(index: int):
    gender = random.choice(["male", "female"])
    name = fake.name_male() if gender == "male" else fake.name_female()
    id = str(uuid.uuid4())
    # get avatar url at index % len(avatar_urls)
    avatar_url = avatar_urls[index % len(avatar_urls)]

    return {
        # Trường này sẽ là Guest.id và cũng dùng để liên kết GuestInfo.guest_id
        "id": id,
        # Các trường cho Guest model
        "provider": random.choice(["messenger", "web"]),
        "account_id": str(fake.random_number(digits=15, fix_len=True)),
        "account_name": fake.user_name(),
        "avatar": avatar_url,
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
sample_customers = [generate_sample_customer(i) for i in range(100)]

# In ra kết quả vào file customers.json
output_filename = os.path.join(os.path.dirname(__file__), "customers.json")
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(sample_customers, f, ensure_ascii=False, indent=2)

print(
    f"'{output_filename}' generated successfully with {len(sample_customers)} customers."
)
