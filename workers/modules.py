import json

def get_value_dict(column_values):
    """
    takes a pandasSeriesInput of column values
    """
    return [str(i).lower() for i in column_values.tolist()]

def send_to_ui(sending_message):
    print("Message is :", sending_message)
    return sending_message


def send_response(selected_df, active_filters, select_column, question_to_be_asked):
    if question_to_be_asked:
        response_msg = "which of the following " +active_filters[0]+ " are you looking for :  "+ ", ".join(active_filters[1])       
    else:
        print(select_column)
        json_df = json.loads(selected_df[select_column].to_json())
        json_df_values = [str(list(i.values())[0]) for i in json_df.values()]
        print(json_df_values)
        response_msg = " : ".join(json_df_values)
        print (response_msg)
    return send_to_ui(response_msg)

def get_generic_response(input_text, k):
    result_message = k.respond(input_text)
    return result_message