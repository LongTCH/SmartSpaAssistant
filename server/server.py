import requests

# Delete points (POST /collections/:collection_name/points/delete)
response = requests.post(
    "http://localhost:6333/collections/spa_knowledge/points/delete",
    headers={
        "Content-Type": "application/json"
    },
    json={
        "filter": {
            "must": [
                {
                    "key": "file_id",
                    "match": {
                        "any": [
                           "13db6bgD9T-sKZqT6r-6xXA_yOqvxMaprZ7j7jsnhOnc",
                           "1ct45E0kWnwXRNKGJpHNtditQofJElOah-brcMkRIYxk"
                        ]
                    }
                }
            ]
        },
        "wait": True
    },
)

print(response.json())
