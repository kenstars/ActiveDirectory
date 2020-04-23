import os
import json
from flask import Flask, request

import aiml
import pandas as pd

from collections import defaultdict
from workers.modules import get_value_dict, send_response, send_to_ui, get_generic_response

class ChatAnswer:
   def __init__(self):
      """
         Initialises the ChatAnswer Class and preprocesses the CSV file for working
      """
      print("Initialising nlp modules and prepping the csv file")
      self.input_df = pd.read_csv("data/MasterData.csv")
      self.columnNames = self.input_df.columns
      self.value_dict = defaultdict(list)
      for eachColumnName in self.columnNames:
         self.value_dict[eachColumnName] = get_value_dict(self.input_df[eachColumnName])
      self.core_words = set(sum(self.value_dict.values(), [])+ list(self.columnNames))
      self.active_filters = []
      self.clarification_question_ask = 0
      self.genericResponseKernel = aiml.Kernel()

      folder_list = ["alice"]
      print("Prep complete")
      print("preparing generic response Kernel")
      for each_folder in folder_list:
         path = "additional_resources/botdata/"+each_folder
         filenames = os.listdir(path)
         for eachFilename in filenames:
            print ("Learning from ", path+"/"+eachFilename)
            self.genericResponseKernel.learn(path+"/"+eachFilename)

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
   chat_grams = json_parsed_data["message"].split()
   is_in_topic = chatAnswerObj.core_words.intersection(chat_grams)
   if chatAnswerObj.clarification_question_ask:
      selected_df = chatAnswerObj.saved_df
      active_filters = chatAnswerObj.active_filters
      chatAnswerObj.clarification_question_ask = 0
   else:
      selected_df =chatAnswerObj.input_df
   if is_in_topic:
      column_found = []
      values_matched_column = []
      for each_columnName in chatAnswerObj.columnNames:
         if each_columnName in chat_grams:
            column_found.append(each_columnName)
         matched_sets = set(chatAnswerObj.value_dict[each_columnName]).intersection(chat_grams)
         if matched_sets:
            values_matched_column.append(each_columnName)
      select_column = values_matched_column + column_found
      if values_matched_column:
         for each_column in values_matched_column:
            selected_df["message_result"] = chatAnswerObj.input_df[each_column].apply(lambda x: int(x in json_parsed_data["message"]) or [0, 2][bool(set(x).intersection(chat_grams))] )
            selected_values_df = selected_df[selected_df["message_result"] == 1]
            if selected_values_df.shape[-1] > 0:
               selected_df = selected_values_df
               active_filters.append([each_column, selected_values_df[each_column]])
            else:
               partial_selected_values_df = chatAnswerObj.input_df[chatAnswerObj.input_df["message_result"] == 2]
               if partial_selected_values_df.shape[-1]==1:
                  selected_df = partial_selected_values_df
                  active_filters.append([each_column, selected_df[each_column]])
               else:
                  chatAnswerObj.clarification_question_ask = 1
      if chatAnswerObj.clarification_question_ask:
         chatAnswerObj.saved_df = selected_df
         chatAnswerObj.active_filters = active_filters   
      response = send_response(selected_df, active_filters, select_column, chatAnswerObj.clarification_question_ask)
   else:
      response = get_generic_response(json_parsed_data["message"], chatAnswerObj.genericResponseKernel)    
   return json.dumps({"response_message":response})


