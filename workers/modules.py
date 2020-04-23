def get_value_dict(column_values):
    """
    takes a pandasSeriesInput of column values
    """
    return column_values.tolist()

def send_to_ui(sending_message):
    print("Message is :", sending_message)
    return sending_message


def send_response(selected_df, active_filters, select_column, question_to_be_asked):
    if question_to_be_asked:
       response_msg = "which of the following " +active_filters[0]+ " are you looking for :  "+ ", ".join(active_filters[1])       
    else:
       response_msg = "The requested answer is : \n" + selected_df.tolist()
    return send_to_ui(response_msg)

def get_generic_response(input_text, k):
    result_message = k.respond(input_text)
    return result_message