import json
import os
import uuid

interests = [
    {
        "id": str(uuid.uuid4()),
        "name": "nâng mũi",
        "related_terms": "nâng mũi, phẫu thuật nâng mũi, mũi cao, làm mũi cao",
        "status": "published",
        "color": "#FF5733",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "tiêm filler",
        "related_terms": "tiêm filler, làm đầy, tiêm chất làm đầy",
        "status": "published",
        "color": "#33FF57",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "trẻ hóa da",
        "related_terms": "trẻ hóa da, làm trẻ, trẻ hóa làn da",
        "status": "published",
        "color": "#3357FF",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "giảm béo",
        "related_terms": "giảm béo, giảm cân, giảm mỡ",
        "status": "published",
        "color": "#FF33A1",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "chăm sóc da",
        "related_terms": "chăm sóc da, làm đẹp da, dưỡng da",
        "status": "published",
        "color": "#FF33FF",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "trị mụn",
        "related_terms": "trị mụn, làm sạch mụn, điều trị mụn",
        "status": "published",
        "color": "#33FFF5",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "xóa xăm",
        "related_terms": "xóa xăm, xóa hình xăm, làm sạch hình xăm",
        "status": "published",
        "color": "#FF5733",
    },
]
output_filename = os.path.join(os.path.dirname(__file__), "interests.json")
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(interests, f, ensure_ascii=False, indent=4)
print(f"Data exported to {output_filename}")
