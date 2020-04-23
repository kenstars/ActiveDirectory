# README

## Logs

### 23rd April 2020 10:40 pm

1. Modified code to fix bugs relating to Architecture.

2. Currently we receive a response to csv related queries like :
         What is the salary of Martha Kent
         Which department does Bruce Wayne work in
         How much does Clark Kent make.
3. We also reply to generic queries like :
         Hi
         Hope this is a good day

4. As next step will work on context related queries.

5. According to the time constraint , I think I will not be working on comparison queries by tomorrow. (will see if this changes by the next log.)


### 23rd April 2020 9:11 pm

1. Post cloning , install dependencies of flask , pandas, python-aiml
   ```
   pip install flask
   pip install pandas
   pip install python-aiml
   ```
2. Run the Flask server from the root server as such :
   ```
   python3 -m flask run
   ```
3. The server takes a post request as input :

Example : 
   ```
     Host : http://127.0.0.1:5000/text_input
     Form-data : {"message": "Hi"}
   ```
