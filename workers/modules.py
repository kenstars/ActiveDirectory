import json

def get_value_dict(column_values):
    """
    takes a pandasSeriesInput of column values
    """
    return [str(i).lower() for i in column_values.tolist()]

def send_to_ui(sending_message):
    print("Message is :", sending_message)
    return sending_message


def send_response(selected_df, active_filters, select_column, column_found, question_to_be_asked):
    print ("active_filters", active_filters)
    if question_to_be_asked:
        response_msg = "which of the following " +active_filters[0][0]+ " are you looking for :  "+ ", ".join(active_filters[1])       
    else:
        print (selected_df)
        json_df = json.loads(selected_df[select_column].to_json())
        json_df_values = [str(list(i.values())[0]) for i in json_df.values()]
        response_msg = " : ".join(json_df_values)
        print (response_msg)
        print ("Column Found", column_found)
        answer = []
        for eachColumn in column_found:
            if eachColumn in json_df:
                answer.append("The "+eachColumn+" is "+str(list(json_df[eachColumn].values())[0]))
        response_msg = " and ".join(answer)
    return send_to_ui(response_msg)

def get_generic_response(input_text, k):
    result_message = k.respond(input_text)
    return result_message