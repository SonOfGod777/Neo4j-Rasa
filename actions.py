# encoding=utf-8
from collections import defaultdict
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset
from py2neo import Graph
import redis
import os, json


class TireNode:
    def __init__(self):
        self.word_finish = False
        self.count = 0
        self.word = None
        self.entity_class = defaultdict(set)
        self.child = defaultdict(TireNode)


class Tire:
    def __init__(self):
        self.root = TireNode()

    def add(self, word, entity_class):
        curr_node = self.root
        for char in str(word).strip():
            curr_node = curr_node.child[char]
        curr_node.count += 1
        curr_node.word = word
        curr_node.entity_class[word].add(entity_class)
        curr_node.word_finish = True

    def search(self, words):
        entity_dic = {}
        for i in range(len(words)):
            word = words[i:]
            curr_node = self.root
            for char in word:
                curr_node = curr_node.child.get(char)
                if curr_node is not None and curr_node.word_finish == True:
                    entity_dic[curr_node.word] = curr_node.entity_class.get(curr_node.word)
                elif curr_node is None or len(curr_node.child) == 0:
                    break
        return entity_dic if entity_dic else ''


class MatchEntity:
    def __init__(self):
        self.tire = Tire()
        self.entity_dic = {}
        self.cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1]) + '/entity_dict/'
        for file_name in [file for file in os.listdir(self.cur_dir) if file != '.DS_Store']:
            entity_name = file_name.split('.')[0]
            self.entity_dic[entity_name] = self.read_data(self.cur_dir + file_name)

        for name, entity_lis in self.entity_dic.items():
            for entity in entity_lis:
                self.tire.add(entity, name)

    def read_data(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return [word.strip() for word in file.readlines() if word.strip()]

    def match(self, words):
        entity_dic = self.tire.search(words)
        slot_list = []
        if entity_dic:
            for entity, class_set in entity_dic.items():
                for class_ in class_set:
                    slot_list.append(SlotSet(class_, entity))
                    return slot_list, entity_dic
        else:
            return slot_list, entity_dic


class parser_question():
    def __init__(self):
        self.num_limit = 20
        self.g = Graph(
            host="127.0.0.1",
            http_port=7474,
            user="neo4j",
            password="1204107788a")
        self.text_json = self.read_json('data/attribute.json')
        self.relation_dic = self.text_json['relation']
        self.com_relation_dic = self.text_json['com_relation']
        self.attribute_lis = self.text_json['attribute']
    def read_json(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def parser(self, entity, intent):
        parser_lis = []
        res_lis = []
        intent = '_'.join(str(intent).split('_')[1:])
        if intent in self.attribute_lis:
            sql = "MATCH (m:Disease) where m.name = '{}' return m.name, m.{}".format(entity, intent)
            parser_lis.append(sql)
        if intent in self.relation_dic:
            end_node = self.relation_dic.get(intent, '')
            if end_node:
                sql = "MATCH (m:Disease)-[r:{}]->(n:{}) where m.name = '{}' return m.name, r.name, n.name".format(intent, end_node, entity)
                parser_lis.append(sql)
        if intent in self.com_relation_dic:
            relations = self.com_relation_dic.get(intent, '')
            if relations:
                sql1 = "MATCH (m:Disease)-[r:{}]->(n:{}) where m.name = '{}' return m.name, r.name, n.name".format(relations[0], intent, entity)
                sql2 = "MATCH (m:Disease)-[r:{}]->(n:{}) where m.name = '{}' return m.name, r.name, n.name".format(relations[1], intent, entity)
                parser_lis.append(sql1)
                parser_lis.append(sql2)
        for sql in parser_lis:
            res = self.g.run(sql).data()
            res_lis.extend(res)
        return res_lis


# parser = parser_question()
class ActionHelloWorld(Action):
    def name(self) -> Text:
        return "question_parser"

    def __init__(self):
        self.match = MatchEntity()
        # self.parser = parser_question()

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        res_lis = []
        input_word = dict(tracker.latest_message)['text']
        slot_list, entity_dic = self.match.match(input_word)
        intent = tracker.latest_message['intent']['name']
        if entity_dic:
            for entity in entity_dic:
                res = parser_question().parser(entity, intent)
                res_lis.extend(res)
            dispatcher.utter_message(json.dumps(res_lis[0]))
        if not entity_dic:
                entity_lis = [tracker.get_slot(name) for name in ['check', 'department', 'disease', 'drug', 'food', 'producer', 'symptom'] if tracker.get_slot(name) is not None]
                if entity_lis:
                    for entity in entity_lis:
                        res = parser_question().parser(entity, intent)
                        res_lis.extend(res)
                    dispatcher.utter_message(json.dumps(res_lis[0]))
                else:
                    return dispatcher.utter_message('我是机器人小八，有什么可以帮助你')  # 闲聊或反问
        return slot_list


class default_utter(Action):
    def name(self):  # type: () -> Text
        return 'defualt_action'

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        dispatcher.utter_message('我是机器人小八，有什么可以帮助你')





