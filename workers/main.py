import os
import json
from flask import Flask, request
import aiml
import pandas as pd
from nltk.corpus import wordnet 
from nltk.stem import PorterStemmer

from collections import defaultdict
from workers.modules import get_value_dict, send_response, send_to_ui, get_generic_response
from nltk.util import ngrams

stemmer= PorterStemmer() 
stem = lambda x: stemmer.stem(x)

def get_syns(x):
   synonyms = []
   for syn in wordnet.synsets(x): 
      for l in syn.lemmas(): 
         synonyms.append(l.name().lower())
   return list(set(synonyms))

def all_ngram_merger(list_val):
   return sum([[" ".join(j) for j in list(ngrams(list_val, i)) ]for i in range(1,len(list_val)+1)], [])

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class ChatAnswer:
   def __init__(self):
      """
         Initialises the ChatAnswer Class and preprocesses the CSV file for working
      """
      print("Initialising nlp modules and prepping the csv file")
      self.input_df = pd.read_csv("data/MasterData.csv")
      self.columnNames = self.input_df.columns
      self.value_dict = defaultdict(list)
      self.synonym_dict = {}
      for eachColumnName in self.columnNames:
         print(self.input_df[eachColumnName].tolist()[0])
         self.value_dict[eachColumnName] = get_value_dict(self.input_df[eachColumnName])
         self.synonym_dict[eachColumnName] = get_syns(eachColumnName)
         if "name" in eachColumnName.lower():
            self.synonym_dict[eachColumnName].append("who")
         if is_number(str(self.input_df[eachColumnName].tolist()[0])):
            self.synonym_dict[eachColumnName].append("how much")

      print (self.synonym_dict)
      self.core_words = set( sum([ 
                                    str(i).lower().split() for i in sum(self.value_dict.values(), []) 
                                  ]
                                 ,[]) 
                                 + [c.lower() for c in self.columnNames ] 
                                 + sum(self.synonym_dict.values(), []))
      self.active_filters = []
      self.column_found = []
      self.clarification_question_ask = 0
      self.genericResponseKernel = aiml.Kernel()

      # folder_list = ["alice"]
      # print("Prep complete")
      # print("preparing generic response Kernel")
      # for each_folder in folder_list:
      #    path = "additional_resources/botdata/"+each_folder
      #    filenames = os.listdir(path)
      #    for eachFilename in filenames:
      #       self.genericResponseKernel.learn(path+"/"+eachFilename)
      
      print("kernel Ready")
      print("Sample Test Hi !")
      result_message = self.genericResponseKernel.respond("hi")
      print("Result : ", result_message)
      print("Finished Initialisation")

chatAnswerObj = ChatAnswer()

api = Flask(__name__)
@api.route('/text_input', methods=['POST'])
def chat_worker():
   """
      Processes the input chat that has come from the user
   """
   message = request.form.get("message")
   json_parsed_data = {"message":message}
   unigrams = json_parsed_data["message"].lower().split()
   stem_chat_grams = all_ngram_merger([stem(i) for i in unigrams])
   chat_grams = sorted(all_ngram_merger(unigrams), key = lambda x:len(x.split()), reverse=True)
   print (chat_grams)
   is_in_topic = chatAnswerObj.core_words.intersection(unigrams)
   if chatAnswerObj.clarification_question_ask:
      selected_df = chatAnswerObj.saved_df
      active_filters = chatAnswerObj.active_filters
      chatAnswerObj.clarification_question_ask = 0
      column_found = chatAnswerObj.column_found
   else:
      active_filters = []
      selected_df =chatAnswerObj.input_df
      column_found = []
   if is_in_topic:
      print("is_in_topic :", is_in_topic)
      values_matched_column = []
      for each_columnName in chatAnswerObj.columnNames:
         if each_columnName.lower() in chat_grams:
            column_found.append(each_columnName)
         else:
            for eachSyn in chatAnswerObj.synonym_dict[each_columnName]:
               if stem(eachSyn) in stem_chat_grams or eachSyn in chat_grams:
                  column_found.append(each_columnName)
                  break
      for each_columnName in chatAnswerObj.columnNames:
         if chatAnswerObj.input_df[each_columnName].dtypes.str.endswith("O"):
            for actual_gram in chat_grams:
               matched_set_df = chatAnswerObj.input_df[chatAnswerObj.input_df[each_columnName].str.contains(actual_gram, case=False, regex=True)][each_columnName]
               if matched_set_df.shape[0]>0:
                  break
            else:
               continue
            print ("#"*10)
            print (each_columnName)
            print (matched_set_df)
            print ("#"*10)
            if matched_set_df.shape[0]>1:
               chatAnswerObj.column_found = column_found
               chatAnswerObj.saved_df = selected_df
               chatAnswerObj.active_filters = active_filters
               response = "There seems to be multiple results showing, Do you want the information for "
               multichoice = list(json.loads(matched_set_df.to_json()).values())
               chatAnswerObj.clarification_question_ask = 1
               if len(multichoice) >2:
                  response += ", ".join(multichoice[:-1]) + " or "+multichoice[-1]
               else:
                  response += multichoice[0] + " or " + multichoice[-1]
               return json.dumps({"response_message":response})
            elif matched_set_df.shape[0]>0:
               values_matched_column.append(each_columnName)
      select_column = values_matched_column + column_found
      select_column = list(set(select_column))
      if values_matched_column:
         print("Values Matched ", values_matched_column)
         selected_df = chatAnswerObj.input_df
         for each_column in values_matched_column:
            temp_df = selected_df
            temp_df["message_result"] = temp_df[each_column].apply(lambda x: int(str(x).lower() in json_parsed_data["message"].lower()) or [0, 2][bool(set(str(x).lower().split()).intersection(unigrams))] )
            selected_values_df = temp_df[temp_df["message_result"] == 1]
            print("Shape check ", selected_values_df.shape)
            if selected_values_df.shape[0] > 0:
               print("Result Found setting filters")
               selected_df = selected_values_df
               print(selected_df)
               active_filters.append([each_column, selected_values_df[each_column].tolist()[0]])
         else:
            for each_column in values_matched_column:
               temp_df = selected_df
               temp_df["message_result"] = temp_df[each_column].apply(lambda x: int(str(x).lower() in json_parsed_data["message"].lower()) or [0, 2][bool(set(str(x).lower().split()).intersection(unigrams))] )
               partial_selected_values_df = temp_df[temp_df["message_result"] == 2]
               if partial_selected_values_df.shape[0]==1:
                  print("PARTIAL MATCH FOUND SINGLE")
                  selected_df = partial_selected_values_df
                  active_filters.append([each_column, selected_df[each_column]])
               elif partial_selected_values_df.shape[0]>1:
                  print("PARTIAL MATCH FOUND MULTIPLE")
                  chatAnswerObj.clarification_question_ask = 1
      if chatAnswerObj.clarification_question_ask:
         chatAnswerObj.saved_df = selected_df
         chatAnswerObj.active_filters = active_filters
      response = send_response(selected_df, active_filters, select_column, column_found, chatAnswerObj.clarification_question_ask)
   else:
      response = get_generic_response(json_parsed_data["message"], chatAnswerObj.genericResponseKernel)    
   return json.dumps({"response_message":response})


