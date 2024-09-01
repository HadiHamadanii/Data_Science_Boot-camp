from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime
import certifi

app = Flask(__name__)

# MongoDB connection string
uri = "mongodb+srv://hamadanihadi04:Hadi_1233@datascience.ojdba.mongodb.net/?retryWrites=true&w=majority&appName=DataScience"
client = MongoClient(uri, tlsCAFile=certifi.where())
db = client["Al_Mayadeen"]
collection = db["Articles"]


# Function to update existing date strings to ISODate format
def update_existing_dates():
    for document in collection.find({"published_date": {"$type": "string"}}):
        try:
            # Convert string to datetime
            iso_date = datetime.strptime(document["published_date"], "%Y-%m-%dT%H:%M:%S.%f")

            # Update the document with the ISODate
            collection.update_one(
                {"_id": document["_id"]},
                {"$set": {"published_date": iso_date}}
            )
        except ValueError:
            print(f"Skipping document with invalid date format: {document['_id']}")


# Optionally run this function when the app starts to update existing data
update_existing_dates()


# 1. Top Keywords
@app.route('/top_keywords', methods=['GET'])
def top_keywords():
    pipeline = [
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 2. Top Authors
@app.route('/top_authors', methods=['GET'])
def top_authors():
    pipeline = [
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 3. Articles by Date
@app.route('/articles_by_date', methods=['GET'])
def articles_by_date():
    pipeline = [
        {"$group": {"_id": "$published_date", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 4. Articles by Word Count
@app.route('/articles_by_word_count', methods=['GET'])
def articles_by_word_count():
    pipeline = [
        {"$project": {"word_count": {"$strLenCP": "$content"}}},
        {"$group": {"_id": "$word_count", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 5. Articles by Language
@app.route('/articles_by_language', methods=['GET'])
def articles_by_language():
    pipeline = [
        {"$group": {"_id": "$language", "count": {"$sum": 1}}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 6. Articles by Category
@app.route('/articles_by_classes', methods=['GET'])
def articles_by_classes():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 7. Recent Articles
@app.route('/recent_articles', methods=['GET'])
def recent_articles():
    results = list(collection.find().sort("published_date", -1).limit(10))
    for doc in results:
        doc["published_date"] = doc["published_date"].isoformat()  # Convert datetime to string for JSON response
    return jsonify(results)


# 8. Articles by Keyword
@app.route('/articles_by_keyword/<keyword>', methods=['GET'])
def articles_by_keyword(keyword):
    results = list(collection.find({"keywords": keyword}))
    return jsonify(results)


# 9. Articles by Author
@app.route('/articles_by_author/<author_name>', methods=['GET'])
def articles_by_author(author_name):
    results = list(collection.find({"author": author_name}))
    return jsonify(results)


# 10. Top Classes
@app.route('/top_classes', methods=['GET'])
def top_classes():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 11. Article Details
@app.route('/article_details/<postid>', methods=['GET'])
def article_details(postid):
    result = collection.find_one({"postid": postid})
    if result:
        result["published_date"] = result["published_date"].isoformat()  # Convert datetime to string for JSON response
    return jsonify(result)


# 12. Articles Containing Video
@app.route('/articles_with_video', methods=['GET'])
def articles_with_video():
    results = list(collection.find({"video_duration": {"$ne": None}}))
    return jsonify(results)


# 13. Articles by Publication Year
@app.route('/articles_by_year/<year>', methods=['GET'])
def articles_by_year(year):
    start_date = datetime.strptime(f"{year}-01-01T00:00:00.000000", "%Y-%m-%dT%H:%M:%S.%f")
    end_date = datetime.strptime(f"{year}-12-31T23:59:59.999999", "%Y-%m-%dT%H:%M:%S.%f")
    results = list(collection.find({"published_date": {"$gte": start_date, "$lte": end_date}}))
    return jsonify(results)


# 14. Longest Articles
@app.route('/longest_articles', methods=['GET'])
def longest_articles():
    results = list(collection.find().sort("word_count", -1).limit(10))
    return jsonify(results)


# 15. Shortest Articles
@app.route('/shortest_articles', methods=['GET'])
def shortest_articles():
    results = list(collection.find().sort("word_count", 1).limit(10))
    return jsonify(results)


# 16. Articles by Keyword Count
@app.route('/articles_by_keyword_count', methods=['GET'])
def articles_by_keyword_count():
    pipeline = [
        {"$project": {"keyword_count": {"$size": "$keywords"}}},
        {"$group": {"_id": "$keyword_count", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 17. Articles by Thumbnail Presence
@app.route('/articles_with_thumbnail', methods=['GET'])
def articles_with_thumbnail():
    results = list(collection.find({"thumbnail": {"$ne": None}}))
    return jsonify(results)


# 18. Articles Updated After Publication
@app.route('/articles_updated_after_publication', methods=['GET'])
def articles_updated_after_publication():
    pipeline = [
        {"$match": {"$expr": {"$gt": ["$last_updated", "$published_date"]}}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 19. Articles by Coverage (from classes)
@app.route('/articles_by_coverage/<coverage>', methods=['GET'])
def articles_by_coverage(coverage):
    results = list(collection.find({"classes": coverage}))
    return jsonify(results)


# 20. Most Popular Keywords in the Last X Days
@app.route('/popular_keywords_last_X_days/<int:days>', methods=['GET'])
def popular_keywords_last_X_days(days):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    pipeline = [
        {"$match": {"published_date": {"$gte": start_date}}},
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 21. Articles by Published Month
@app.route('/articles_by_month/<int:year>/<int:month>', methods=['GET'])
def articles_by_month(year, month):
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    results = list(collection.find({"published_date": {"$gte": start_date, "$lt": end_date}}))
    return jsonify(results)


# 22. Articles by Word Count Range
@app.route('/articles_by_word_count_range/<int:min>/<int:max>', methods=['GET'])
def articles_by_word_count_range(min, max):
    pipeline = [
        {"$project": {"word_count": {"$strLenCP": "$content"}}},
        {"$match": {"word_count": {"$gte": min, "$lte": max}}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 23. Articles with Specific Keyword Count
@app.route('/articles_with_specific_keyword_count/<int:count>', methods=['GET'])
def articles_with_specific_keyword_count(count):
    results = list(collection.find({"keywords": {"$size": count}}))
    return jsonify(results)


# 24. Articles by Specific Date
@app.route('/articles_by_specific_date/<date>', methods=['GET'])
def articles_by_specific_date(date):
    try:
        specific_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f")
        results = list(collection.find({"published_date": specific_date}))
        return jsonify(results)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS.SSSSSS"}), 400


# 25. Articles Containing Specific Text
@app.route('/articles_containing_text/<text>', methods=['GET'])
def articles_containing_text(text):
    results = list(collection.find({"content": {"$regex": text, "$options": "i"}}))  # case-insensitive search
    return jsonify(results)


# 26. Articles with More than N Words
@app.route('/articles_with_more_than/<int:word_count>', methods=['GET'])
def articles_with_more_than(word_count):
    pipeline = [
        {"$project": {"word_count": {"$strLenCP": "$content"}}},
        {"$match": {"word_count": {"$gt": word_count}}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 27. Articles Grouped by Coverage
@app.route('/articles_grouped_by_coverage', methods=['GET'])
def articles_grouped_by_coverage():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 28. Articles Published in Last X Hours
@app.route('/articles_last_X_hours/<int:hours>', methods=['GET'])
def articles_last_X_hours(hours):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=hours)
    results = list(collection.find({"published_date": {"$gte": start_date}}))
    return jsonify(results)


# 29. Articles by Day of the Week
@app.route('/articles_by_day_of_week/<int:day>', methods=['GET'])
def articles_by_day_of_week(day):
    pipeline = [
        {"$addFields": {"day_of_week": {"$dayOfWeek": "$published_date"}}},
        {"$match": {"day_of_week": day}}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


# 30. Most Updated Articles
@app.route('/most_updated_articles', methods=['GET'])
def most_updated_articles():
    pipeline = [
        {
            "$project": {
                "title": 1,
                "update_count": {"$subtract": [{"$strLenCP": "$last_updated"}, {"$strLenCP": "$published_date"}]}
            }
        },
        {"$sort": {"update_count": -1}},
        {"$limit": 10}
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
