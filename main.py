import calendar
import pprint
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import conversation
import databaseimporter as importer
from analyzer import find_sentiment_for_ids
from config import jsonDirectory, collection
from conversation import RootTweetFilterOptions
from conversation import find_average_conversation_length, import_conversation_trees_from_db
from sentiment_test import get_average_sentiment_for


def create_database():
    # function that imports the tweets

    importer.create_indexes()
    importer.process_all_json_files(jsonDirectory)
    importer.sanitize_db()


def create_conversation_database():
    # map the tweets to a conversation database
    conversation.create_indexes()
    conversation.export_all_trees_to_db()


def print_average_conversation_lengths(user_ids):
    # creates a dictionary with the following mapping: airline_id -> average_conversation_length

    avg_lengths = dict()
    for user_id in user_ids:
        user_trees = import_conversation_trees_from_db(user_id)
        avg_lengths[user_id] = find_average_conversation_length(user_trees)
    pprint.pprint(avg_lengths)
    return avg_lengths


def print_average_sentiment_scores(user_ids):
    # creates a dictionary with the following mapping: airline_id -> average_sentiment_score

    avg_scores = dict()
    for user_id in user_ids:
        user_trees = import_conversation_trees_from_db(user_id)
        avg_scores[user_id] = get_average_sentiment_for(user_trees)
    pprint.pprint(avg_scores)
    return avg_scores


def sort_conversation_trees_by_day(trees):
    # creates a dictionary with the following mapping: weekday_number -> list of trees

    day_dict = dict()
    return_day_dict = dict()

    for hour in range(0, 7):
        day_dict[calendar.day_name[hour]] = []

    for tree in trees:
        document = collection.find_one({"id": tree.root.id})
        text = document['text']
        timestamp = document['timestamp_ms']
        created_at = document['created_at']

        dat = datetime.fromtimestamp(int(timestamp) / 1000)
        day = calendar.day_name[dat.weekday()]
        day_dict[day].append(tree)

    for key, value in day_dict.items():
        # return_day_dict[key] = find_average_conversation_length(value)
        return_day_dict[key] = get_average_sentiment_for(value)

    return return_day_dict


def count_trees_by_day_per_year(trees):
    # creates a dictionary with the following mapping: day_number -> list of trees
    days_dict = dict()

    for hour in range(0, 365):
        days_dict[hour] = 0

    for i, tree in enumerate(trees):
        document = collection.find_one({"id": tree.root.id})
        timestamp = document['timestamp_ms']

        dat = datetime.fromtimestamp(int(timestamp) / 1000).timetuple().tm_yday

        days_dict[dat] = days_dict[dat] + len(tree.descendants) + 1
        if i % 10000 == 0:
            print("Processed: {} some value: {}".format(i, days_dict[dat]))

    return days_dict


def sort_conversation_trees_by_hour(trees):
    # creates a dictionary with the following mapping: hour_of_day -> list of trees
    hours_dict = dict()
    return_hours_dict = dict()

    for hour in range(0, 24):
        hours_dict[hour] = []

    for tree in trees:
        document = collection.find_one({"id": tree.root.id})
        text = document['text']
        timestamp = document['timestamp_ms']
        created_at = document['created_at']

        dat = datetime.fromtimestamp(int(timestamp) / 1000)
        time = (dat.hour - 2) % 24
        hours_dict[time].append(tree)

    for key, value in hours_dict.items():
        # return_hours_dict[key] = find_average_conversation_length(value)
        return_hours_dict[key] = get_average_sentiment_for(value)

    return return_hours_dict


user_ids = [56377143, 106062176, 18332190,
            22536055, 124476322, 26223583,
            2182373406, 38676903, 1542862735,
            253340062, 218730857, 45621423,
            20626359]


def violin_plot(use_root=False):
    topics = {"Food": ["food", "drink", "meal", "eat", "drink", "beverage", "alcohol"],

              "Luggage": ["luggage", "bag", "suitcase", "backpack", "lost", "gear", "carry-on", "trunk",
                          "conveyor belt",
                          "damage",
                          "missing",
                          "belonging", "possession"],

              "Delay": ["delay", "cancel", "wait", "postpone", "late", "slow", "abort", "suspen"],

              "Space": ["spac", "seat", "room", "leg", "chair"],

              "Service": ["service", "assistance", "help", "steward", "air host", "cabin crew", "hostess", "captain",
                          "pilot"]
              }
    topic_values = dict()

    for key, value in topics.items():
        print(key)
        data = find_sentiment_for_ids(user_ids[1:2], topics=value,  # [3:4] is american air sliced.
                                      root_tweet_filter_options=RootTweetFilterOptions.NO_AIRLINE)

        if use_root:
            topic_values[key] = pd.Series(data[0]['root_sent_list'])
        else:
            topic_values[key] = pd.Series(data[0]['sent_list'])

    df = pd.DataFrame(topic_values)

    ax = sns.violinplot(data=df)
    plt.xlabel("Topic")
    plt.ylabel("Sentiment")
    plt.title("Delta sentiments for topics inside conversations.")

    if use_root:
        plt.savefig("root_sentiment_graph.svg", bbox_inches='tight')
    else:
        plt.savefig("delta_sentiment_graph.svg", bbox_inches='tight')
    # plt.show()


def plot_data(datapoint):
    frq = datapoint['hist_freq']
    edges = datapoint['hist_edges']
    fig, ax = plt.subplots()
    ax.bar(edges[:-1], frq, width=np.diff(edges), ec="k", align="edge")
    ax.set_ylabel('Frequency')  # , fontsize=40)
    ax.set_xlabel('Sentiment')  # , fontsize=40)

    # plt.show()
    plt.savefig("food_distribution.svg", bbox_inches='tight')
    plt.savefig("food_distribution.pdf", bbox_inches='tight')


def sorted_over_year(user_id):
    trees = import_conversation_trees_from_db(user_id,
                                              root_tweet_filter_options=RootTweetFilterOptions.BOTH)
    sorted = count_trees_by_day_per_year(trees)
    pprint.pprint(sorted)


# create_database()  # run this only once!
# create_conversation_database()  # run this once too.



sorted_over_year(22536055)  # returns printed list of conversations throughout the year

# violin_plot(use_root=True) # returns the violin plot for the root sentiment
# violin_plot(use_root=False) # same but for deltas

pprint.pprint(find_sentiment_for_ids(user_ids[1:3], include_all_data_points=False)) # prints all gathered data
