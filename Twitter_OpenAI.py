import json
import requests
import pandas
import openai
from ratelimiter import RateLimiter

# Uses requests to access the API, then stores the non-meta tagged items into a list that's organized as per requirementes
#NOTES: rate limited via wrapper
#NOTES: Bearer token is used instead of API Key for apps. API Key will not work
#NOTES: Max results have been changed from the default 10 -> 30
@RateLimiter(max_calls=450, period=900)
def get_tweets_by_handle(handle: str, api_key: str) -> list:
    response = requests.get("https://api.twitter.com/2/tweets/search/recent",
                            headers={"Authorization": f"Bearer {api_key}"},
                            params={"query": f"from:{handle}",
                                    "max_results": 30}
                            )

    orig_tweets = response.json()["data"]
    tweets = []
    for item in orig_tweets:
        tweets.append(
            {"handle": handle, "tweet": item["text"], "tweet_id": item["id"]})

    return tweets

# Openai API general text processor is used with a risk chance of 0 via "temperature"
# Prompts are passed in as a string, the result is then recieved and the text value is extracted and interpreted as a bool value
#NOTES: rate limited via wrapper
#NOTES: Openai also uses Bearer Token
@RateLimiter(max_calls=20, period=60)
def check_deal_from_tweet(tweet: str, api_key: str) -> bool:
    next_prompts = "Decide whether the Tweet's contains a deal with a True, or False.\nTweet: \"" + tweet + "\"\nhasDeal:"

    openai.api_key = api_key
    response = openai.Completion.create(model="text-davinci-003",
                                        prompt=next_prompts, temperature=0,
                                        )

    prediction = response["choices"][0]["text"]
    if "True" in prediction:
        return True
    if "False" in prediction:
        return False

# Extra print statements are included for clarity sake
def main():
    # As per OAuth 2.0, Bearer Tokens are used instead of API keys (Specifically for this use case)
    twitter_api_key = input("Please enter your twitter Bearer Token:")
    #twitter_api_key = "AAAAAAAAAAAAAAAAAAAAAC%2FblQEAAAAAL%2FG7kawvPURvYWNaoJgkrdqfMsg%3DcYmWz6RzDgJxkAbhsAgyNdtXc0qf2MqmDlc13cZr1bnJhG60Lb"
    openai_api_key = input("Please enter your OpenAI API key:")
    #openai_api_key = "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"
    handle = 'RedFlagDeals'
    output = []

    print("Retrieving tweets...\n")
    tweets = get_tweets_by_handle(handle, twitter_api_key)
    # The pandas display created for comparison reasons
    original_pandas = pandas.DataFrame(tweets)
    print(original_pandas)
    print("-------------------------")
    print("Calling OpenAi. This can be a slow process.")
    print("Rate limited to 20 request per minute.")
    print("It will freeze for an alloted time after rate limit reached and then resume.\n")
    
    # Iterate over all the tweets and get prediction
    processed_tweet_count = 1
    for tweet in tweets:
        print("Currently processing tweet #" + str(processed_tweet_count))
        processed_tweet_count = processed_tweet_count + 1
        cur_tweet = tweet["tweet"]
        has_deal = check_deal_from_tweet(cur_tweet, openai_api_key)
        tweet.update({"hasDeal": has_deal})
        output.append(tweet)

    # OUTPUTS as per requirement
    pandas_output = pandas.DataFrame(output)
    print(pandas_output)
    print("-------------------------")
    output = json.dumps(output, indent=4)
    print(output)
    print("-----------END-----------")


if __name__ == "__main__":
    main()