import pickle
from datetime import datetime
import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from tqdm import tqdm
import app
from app import Search
from app import Video


@st.cache_data
def create_table(_search):
    # creating the comparison table to be put on the website

    # Create an empty DataFrame with the desired column names
    columns = ['Video Title', 'Thumbnails', 'Channel Name', 'Published On', 'Like Count', 'Comment Count', 'View Count',
               'Total Subscribers',
               'Total Channel Views', 'Total Videos Uploaded', "Watch Video"]
    metaData_df = pd.DataFrame(columns=columns)

    # Create an empty list to store rows
    rows = []

    # Iterate through the videos and add data as rows
    for video in _search.videos.values():
        row = {
            "Channel Name": video.channelData["channelName"],
            "Thumbnails": video.metaData["thumbnail"],
            "Published On": video.metaData["videoPublishTime"],
            "Like Count": video.metaData["likeCount"],
            "Comment Count": video.metaData["commentCount"],
            "View Count": video.metaData["viewCount"],
            "Total Subscribers": video.channelData["subscriberCount"],
            "Total Channel Views": video.channelData["viewCount"],
            "Total Videos Uploaded": video.channelData["videoCount"],
            "Watch Video": f'https://www.youtube.com/watch?v={video.metaData["videoId"]}'
        }

        rows.append(row)

    # Concatenate the list of rows to create the DataFrame
    metaData_df = pd.concat([metaData_df, pd.DataFrame(rows)])

    # Now, metaData_df contains the video metadata as rows, and you've avoided the deprecated .append method.

    # Transpose the DataFrame
    # metaData_df = metaData_df.T

    titles = []
    for video in _search.videos.values():
        titles.append(video.metaData["videoTitle"])

    metaData_df["Video Title"] = titles
    # metaData_df = metaData_df.reset_index()
    return metaData_df


def return_pickle():
    with open('my_object.pkl', 'rb') as file:
        search = pickle.load(file)
        return search


def tab_home():
    custom_css = """
        <style>
            /* Change the font for the entire app */
            h2 {
                font-family: 'Comic Sans MS', cursive; /* Replace 'Arial' with your desired font */
            }
            h3 {
                font-family: 'Comic Sans MS', cursive; /* Replace 'Arial' with your desired font */
            }
            h4 {
                font-family: 'Comic Sans MS', cursive; /* Replace 'Arial' with your desired font */
            }
            h5 {
                font-family: 'Comic Sans MS', cursive; /* Replace 'Arial' with your desired font */
            }
        </style>
    """

    # Display the custom CSS to change the font
    st.markdown(custom_css, unsafe_allow_html=True)
    # st.title("Home Tab")
    # st.write("This is the Home tab content.")

    st.subheader("Metrics & Moods: A Keyword's Tale.")
    search_query = st.text_input('Enter search keyword:', 'Joe Rogan Podcast', max_chars=20,
                                 help="enter the keyword you want to search on youtube")

    # youtube = app.get_youtube_object()

    search = return_pickle()

    # search = app.Search(keyword=search_query, youtube=youtube)  # creating the search object

    # for vid in tqdm(search.videos, "do_it_all_functions"):
    #     search.videos[vid].do_it_all()

    vid_keys = list(search.videos.keys())

    # -----------------------html table------------------------------------
    # html_table = create_table(search).to_html(index=False)
    #
    # pattern = r'<td>(https?://\S+)</td>'
    #
    # # Replace matched URLs with img tags
    # html_table = re.sub(pattern, r'<td><img height="80" width="120" src="\1"></td>', html_table)
    #
    # st.write(html_table, unsafe_allow_html=True)
    # ---------------------------------------------------------------------------------------------
    # converting values into numeric

    df_table = create_table(search)
    df_table[["View Count", "Like Count", "Comment Count", "Total Subscribers", "Total Channel Views"]] = df_table[
        ["View Count",
         "Like Count", "Comment Count", "Total Subscribers", "Total "
                                                             "Channel"
                                                             " Views"]].apply(pd.to_numeric)

    st.dataframe(df_table, hide_index=True, column_config={
        "Published On": st.column_config.DatetimeColumn(
            "Published On",
            min_value=datetime(2000, 6, 1),
            max_value=datetime(2024, 1, 1),
            format="D MMM YYYY, h:mm a",
            step=60,
        ),
        "Thumbnails": st.column_config.ImageColumn(
            "Video Thumbnails", help="Thumbnails shown on videos on youtube", width="small"
        ),
        "Watch Video": st.column_config.LinkColumn(),
        "Total Videos Uploaded": st.column_config.ProgressColumn(
            "Total Videos Uploaded",
            help="Total videos uploaded by the channel till date",
            format="%f",
            min_value=df_table["Total Videos Uploaded"].min(),
            max_value=df_table["Total Videos Uploaded"].max(),
        )
    })
    # print(search_query)
    # data = pd.DataFrame({
    #     'Date Of Publish Of Video': ['Alice', 'Bob', 'Charlie'],
    #     'Number Of Likes On Video': [25, 30, 28],
    #     'Number Of Views On Video': ['USA', 'Canada', 'UK'],
    #     'Name Of Channel': [None, None, None],
    #     'Name Of Channelfasddddd1': [None, None, None]
    # })
    # st.dataframe(data, width=1600)

    with st.sidebar:
        orientation = st.radio("Select Orientation", ("h", "v"), captions=("Horizontal", "Vertical"))
        chart_selection = st.radio("Select a Chart",
                                   ("Like Count vs View Count", "Comment Count vs View Count",
                                    "Like Count vs Comment Count"))
        scatterplot = st.radio("Select a video for ScatterPlot",
                               ("Video 1", "Video 2", "Video 3", "Video 4", "Video 5"))
        word_cloud_sentiment = st.multiselect('select topic', ['Positive', 'Neutral', 'Negative'])

    col1, col2 = st.columns(2)
    # Like Count vs View Count
    # with col1:
    H = None
    W = None
    X1 = 'Channel Name'
    X2 = 'Channel Name'
    X3 = 'Channel Name'
    Y1 = "Views Per Comment"
    Y2 = "Views Per Like"
    Y3 = "Likes Per Comment"

    if orientation == 'h':
        Y1 = 'Channel Name'
        Y2 = 'Channel Name'
        Y3 = 'Channel Name'
        X1 = "Views Per Comment"
        X2 = "Views Per Like"
        X3 = "Likes Per Comment"

    with col1:
        if chart_selection == "Comment Count vs View Count":
            st.write('<br><h3>Comment Count vs View Count</h3>', unsafe_allow_html=True)
            df_table["Views Per Comment"] = df_table["View Count"] / df_table["Comment Count"]
            fig = px.bar(df_table, x=X1, y=Y1,
                         color='Comment Count', hover_data=["Video Title"],
                         height=H, width=W, orientation=orientation)
            st.plotly_chart(fig)

        # Comment Count vs View Count
        if chart_selection == "Like Count vs View Count":
            st.write("<br><h3>Like Count vs View Count</h3>", unsafe_allow_html=True)
            df_table["Views Per Like"] = df_table["View Count"] / df_table["Like Count"]
            fig = px.bar(df_table, x=X2, y=Y2,
                         color='Like Count', hover_data=["Video Title"],
                         height=H, width=W, orientation=orientation)
            st.plotly_chart(fig)

        if chart_selection == "Like Count vs Comment Count":
            st.write("<br><h3>Like Count vs Comment Count</h3>", unsafe_allow_html=True)
            df_table["Likes Per Comment"] = df_table["Like Count"] / df_table["Comment Count"]
            fig = px.bar(df_table, x=X3, y=Y3,
                         color='View Count', hover_data=["Video Title"],
                         height=H, width=W, orientation=orientation)
            st.plotly_chart(fig)

    with col2:
        st.write("<br><h3>Scatter Plot of Vader Polarity Scores for YouTube Comments</h3>", unsafe_allow_html=True)
        if scatterplot == "Video 1":
            fig = px.scatter(search.videos[vid_keys[0]].comments, x='commenter', y='compound',
                             color='neg', size='pos')

            fig.update_xaxes(title="Commenters on the Video", showticklabels=False)
            fig.update_yaxes(title="Vader Polarity Scores")
            st.plotly_chart(fig)
        if scatterplot == "Video 2":
            fig = px.scatter(search.videos[vid_keys[1]].comments, x='commenter', y='compound',
                             color='neg', size='pos')

            fig.update_xaxes(title="Commenters on the Video", showticklabels=False)
            fig.update_yaxes(title="Vader Polarity Scores")
            st.plotly_chart(fig)

        if scatterplot == "Video 3":
            fig = px.scatter(search.videos[vid_keys[2]].comments, x='commenter', y='compound',
                             color='neg', size='pos')

            fig.update_xaxes(title="Commenters on the Video", showticklabels=False)
            fig.update_yaxes(title="Vader Polarity Scores")
            st.plotly_chart(fig)

        if scatterplot == "Video 4":
            fig = px.scatter(search.videos[vid_keys[3]].comments, x='commenter', y='compound',
                             color='neg', size='pos')

            fig.update_xaxes(title="Commenters on the Video", showticklabels=False)
            fig.update_yaxes(title="Vader Polarity Scores")
            st.plotly_chart(fig)

        if scatterplot == "Video 5":
            fig = px.scatter(search.videos[vid_keys[4]].comments, x='commenter', y='compound',
                             color='neg', size='pos')

            fig.update_xaxes(title="Commenters on the Video", showticklabels=False)
            fig.update_yaxes(title="Vader Polarity Scores")
            st.plotly_chart(fig)

    st.write("<h2> Word Clouds Of the most commonly used phrases in the comments</h2>", unsafe_allow_html=True)
    st.write(
        f"<h3> Please Select the Sentiment type from the Sidebar.<br> CURRENT MOOD: {','.join(word_cloud_sentiment)}</h3>",
        unsafe_allow_html=True)

    for i in range(5):  # Displaying 5 word clouds and titles
        st.write(f'<h4>Video Title: {df_table["Video Title"][i]}</h4>', unsafe_allow_html=True)
        cols = st.columns(2)
        # Display word cloud in the first column
        with cols[0]:
            wordcloud = search.videos[vid_keys[i]].create_commentsCloud(word_cloud_sentiment)
            st.image(wordcloud.to_array(), width=750)

        # Display title parallel to the word cloud in the second column
        with cols[1]:
            st.write("<h5>Most Popular Comments in each Category: </h5>", unsafe_allow_html=True)
            most_liked_comments = search.videos[vid_keys[i]].comments.loc[
                search.videos[vid_keys[i]].comments.groupby(by='sentiment', observed=False)
                ["likeCount"].idxmax()]
            most_liked_comments = most_liked_comments.drop(
                columns=["neg", "neu", "pos", "compound", "PublishTime", "totalReplyCount", "likeCount", "tokens"])
            st.dataframe(most_liked_comments, use_container_width=True, hide_index=True)
    st.write("<h3>Overall Sentiment of People About the Videos: </h3>", unsafe_allow_html=True)
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.write(df_table["Video Title"][i])
            avg = search.videos[vid_keys[i]].comments.sentiment.value_counts().idxmax()
            if avg == "Positive":
                st.image("happy.png")
            if avg == "Neutral":
                st.image("neutral.png")
            if avg == "Negative":
                st.image("sad.png")


def about_us():
    st.title('About Us - YouTube Analyzer')
    st.markdown(
        """Welcome to **YouTube Analyzer**, a project developed by a team of four dedicated data science students. 
        Our mission is to provide users with an insightful analysis of YouTube videos based on their interests and 
        sentiments. YouTube Analyzer is an innovative Python-based application designed by a team of proficient data 
        science students. Leveraging a plethora of powerful libraries such as NLTK, Streamlit, Pandas, 
        Plotly Express, and Spacy, this project focuses on providing users with a comprehensive analysis of YouTube 
        videos based on specific search keywords.

At its core, the application enables users to input keywords of interest, initiating a search that retrieves the top 
five videos related to the provided query. The system conducts in-depth Exploratory Data Analysis (EDA) on these 
videos, extracting crucial insights about their content, engagement metrics, and audience reception. Through Pandas 
for data manipulation and Plotly Express for interactive visualizations, the application showcases statistical 
patterns, views, likes, comments, and other relevant metrics, aiding users in understanding the popularity and impact 
of the videos.
One of the standout features of the YouTube Analyzer is its sophisticated sentiment analysis module, powered by NLTK 
and Spacy. This module evaluates the sentiment conveyed within the video content, deciphering the emotions and 
attitudes expressed. By employing natural language processing techniques, it categorizes sentiments as positive, 
negative, or neutral, empowering users with a deeper understanding of the emotional tone of the videos.
Additionally, the application includes a recommendation system that utilizes the analyzed data to suggest the most 
suitable video for users based on their preferences and sentiments. The user-friendly interface, developed using 
Streamlit, ensures seamless interaction and accessibility for individuals seeking comprehensive insights into YouTube 
content.
In essence, the YouTube Analyzer amalgamates advanced data science methodologies with user-friendly functionalities, 
offering a powerful tool for individuals keen on exploring and understanding the landscape of YouTube videos through 
a data-driven lens.


        """
    )

    st.header('Meet the Team')
    st.markdown(
        """
        Meet the brilliant minds behind YouTube Analyzer:
        """
    )

    # Information about team members
    team_members = [
        {
            'name': 'Ashutosh Goyal',
            'description': 'Leading the project, bringing innovative ideas.',
            'image': 'https://via.placeholder.com/150',  # Replace with actual image link
        },
        {
            'name': 'Sangam Sharma',
            'description': 'Expertise in data analysis and visualization.',
            'image': 'https://via.placeholder.com/150',  # Replace with actual image link
        },
        {
            'name': 'Vyom Dalakoti',
            'description': 'Implementing advanced sentiment analysis algorithms.',
            'image': 'https://via.placeholder.com/150',  # Replace with actual image link
        },
        {
            'name': 'Kartik Anand',
            'description': 'Developing user-friendly features and interfaces.',
            'image': 'https://via.placeholder.com/150',  # Replace with actual image link
        }
    ]

    for member in team_members:
        st.subheader(member['name'])
        st.image(member['image'], caption=member['description'], width=150)
        st.write(member['description'])

    st.header('Our Contributions')
    st.markdown(
        """
        Our project offers the following key features:
        """
    )
    contributions = [
        'Keyword-based YouTube video search',
        'Exploratory Data Analysis on top five YouTube videos',
        'Sentiment analysis on video content',
        'Recommendation system for users',
    ]

    for i, contribution in enumerate(contributions, start=1):
        st.write(f"{i}. {contribution}")


def tab_contact():
    st.title("Contact Us")
    st.write("This is the Contact tab content.")


def main():
    st.set_page_config(page_title="Ytrend Analyser", layout='wide')
    image_url = "https://upload.wikimedia.org/wikipedia/commons/e/e1/Logo_of_YouTube_%282015-2017%29.svg"
    # image_url = "YT_logo.jpg"

    # Generate HTML and CSS to position the image in the top-right corner
    image_html = f"""
        <div style="position: absolute; top: 10px; right: 10px;">
            <a href=www.youtube.com><img src="{image_url}" alt="Image" width="300"><a>
        </div>
    """

    # Display the HTML content within Streamlit using st.markdown()
    st.markdown(image_html, unsafe_allow_html=True)

    st.title("Ytrend Analyser")

    # Create a sidebar with tab selection
    tabs = ["Home", "About"]
    selected_tab = st.sidebar.radio("Select Tab", tabs)

    # Display content based on selected tab
    if selected_tab == "Home":
        tab_home()
    elif selected_tab == "About":
        about_us()


if __name__ == "__main__":
    main()
