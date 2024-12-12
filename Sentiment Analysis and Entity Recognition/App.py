from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime
import certifi
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

# MongoDB connection string
uri = "mongodb+srv://hamadanihadi04:Hadi_1233@datascience.ojdba.mongodb.net/?retryWrites=true&w=majority&appName=DataScience"
client = MongoClient(uri, tlsCAFile=certifi.where())
db = client["Al_Mayadeen"]
collection = db["Articles"]

# 1. Top Keywords
@app.route('/top_keywords', methods=['GET'])
def top_keywords():
    pipeline = [
        {"$unwind": "$keywords"},
        {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 2. Top Authors
@app.route('/top_authors', methods=['GET'])
def top_authors():
    pipeline = [
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 3. Articles by Date
@app.route('/articles_by_date', methods=['GET'])
def articles_by_date():
    try:
        pipeline = [
            {
                "$addFields": {
                    "published_time": {
                        "$toDate": "$published_time"
                    }
                }
            },
            {
                "$group": {
                    "_id": "$published_time",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}  # Sort by date ascending
            },
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "count": 1
                }
            }
        ]

        result = list(collection.aggregate(pipeline))
        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 4. Articles by Word Count
@app.route('/articles_by_word_count', methods=['GET'])
def articles_by_word_count():
    pipeline = [
        {"$group": {"_id": "$word_count", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 5. Articles by Language
@app.route('/articles_by_language', methods=['GET'])
def articles_by_language():
    pipeline = [
        {"$group": {"_id": "$lang", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 6. Articles by Category (Classes)
@app.route('/articles_by_classes', methods=['GET'])
def articles_by_classes():
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 7. Recent Articles
@app.route('/recent_articles', methods=['GET'])
def recent_articles():
    try:
        # Find the most recent 10 articles sorted by published_time in descending order
        result = list(collection.find().sort("published_time", -1).limit(10))

        # Convert ObjectId to string for JSON serialization and format the result
        for article in result:
            if '_id' in article:
                article['_id'] = str(article['_id'])

        # Check if the result is empty
        if not result:
            return jsonify({"message": "No recent articles found"}), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 8. Articles by Keyword
@app.route('/articles_by_keyword/<keyword>', methods=['GET'])
def articles_by_keyword(keyword):
    pipeline = [
        {"$match": {"keywords": keyword}},
        {"$project": {"_id": 0, "postid": 1, "title": 1, "author": 1, "published_time": 1, "url": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 9. Articles by Author
@app.route('/articles_by_author/<author_name>', methods=['GET'])
def articles_by_author(author_name):
    pipeline = [
        {"$match": {"author": author_name}},
        {"$project": {"_id": 0, "postid": 1, "title": 1, "published_time": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 9.1 all authors
@app.route('/all_authors', methods=['GET'])
def all_authors():
    authors = collection.distinct("author")  # Get distinct authors from MongoDB
    return jsonify(authors)

# 10. Top Classes
@app.route('/top_classes', methods=['GET'])
def top_classes():
    limit = int(request.args.get('limit', 10))  # Get the limit from query parameters, default to 10
    pipeline = [
        {"$unwind": "$classes"},
        {"$group": {"_id": "$classes", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 11. Article Details
@app.route('/article_details/<postid>', methods=['GET'])
def article_details(postid):
    result = collection.find_one({"postid": postid}, {"_id": 0})
    return jsonify(result)

# 12. Articles Containing Video
@app.route('/articles_with_video', methods=['GET'])
def articles_with_video():
    pipeline = [
        {"$match": {"video_duration": {"$ne": None}}},
        {"$project": {"_id": 0, "postid": 1, "title": 1, "video_duration": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 13. Articles by Publication Year
@app.route('/articles_by_year/<int:year>', methods=['GET'])
def articles_by_year(year):
    try:
        # Define the start and end dates for the year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)

        # Define the aggregation pipeline
        pipeline = [
            {
                "$addFields": {
                    "published_time": {
                        "$toDate": "$published_time"  # Cast to date
                    }
                }
            },
            {
                "$match": {
                    "published_time": {"$gte": start_date, "$lt": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "month": {"$month": "$published_time"},
                        "year": {"$year": "$published_time"}
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {
                    "_id.year": 1,
                    "_id.month": 1
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "month": "$_id.month",
                    "year": "$_id.year",
                    "count": 1
                }
            }
        ]

        # Execute the aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # If no results, return a message indicating no data found
        if not result:
            return jsonify({"message": "No articles found for the specified year."})

        # Return the results
        return jsonify(result)

    except OperationFailure as e:
        # Return an error message if the aggregation fails
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        # Return an error message if something goes wrong
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 14. Longest Articles
@app.route('/longest_articles', methods=['GET'])
def longest_articles():
    try:
        # Retrieve and sort the articles by word_count in descending order
        cursor = collection.find().sort("word_count", -1).limit(10)

        # Convert each document to a dictionary and convert _id to string
        result = []
        for doc in cursor:
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            result.append(doc)

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 15. Shortest Articles
@app.route('/shortest_articles', methods=['GET'])
def shortest_articles():
    try:
        # Retrieve and sort the articles by word_count in ascending order
        cursor = collection.find().sort("word_count", 1).limit(10)

        # Convert each document to a dictionary and convert _id to string
        result = []
        for doc in cursor:
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            result.append(doc)

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 16. Articles by Keyword Count
@app.route('/articles_by_keyword_count', methods=['GET'])
def articles_by_keyword_count():
    pipeline = [
        {"$project": {"keyword_count": {"$size": "$keywords"}}},
        {"$group": {"_id": "$keyword_count", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 17. Articles with Thumbnail
@app.route('/articles_with_thumbnail', methods=['GET'])
def articles_with_thumbnail():
    pipeline = [
        {"$match": {"thumbnail": {"$ne": None}}},
        {"$project": {"_id": 0, "postid": 1, "title": 1, "thumbnail": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 18. Articles Updated After Publication
@app.route('/articles_updated_after_publication', methods=['GET'])
def articles_updated_after_publication():
    pipeline = [
        {"$match": {"$expr": {"$gt": ["$last_updated", "$published_time"]}}},
        {"$project": {"_id": 0, "postid": 1, "title": 1, "last_updated": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)
# count updated articles
@app.route('/count_updated_articles', methods=['GET'])
def count_updated_articles():
    # Define the query to find articles updated after publication
    pipeline = [
        {
            '$match': {
                '$expr': {
                    '$gt': ['$last_updated', '$published_time']
                }
            }
        },
        {
            '$count': 'count'
        }
    ]

    # Execute the aggregation pipeline
    result = list(collection.aggregate(pipeline))

    # Get the count from the result
    count = result[0]['count'] if result else 0

    return jsonify({"count": count})

# 19. Articles by Coverage
@app.route('/articles_by_coverage/<coverage>', methods=['GET'])
def articles_by_coverage(coverage):
    try:
        # Aggregate pipeline to match documents where 'coverage' exists in 'classes'
        pipeline = [
            {
                "$match": {
                    "classes": {
                        "$elemMatch": {
                            "mapping": "coverage",
                            "value": coverage
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "postid": 1,
                    "title": 1,
                    "published_time": 1
                }
            }
        ]

        result = list(collection.aggregate(pipeline))
        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 20. Most Popular Keywords in the Last X Days
@app.route('/popular_keywords_last_<int:x>_days', methods=['GET'])
def popular_keywords_last_X_days(x):
    try:
        # Calculate the date threshold
        date_threshold = datetime.utcnow() - timedelta(days=x)

        # Aggregation pipeline
        pipeline = [
            {
                "$addFields": {
                    "published_time": {
                        "$dateFromString": {
                            "dateString": "$published_time",
                            "onError": None  # Handle invalid date strings
                        }
                    }
                }
            },
            {
                "$match": {
                    "published_time": {
                        "$gte": date_threshold
                    }
                }
            },
            {
                "$unwind": "$keywords"  # Unwind the keywords array
            },
            {
                "$group": {
                    "_id": "$keywords",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 10
            }
        ]

        # Execute aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if the result is empty
        if not result:
            return jsonify({"message": "No keywords found for the specified period"}), 404

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 21. Articles by Published Month
@app.route('/articles_by_month/<int:year>/<int:month>', methods=['GET'])
def articles_by_month(year, month):
    try:
        # Calculate the start and end dates for the specified month
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)

        # Aggregation pipeline
        pipeline = [
            {
                "$addFields": {
                    "published_time": {
                        "$dateFromString": {
                            "dateString": "$published_time",
                            "onError": None  # Handle invalid date strings
                        }
                    }
                }
            },
            {
                "$match": {
                    "published_time": {
                        "$gte": start_date,
                        "$lt": end_date
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "postid": 1,
                    "title": 1,
                    "published_time": 1
                }
            }
        ]

        # Execute aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if the result is empty
        if not result:
            return jsonify({"message": "No articles found for the specified month"}), 404

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 22. Articles by Word Count Range
@app.route('/articles_by_word_count_range/<int:min>/<int:max>', methods=['GET'])
def articles_by_word_count_range(min, max):
    try:
        # Aggregation pipeline
        pipeline = [
            {
                "$match": {
                    "word_count": {
                        "$gte": min,
                        "$lte": max
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "postid": 1,
                    "title": 1,
                    "word_count": 1
                }
            }
        ]

        # Execute aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if the result is empty
        if not result:
            return jsonify({"message": "No articles found for the specified word count range"}), 404

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 23. Articles with Specific Keyword Count
@app.route('/articles_with_specific_keyword_count/<int:count>', methods=['GET'])
def articles_with_specific_keyword_count(count):
    try:
        pipeline = [
            {"$project": {"keyword_count": {"$size": "$keywords"}, "postid": 1, "title": 1, "published_time": 1}},
            {"$match": {"keyword_count": count}},
            {"$limit": 10}  # Adjust this limit as needed
        ]
        result = list(collection.aggregate(pipeline))

        # Convert ObjectId to string directly in the route
        for doc in result:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        # Check if no articles were found
        if not result:
            return jsonify({"message": f"No articles found with exactly {count} keywords."}), 404

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 24. Articles by Specific Date
@app.route('/articles_by_specific_date/<date>', methods=['GET'])
def articles_by_specific_date(date):
    try:
        # Parse the date string into a datetime object
        try:
            specific_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

        # Create start and end dates for the day
        start_date = specific_date
        end_date = start_date + timedelta(days=1)

        # Aggregation pipeline to find articles by specific date
        pipeline = [
            {
                "$addFields": {
                    "published_time": {"$toDate": "$published_time"}  # Ensure published_time is a date
                }
            },
            {
                "$match": {
                    "published_time": {"$gte": start_date, "$lt": end_date}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "postid": 1,
                    "title": 1,
                    "published_time": 1
                }
            }
        ]

        # Execute the aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if no articles were found for the date
        if not result:
            return jsonify({"message": f"No articles found for the date {date}."}), 404

        # Format the response with articles grouped by the specified date
        response = {
            "date": date,
            "articles": result
        }

        return jsonify(response)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 25 articles with a specific text
@app.route('/articles_containing_text/<text>', methods=['GET'])
def articles_containing_text(text):
    try:
        # Aggregation pipeline to find articles containing specific text in full_text
        pipeline = [
            {
                "$match": {
                    "full_text": {"$regex": text, "$options": "i"}  # Case-insensitive search for the text
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "postid": 1,
                    "title": 1,
                    "full_text": 1,
                    "published_time": 1
                }
            },
            {
                "$limit": 10  # Adjust limit as needed
            }
        ]

        # Execute the aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if no articles were found
        if not result:
            return jsonify({"message": f"No articles found containing the text '{text}'."}), 404

        # Format the response with articles containing the specified text
        response = {
            "text": text,
            "articles": result
        }

        return jsonify(response)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 26. Articles by Word Count Over X
@app.route('/articles_by_word_count_over/<int:x>', methods=['GET'])
def articles_by_word_count_over(x):
    pipeline = [
        {"$match": {"word_count": {"$gt": x}}},
        {"$project": {"_id": 0, "postid": 1, "title": 1, "word_count": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    return jsonify(result)

# 27. Articles by Word Count Under X
@app.route('/articles_by_word_count_under/<int:x>', methods=['GET'])
def articles_by_word_count_under(x):
    try:
        # Aggregation pipeline
        pipeline = [
            {"$match": {"word_count": {"$lt": x}}},
            {"$project": {"_id": 0, "postid": 1, "title": 1, "word_count": 1}}
        ]

        # Execute aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if the result is empty
        if not result:
            return jsonify({"message": "No articles found with word count under the specified limit"}), 404

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 28. articles grouped by coverage
@app.route('/articles_grouped_by_coverage', methods=['GET'])
def articles_grouped_by_coverage():
    try:
        # Aggregation pipeline to group articles by the 'coverage' field in 'classes'
        pipeline = [
            {
                "$unwind": "$classes"  # Unwind the 'classes' array
            },
            {
                "$match": {
                    "classes.mapping": "coverage"  # Ensure we are matching coverage
                }
            },
            {
                "$group": {
                    "_id": "$classes.value",  # Group by the coverage category
                    "article_count": {"$sum": 1}  # Count the number of articles
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "coverage": "$_id",
                    "article_count": 1
                }
            }
        ]

        # Execute the aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if no articles were found
        if not result:
            return jsonify({"message": "No articles found for any coverage category."}), 404

        # Format the response with coverage and article counts
        response = {
            "coverage_summary": result
        }

        return jsonify(response)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 29 articles last x hours
@app.route('/articles_last_X_hours/<int:x>', methods=['GET'])
def articles_last_X_hours(x):
    try:
        # Calculate the time threshold (current time minus X hours)
        time_threshold = datetime.utcnow() - timedelta(hours=x)

        # Aggregation pipeline
        pipeline = [
            {
                "$addFields": {
                    "published_time": {
                        "$dateFromString": {
                            "dateString": "$published_time",
                            "onError": None  # Handle invalid date strings
                        }
                    }
                }
            },
            {
                "$match": {
                    "published_time": {
                        "$gte": time_threshold  # Filter articles published in the last X hours
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "published_time": 1
                }
            },
            {
                "$sort": {
                    "published_time": -1  # Sort articles by most recent first
                }
            }
        ]

        # Execute aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if no articles were found
        if not result:
            return jsonify({"message": f"No articles found in the last {x} hours."}), 404

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 30 most articles by title length
@app.route('/articles_by_title_length', methods=['GET'])
def articles_by_title_length():
    try:
        # Aggregation pipeline
        pipeline = [
            {
                "$addFields": {
                    "title_length": {
                        "$size": {
                            "$split": ["$title", " "]  # Split the title into words and count them
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$title_length",  # Group by the length of the title
                    "count": {"$sum": 1}  # Count the number of articles for each title length
                }
            },
            {
                "$sort": {"_id": 1}  # Sort by title length in ascending order
            }
        ]

        # Execute aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if no articles were found
        if not result:
            return jsonify({"message": "No articles found."}), 404

        # Format the result to include title length in the message
        formatted_result = [
            {
                "title_length": item["_id"],
                "count": item["count"]
            } for item in result
        ]

        return jsonify(formatted_result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

# 31 most updated artciles
@app.route('/most_updated_articles', methods=['GET'])
def most_updated_articles():
    try:
        # Aggregation pipeline
        pipeline = [
            {
                "$match": {
                    "$expr": {"$gt": ["$last_updated", "$published_time"]}  # Only articles updated after publication
                }
            },
            {
                "$addFields": {
                    "update_count": {
                        "$cond": {
                            "if": {"$isArray": "$last_updated"},  # Check if last_updated is an array
                            "then": {"$size": "$last_updated"},  # Count the number of updates (array size)
                            "else": 1  # If not an array, but updated, count as 1 update
                        }
                    }
                }
            },
            {
                "$match": {
                    "update_count": {"$gt": 0}  # Ensure articles have been updated at least once
                }
            },
            {
                "$sort": {"update_count": -1}  # Sort articles by number of updates (most to least)
            },
            {
                "$limit": 10  # Limit to the top 10 most updated articles
            },
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "update_count": 1,  # Include the number of updates
                    "last_updated": 1  # Optionally include the last updated time(s)
                }
            }
        ]

        # Execute the aggregation pipeline
        result = list(collection.aggregate(pipeline))

        # Check if no articles were found
        if not result:
            return jsonify({"message": "No updated articles found."}), 404

        return jsonify(result)

    except OperationFailure as e:
        return jsonify({"error": "MongoDB operation failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)