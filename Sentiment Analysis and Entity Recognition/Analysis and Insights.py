from pymongo import MongoClient
from textblob import TextBlob
from concurrent.futures import ThreadPoolExecutor

# Connect to MongoDB using URI with `tlsAllowInvalidCertificates=true` in the URI
uri = "mongodb+srv://hamadanihadi04:Hadi_1233@datascience.ojdba.mongodb.net/?retryWrites=true&w=majority&appName=DataScience&tlsAllowInvalidCertificates=true"
client = MongoClient(uri)

# Access the database and collection
db = client["Al_Mayadeen"]  # Your database name
collection = db["Articles"]  # Your collection name


# Function to analyze sentiment
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0:
        return 'positive'
    elif sentiment < 0:
        return 'negative'
    else:
        return 'neutral'


# Function to process each article
def process_article(article):
    try:
        # Get the full text of the article
        article_text = article.get('full_text', '')

        # Analyze sentiment
        sentiment_result = analyze_sentiment(article_text)

        # Update the article document with sentiment
        collection.update_one(
            {'_id': article['_id']},  # Filter by article ID
            {'$set': {'sentiment': sentiment_result}}  # Update with sentiment result
        )
        return article['_id']  # Return the article ID for progress tracking
    except Exception as e:
        print(f"Error processing article {article['_id']}: {str(e)}")
        return None


# Get all articles from the collection
try:
    articles = list(collection.find())
    print(f"Found {len(articles)} articles for sentiment analysis.")
except Exception as e:
    print(f"Error fetching articles: {str(e)}")
    client.close()
    exit()

# Use ThreadPoolExecutor to process articles concurrently
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit all articles for processing
    results = list(executor.map(process_article, articles))

print(f"Sentiment analysis completed for {len(results)} articles and updated in MongoDB!")

# Close the client connection
client.close()
