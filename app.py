import os
import pickle
import re

import googleapiclient.discovery  # youtube api
# import matplotlib.pyplot as plt
import pandas as pd
import spacy
# VADER
import nltk

from nltk.sentiment import SentimentIntensityAnalyzer
from tqdm import tqdm  # to get cool progress bar
from wordcloud import WordCloud

# keyword to be searched
KEYWORD = 'Joe Rogan Podcast'

# max comments to be scraped
MAX = 10


def get_youtube_object(DEVELOPER_KEY):
    # file = open("API_KEY", 'r')  # opening the file containg my API key

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    # DEVELOPER_KEY = file.read()  # reading the API key from the file, did this for security purpose
    youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=DEVELOPER_KEY)
    print("got the youtube object")
    return youtube



# a function to check if the token we are trying to make is actually a meaningful token
# -------------------------------tokenization functions ----------------------------------------------------------------
def is_token_allowed(token):
    return bool(token and str(token).strip() and not token.is_stop and not token.is_punct)


# function to preprocess each token at once
# lemmatization -- get the base word out of the token, e.g. "be" is lemma of "was"
# strip of extra space or punctuation
# convert all to lowercase
def preprocess_token(token):
    return token.lemma_.strip().lower()


# final function which will return a string of created tokens
def create_tokens(string):
    # load the english language
    nlp = spacy.load("en_core_web_sm")

    # create an object of spacy library
    nlp_text = nlp(string)
    complete_filtered_tokens = [preprocess_token(token) for token in nlp_text if is_token_allowed(token)]

    # remove if it is of length 1, i.e. emoticons and other symbols etc.
    complete_filtered_tokens = [x for x in complete_filtered_tokens if len(x) > 1]

    # return the tokens as one complete string
    complete_filtered_tokens = " ".join(complete_filtered_tokens)
    return complete_filtered_tokens


# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------video class-----------------------------------------------------------------

# video class containing all the data associated with each video id containing comments, metaData,channelData
class Video:

    def __init__(self):
        self.comments = 0
        self.metaData = 0
        self.channelData = 0
        print("created video object")

    # a function to check if all the functions work or not
    def do_it_all(self):
        self.process_comments()
        nltk.download('vader_lexicon')
        self.sentiment_analysis()
        self.process_metaData()
        # self.create_commentsCloud()

    # a function to clean and process all the comments and generate tokens from them
    def process_comments(self):
        try:
            # convert 2023-10-21T18:31:54Z to 2023-10-21 18:31:54+00:00
            self.comments["PublishTime"] = pd.to_datetime(self.comments["PublishTime"])
            self.comments["PublishTime"] = self.comments["PublishTime"].dt.strftime("%d %b %Y, %I:%M %p")

            # create tokens out of comments
            self.comments["tokens"] = self.comments["comments"].apply(create_tokens)
            self.comments = self.comments.dropna()
        except Exception as e:
            print(f"error found in Video.process_comments() function: {e}")

    # a function to generate VADER sentiment analysis of the comments
    # only to be used after generating tokens using process_comments() function
    #kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk
    def sentiment_analysis(self):
        try:
            # nltk.download('vader_lexicon')
            SIA = SentimentIntensityAnalyzer()
            results = {}
            for i, row in tqdm(self.comments.iterrows(),"sentiment Analysis"):  # iterate through each row of the comments dataset
                text = row["comments"]
                myid = row["commenter"]
                results[myid] = SIA.polarity_scores(text)  # get the polarity scores and store in dictionary
            Vaders = pd.DataFrame(results).T
            Vaders = Vaders.reset_index().rename(columns={'index': 'commenter'})
            self.comments = Vaders.merge(self.comments, how='left')  # merge and store back in the original variable

            # categorise as positive, negative or neutral based on compound score
            self.comments["sentiment"] = pd.cut(self.comments["compound"], bins=[-1, -0.05, 0.05, 1],
                                                labels=["Negative", "Neutral", "Positive"])

        except Exception as e:
            print(f"error found in Video.sentiment_analysis() function: {e}")

    # function to clean the video metadata
    def process_metaData(self):
        try:
            # removing urls from the video description
            self.metaData["videoDescription"] = re.sub(r"(http.+)|(\n)", "", self.metaData["videoDescription"])

            # changing vidLen string into seconds
            k = re.search(r"(?P<hour>\d+H)?(?P<min>\d+M)?(?P<sec>\d+S)", self.metaData["vidLen(sec)"])
            if k:
                hours = int(k["hour"][:-1]) if k["hour"] else 0
                minutes = int(k["min"][:-1]) if k["min"] else 0
                seconds = int(k["sec"][:-1]) if k["sec"] else 0
                self.metaData["vidLen(sec)"] = hours * 3600 + minutes * 60 + seconds
            else:
                print("wrong video duration format")

            # convert 2023-10-21T18:31:54Z to 2023-10-21 18:31:54+00:00
            self.metaData["videoPublishTime"] = pd.to_datetime(self.metaData["videoPublishTime"])

        except Exception as e:
            print(f"error found in Video.process_metaData() function: {e}")

    # create a word cloud to see the most used words in the comments
    def create_commentsCloud(self, sentiment_type=None):  # cloud for positive negative or neutral
        if sentiment_type is None:
            sentiment_type = ["Positive", "Negative",
                              "Neutral"]
        words = " ".join(self.comments[self.comments["sentiment"].isin(sentiment_type)]["tokens"])
        word_cloud = WordCloud(margin= 0, max_words=100, background_color=(14,17,23), collocations=True).generate(words)
        return word_cloud



# ----------------------------------------------------------------------------------------------------------------------

# ---------------------------------------- Search classe----------------------------------------------------------------
# a search class which contains data about top 5 search results
class Search:
    def __init__(self, keyword, youtube, order_by="relevance"):
        request = youtube.search().list(
            part="snippet",
            maxResults=5,
            order=order_by,
            q=keyword,
            type="video"
        )
        response = request.execute()
        print("Successfully got response object")
        self.IDs = {}
        for item in response["items"]:
            self.IDs[item["id"]["videoId"]] = item["snippet"][
                "channelId"]  # keys are video ids and values are channel ids
        print("stored video ids and channel ids in self.IDs")
        # print(self.IDs)

        self.videos = {}
        for video in self.IDs.keys():
            self.videos[video] = Video()

        self.get_video_meta_data(youtube)  # a call is made when an instance of search class is created
        self.get_comments(youtube)  # a call is made when an instance of search class is created
        self.get_channel_meta_data(youtube)

    # a function to get top comments[upto MAX] for all the top search results and store as dataframe
    def get_comments(self, youtube):
        for vID in tqdm(self.IDs.keys(),"get comments"):
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=vID, maxResults=100  # ,order='time'
            )

            response = request.execute()

            comments = []
            commenter = []
            publishedAt = []
            totalReplyCount = []
            likeCount = []
            for item in response['items']:  # get all top level comments on the first page of the video
                snippet = item['snippet']['topLevelComment']['snippet']

                comments.append(snippet['textOriginal'])
                commenter.append(snippet['authorDisplayName'])
                publishedAt.append(snippet['updatedAt'])
                likeCount.append(snippet['likeCount'])
                totalReplyCount.append(item['snippet']['totalReplyCount'])

            next_page_token = response.get('nextPageToken')

            while next_page_token is not None:  # getting the comments on the next pages
                if len(comments) > MAX:
                    break
                request = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=vID, maxResults=100,
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response['items']:
                    snippet = item['snippet']['topLevelComment']['snippet']

                    comments.append(snippet['textOriginal'])
                    commenter.append(snippet['authorDisplayName'])
                    publishedAt.append(snippet['updatedAt'])
                    likeCount.append(snippet['likeCount'])
                    totalReplyCount.append(item['snippet']['totalReplyCount'])

                next_page_token = response.get('nextPageToken')

            data = {
                "commenter": commenter,
                "comments": comments,
                "PublishTime": publishedAt,
                "totalReplyCount": totalReplyCount,
                "likeCount": likeCount
            }

            self.videos[vID].comments = pd.DataFrame(data)
        # print("Successfully fetched comments")

    # a function to get all the meta data about the video and store as a series
    def get_video_meta_data(self, youtube):

        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=list(self.IDs.keys())
        )

        response = request.execute()

        for item in tqdm(response["items"],"video_meta_data"):
            dic = {
                "videoId": item["id"],
                "videoTitle": item["snippet"]["title"],
                "videoDescription": item["snippet"]["description"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                #             "channelName": item["snippet"]["channelTitle"],
                #             "tags": item["snippet"]["tags"],
                "videoPublishTime": item["snippet"]["publishedAt"],
                "vidLen(sec)": item["contentDetails"]["duration"],
                "viewCount": item["statistics"]["viewCount"],
                "likeCount": item["statistics"]["likeCount"],
                "commentCount": item["statistics"]["commentCount"]
            }

            self.videos[item["id"]].metaData = pd.Series(dic)
        # print("Successfully retrieved video meta data")

    def get_channel_meta_data(self, youtube):
        # print(self.IDs.values())
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=list(self.IDs.values())
        )

        response = request.execute()
        # print(response)
        try:
            for item in tqdm(response["items"],"channel_meta_data"):
                dic = {
                    "channelId": item["id"],
                    "channelName": item["snippet"]["title"],
                    "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                    #                 "countryOfOrigin": item["snippet"]["country"],
                    "viewCount": item["statistics"]["viewCount"],
                    "videoCount": item["statistics"]["videoCount"],
                    "subscriberCount": item["statistics"]["subscriberCount"]
                }
                # print(dic["channelName"])

                for key in self.IDs.keys():
                    if self.IDs[key] == item["id"]:
                        self.videos[key].channelData = pd.Series(dic)

            # print("successfully fetched channel meta data")
        except Exception as e:
            print(f"unable to fetch channel meta data: {e}")


# ----------------------------------------------------------------------------------------------------------------------


# def main():
#     youtube = get_youtube_object()
#     search = Search(keyword=KEYWORD, youtube=youtube)
#     vid1, vid2, vid3, vid4, vid5 = search.videos.keys()
#     print("starting do it all function")
#     for vid in tqdm(search.videos, "do_it_all_functions"):
#         search.videos[vid].do_it_all()
#
#     with open('my_object.pkl', 'wb') as file: # creating a pickle object
#         pickle.dump(search, file)
#
#
#     # search.videos[vid1].do_it_all()
#     print("done processing do it all function")
#
#     print(search.videos[vid1].channelData)
#     print(search.videos[vid1].metaData)
#     print(search.videos[vid1].comments)
#     search.videos[vid1].create_commentsCloud(["Positive"])
#
# main()

