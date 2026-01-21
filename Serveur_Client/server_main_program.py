# ╔══════════════════════════════════════╗
# ║                Modules               ║
# ╚══════════════════════════════════════╝
import base64
import csv
import os
from pathlib import Path
import shutil
import subprocess
import traceback
from paho.mqtt import client as mqtt_client
import re, uuid, time, random, threading
from datetime import datetime
import psycopg2
import argparse
import re
from threading import Thread
import numpy as np # type: ignore
# ╔══════════════════════════════════════╗
# ║             Présentation             ║
# ╚══════════════════════════════════════╝







# ╔════════════════════════════════════════════════════════════════════════════╗
# ║────────────────────────────────────────────────────────────────────────────║
# ╚════════════════════════════════════════════════════════════════════════════╝

# ╔══════════════════════════════════════╗
# ║            Global Variable           ║
# ╚══════════════════════════════════════╝
# We'll import a Verbose parameter that we're gonna be able to activate via -v
verbose = True

# connexion_sql represent the connexion to the database, cursor_sql allow Python to execute sql querys
global connexion_sql

# IP Address & Port for the MQTT Broker
broker = os.getenv('MQTT_BROKER_HOST', '172.18.0.1')
port = 1883
# Unique ID given to the client, for the server client it has been put at 0
client_id = str(0)
global client

#We then create an array that contains multiple users
user_array = []

#List of user updated to the user currently here
last_hb_user=[]

global model_id, dataset_id, hubs, typeOfSelection, rulesList, numberOfParts, parameter, dataset_id_array, typeOfSelection_array, rulesList_array,numberOfParts_array

global work_id 
global list_dataset

global number_of_turn, number_of_turn_total
global mode_of_execution, is_initialized_model_given, input_dim

global default_path
default_path = Path("/") / "app" / "FL"
# ╔══════════════════════════════════════╗
# ║     0. Handling the log & Message    ║
# ╚══════════════════════════════════════╝
# Message transmitted over the MQTT Canal are over this form : 
# [Sender_ID] [Receiver_ID] [INSTRUCTIONS] [DETAILS]
# Example : 
# [0] [MAC ADDRESS] [Providing Name] [NAME:name]
# [client_id] [0] [Waiting For Connexion] []

# Function that return the correct way to construct a message in our mqtt process
def construct_message(receiver_id,instructions,details=""):
    return "["+client_id+"] ["+receiver_id+"] ["+instructions+"] ["+details+"]"

def insert_logs(message,user="Server"):
    if verbose:
        print("Logs received from name:"+user+ ":"+message)
    sql_execute(f"INSERT INTO logs(hub_name, logs, type, timestamp) VALUES ('{user}', '{message}', 'type', '{datetime.now()}')")
    logs_to_file(message,user)

# ╔══════════════════════════════════════╗
# ║    1. Handling the SQL Connection    ║
# ╚══════════════════════════════════════╝

# ────────────────[Connecting to the database]───────────────
# [------------------------------------------------------]
# 1. Connect to the database, and put the connexion index in the variable connexion_sql
# 2. Create a cursor, used to manipulate the database, in the variable cursor_sql
# 3. Launch the function launch_mqtt_server
# [------------------------------------------------------]

def connect_sql():
    try:
        global connexion_sql
        connexion_sql = psycopg2.connect(database="FL",user="program", host="postgresql",password="program")
        launch_mqtt_server()
    except Exception as e:
        print("[CRITICAL ERROR] An error has been caught in the function connect_sql ("+e.__class__.__name__+") : ")
        traceback.print_exc()
        return

# ────────────────[Executing a sql query]───────────────
# [------------------------------------------------------]
# 1. With the cursor_sql, execute the query and commit it into the database
# [------------------------------------------------------]
def sql_execute(query, parameter=()):
    try:
        with connexion_sql.cursor() as cursor_sql:
            cursor_sql.execute(query, parameter)
            connexion_sql.commit()
    except Exception as e:
        connexion_sql.rollback()

# ────────────────[Getting a sql result]───────────────
# [------------------------------------------------------]
# 1. Execute the query and get the result
# 2. Return the result if there is only 1 result, or raise an exception
# [------------------------------------------------------]
def sql_get_single(query):
    with connexion_sql.cursor() as cursor_sql:
        cursor_sql.execute(query)
        variable=cursor_sql.fetchall() or []
        if variable==[]:
            return "NOT FOUND"
        if len(variable)==1:
            return variable[0][0]
        elif len(variable)>1:
            raise Exception("Multiples possibilities for query : " + str(query))

# ╔══════════════════════════════════════╗
# ║    2. Handling the MQTT Connection   ║
# ╚══════════════════════════════════════╝

# ────────────────[Creating the mqtt client]───────────────
# [------------------------------------------------------]
# 1. Create the mqtt client, while redefining the :
# - on_connect
# - on_disconnect
# - on_message
# [------------------------------------------------------]
def connect_mqtt():
    client = mqtt_client.Client(client_id=client_id)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    return client

# ────────────────[Connect to the mqtt client]───────────────
# [------------------------------------------------------]
# 1. Initialize the mqtt connection  : 
# - Connect to the broker
# - Disconnect all the user 
# - Start the heartbeat threads
# - Put itself in an infinite loop, to listen
# - reconnect itself when there is a problem
# [------------------------------------------------------]
def launch_mqtt_server():
    global client, is_initialized_model_given, input_dim, number_of_turn, mode_of_execution
    client = connect_mqtt()
    is_initialized_model_given=False
    input_dim=200
    number_of_turn=-1
    mode_of_execution="None"
    if os.path.exists(default_path / "logs" / "Server" / "Server.txt"):
        os.remove(default_path / "logs" / "Server" / "Server.txt")
    while True:
        try:
            if not client.is_connected():
                client.connect(broker, port)
                sql_execute("UPDATE hubs SET status='OFFLINE';")
                connexion_sql.commit()
                sending_heartbeat()
                check_heartbeat()
                insert_logs("Connection succeeded")
                client.loop_forever()
        except KeyboardInterrupt as k:
            return
        except Exception as e:
            print("[CRITICAL ERROR] An exception has been caught during the function launch_mqtt_server ("+e.__class__.__name__+") : ")
            traceback.print_exc()
            return

#______________________________________________#
# - on_connect allows us to change the behavior of our client whenever he is connecting to the broker
# - on_disconnect allows us to change the behavior of our client whenever he get disconnected from the broker
#______________________________________________#

# Reconfiguration of on_connect, to get some information about how did it went
def on_connect(client, userdata, flags, rc):
    """Callback exécuté lors de la connexion au broker MQTT"""
    if rc == 0:
        client.subscribe("#")
        print(f"[INFO] Connected to MQTT Broker with client ID {client_id}!")
    else:
        print(f"[ERROR] Failed to connect, return code {rc}")

# Reconfiguration of on_disconnect, to get the information when it happen.
def on_disconnect(client, userdata, rc):
    """Callback exécuté lors de la déconnexion du broker MQTT"""
    print(f"[WARNING] Disconnected from broker, return code {rc}. Will try to reconnect.")
    launch_mqtt_server()

# ╔══════════════════════════════════════╗
# ║     3. Handling connexion of hubs    ║
# ╚══════════════════════════════════════╝

# ────────────────[Handle the user connection]───────────────
# [------------------------------------------------------]
# 1. Try to see if the user is registered in the database
# 2. If he is, we send him his name and add him to the user list
# 3. Else, if the mac address isn't recognized, he return a warning
# 4. We do it in a thread, to be able to wait 1 sec per client, and thus let him the time to initialise the mqtt connection
# [------------------------------------------------------]
def handler_connect_user(payload_data,topic):
    t=Thread(target=handler_connect_user_thread,args=(payload_data,topic,)).start()


def handler_connect_user_thread(payload_data,topic):
    time.sleep(1)
    #We then check for his presence in the database to see if he is registered
    name=sql_get_single("SELECT name FROM hubs WHERE hubs.mac_address='"+payload_data[0]+"';")
        # If he is registered, we send his name, else we send him that he isn't registered.
    if name!="NOT FOUND":
        message= construct_message(payload_data[0],"NAME:"+name)
        add_user(name)
        result=client.publish(topic,message)
        if result[0]==0:
            insert_logs(f"[INFO] {payload_data[0]} has been recognized : {name} successfully connected")
        if "CAPACITY" in payload_data[3]:
            sql_execute("UPDATE hubs SET stockage='"+payload_data[3].split(":")[1].split(".")[0]+"' WHERE name='"+name[0][0]+"';")
    else:
        message=construct_message(payload_data[0],"NOT REGISTERED IN THE DATABASE")
        result=client.publish(topic,message)
        insert_logs(f"[WARNING] {payload_data[0]} not recognized : make sure to insert it into the database.")


# ╔══════════════════════════════════════╗
# ║         4. Handling the users        ║
# ╚══════════════════════════════════════╝

#We create a user class that contains the name and the status
class User:
    def __init__(self,name):
        self.name=name
        self.status="ONLINE"

# ────────────────[Check if the user is connected]───────────────
def is_user_connected(name):
    for user in user_array:
        if user.name==name:
            return True
    return False

# ────────────────[Check if the user status]───────────────
def get_user_status(name):
    for user in user_array:
        if user.name==name:
            return user.status

# ────────────────[Update the status of someone]───────────────
def update_user_status(name,status):
    for user in user_array:
        if user.name==name:
            user.status=status
            sql_execute("UPDATE hubs SET status='"+status+"' WHERE name='"+name+"';")
            break

# ────────────────[Disconnect a user]───────────────
def user_disconnected(name):
    i=0
    for user in user_array:    
        if user.name==name:
            user_array.remove(user)
            sql_execute("UPDATE hubs SET status='OFFLINE' WHERE name='"+name+"';")
            del last_hb_user[i]
            break
        else:
            i+=1

# ────────────────[Add an user]───────────────
# [------------------------------------------------------]
# 1. We create an user, and try to see if name is already connected
# 2.If he is already connected, we just update him
# 3. Else, we add him in the user list and update it
# [------------------------------------------------------]
def add_user(name):
    user = User(name)
    k=True
    for i in range(0,len(user_array)):
        if user_array[i].name==name:
            last_hb_user[i]=1
            update_user_status(name,"ONLINE")
            k=False
    if k:
        user_array.append(user)
        last_hb_user.append(1)
        sql_execute("UPDATE hubs SET status='ONLINE' WHERE name='"+name+"';")

# ╔══════════════════════════════════════╗
# ║             5. Heartbeats            ║
# ╚══════════════════════════════════════╝

# ────────────────[Start the sending HB thread]───────────────
def sending_heartbeat():
    t=Thread(target=sending_heartbeat_thread)
    t.start()

# ────────────────[Sending HB thread]───────────────
def sending_heartbeat_thread():
    while True:
        time.sleep(15)
        for user in user_array:
            heartbeat_request(user.name)

# ────────────────[Send the heartbeat message]───────────────
def heartbeat_request(user):
    message=construct_message(user,"HEARTBEAT")
    topic = "hubs/"+user+"/logs"
    client.publish(topic,message)

# ────────────────[Update Heartbeat array]───────────────
def update_heartbeat(name):
    i=0
    for user in user_array:
        if user.name==name:
            last_hb_user[i]=1
        else:
            i+=1

# ────────────────[Start the receiving HB thread]───────────────
def check_heartbeat():
    t=Thread(target=check_heartbeat_thread)
    t.start()

# ────────────────[Receiving HB thread]───────────────
# [------------------------------------------------------]
# 1. At the start, we empty the late_connexion array (user who are late to connect) and last_hb_user, the array of the heartbeat signal
# 2. After 15 seconds, we check the heartbeat signal and, for each 0, we add the user in the late_connexion array
# 3. If atleast one user is late, we recheck if he is connecting 3 times, every 2 seconds
# 4. If the late_connexion has still user after that, we consider the client dead and remove it from the user list
# [------------------------------------------------------]
def check_heartbeat_thread():
    global last_hb_user
    while True:
        late_connexion=[]
        for i in range(len(last_hb_user)):
            last_hb_user[i]=0
        time.sleep(15)
        for i in range(len(last_hb_user)):
            if last_hb_user[i]==0:
                late_connexion.append(user_array[i].name)
        if late_connexion!=[]:
            for _ in range(3):
                time.sleep(2)
                for k in range(len(last_hb_user)):
                    if user_array[k].name in late_connexion and last_hb_user[k]==1:
                        for i in range(len(late_connexion)):
                            if late_connexion[i]==user_array[k].name:
                                del late_connexion[i]
                                break
            if late_connexion!=[]:
                for username in late_connexion:
                    for user in user_array:
                        if user.name==username:
                            insert_logs(f"[WARNING] Death of client {user.name}")
                            user_disconnected(user.name)

# ╔══════════════════════════════════════╗
# ║         6. Handling messages         ║
# ╚══════════════════════════════════════╝

# ────────────────[Check the topic]───────────────
# [------------------------------------------------------]
# 1. Check if the topic correspond to the goodTopic
# 2. The "*" can be used to be a wildcard (design everything)
# [------------------------------------------------------]   
def check_if_right_topic(topic, goodTopic):
    topic_split=topic.split("/")
    goodTopic_split=goodTopic.split("/")
    if len(topic_split)==len(goodTopic_split):
        for i in range(len(topic_split)):
            if topic_split[i]==goodTopic_split[i] or goodTopic_split[i]=="*":
                if i==len(topic_split)-1:
                    return True
                else:
                    continue
            else:
                break
    return False

# ────────────────[Redefining on_message]───────────────
# [------------------------------------------------------]
# 1. Redefining on_message to handle the protocol of communication
# 2. Handle the differents topics via message made with construct_message
# [------------------------------------------------------]           
def on_message(client,userdata,message):
    # >>> Extracting the data and the topic
    payload_data,topic = re.findall(r"\[(.*?)\]",str(message.payload.decode("utf-8"))), str(message.topic)
    # >>> Checking if the message is for us
    print(str(len(payload_data)) + " avec "+ payload_data[1] + " qui doit correspondre à 0")
    if len(payload_data)>0 and payload_data[1]==client_id:
        # >>> Connexion part
        if check_if_right_topic(topic,"connexion/*") and payload_data[2]=="Asking for connexion":
            handler_connect_user(payload_data,topic)
        # >>> Intern message
        elif check_if_right_topic(topic,"Data/Server"):
            if payload_data[0]=="1" and payload_data[2]=="START":
                # >>> Start message : getting all the instructions
                received_start_message_server(payload_data)
            elif payload_data[0]=="0":
                # >>> Going to another step
                received_instruction_message_from_server(payload_data)
        elif is_user_connected(payload_data[0]) or payload_data[0]=="1":
                # >>> Got an update on a command
                if check_if_right_topic(topic,"*/*/commands"):
                    on_message_commands(payload_data)
                # >>> Got a metric
                elif check_if_right_topic(topic,"*/*/metrics"):
                    on_message_metrics(payload_data)
                # >>> Got a log
                elif check_if_right_topic(topic,"*/*/logs"):
                    # >>> Heartbeat log
                    if payload_data[2]=="HEARTBEAT":
                        update_heartbeat(payload_data[0])
                    # >>> Normal log
                    else:
                        on_message_logs(str(message.payload.decode("utf-8")))
        elif payload_data[2]=="Sending Data" and check_if_right_topic(topic,"Data"):
            # We want to save the data that is sent on that link
            save_data_locally(payload_data)
    else:
        print("Message not recognized :"+str(message.payload.decode("utf-8")))

def extract_field(s, name):
    try:
        return s.split(f"{name}:")[1].split("|")[0]
    except:
        return None


def save_data_locally(payload_data):
    sensor = extract_field(payload_data[3], "sensor")
    value = extract_field(payload_data[3], "value")

    place = extract_field(payload_data[3], "place")
    person = extract_field(payload_data[3], "person")
    path = extract_field(payload_data[3], "path")

    ts = datetime.now()
    date = ts.strftime("%Y-%m-%d")
    ts_str = ts.strftime("%d/%m/%Y %H:%M:%S")

    if path:
        csv_path = default_path / "Data" / path
    else:
        csv_path = default_path / "Data" / date / payload_data[0] / sensor / "data.csv"

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    new_file = not csv_path.exists()

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["host", "sensor", "value", "timestamp", "place", "person"])
        w.writerow([payload_data[0], sensor, value, ts_str, place, person])

# ────────────────[Received a log message]───────────────
def on_message_logs(message):
    log_recu=message.split(f"[{client_id}]")[1]
    nom=re.findall(r"\[(.*?)\]",message)[0]
    insert_logs(log_recu,nom)

# ────────────────[Received a metric message]───────────────
def on_message_metrics(payload_data):
    print("pas fait encore ! ")

# ────────────────[Received a command message]───────────────
# [------------------------------------------------------]
# 1. We received a message from a hub about a task we gave him
# 2. For each task, we check the message and update the user accordingly
# [------------------------------------------------------]   
def on_message_commands(payload_data):
    # >>> The user has finished downloading the dataset
    if payload_data[2]=="DATASET DOWNLOADED":
        for user in user_array:
            if user.name==payload_data[0]:
                update_user_status(user.name,"MODELS")
                break
    # >>> The user has finished downloading the model
    elif payload_data[2]=="MODEL DOWNLOADED":
        for user in user_array:
            if user.name==payload_data[0]:
                if mode_of_execution=="FL":
                    update_user_status(user.name,"WEIGHT")
                else:
                    update_user_status(user.name,"READY")
                break
    # >>> The user has finished downloading the weight
    elif payload_data[2]=="WEIGHT DOWNLOADED":
        for user in user_array:
            if user.name==payload_data[0]:
                update_user_status(user.name,"READY")
                break
    # >>> The user has finished his work 
    elif payload_data[2]=="WAITING FOR WORK":
        if mode_of_execution=="FL":
            decrypt_message(payload_data)
        for user in user_array:
            if user.name==payload_data[0]:
                update_user_status(user.name,"FINISHED")
                break

# ────────────────[Received an update message from server]───────────────
def received_instruction_message_from_server(payload_data):
    # >>> We need to adapt the datasets 
    if payload_data[2]=="ADAPT DATASETS":
        adapt_dataset()
    # >>> We can download the models
    elif payload_data[2]=="MODEL READY":
        download_models()
    # >>> We can download the weights
    elif payload_data[2]=="DOWNLOAD THE WEIGHT":
        download_weight()
    # We can start the execution
    elif payload_data[2]=="START THE EXECUTION":
        launch_execution()
    # We can relaunch a turn or start a turn
    elif payload_data[2]=="RELAUNCH THE EXECUTION" or payload_data[2]=="DOWNLOAD DATASET":
        if mode_of_execution=="MA":
            download_models()
        else:
            download_datasets()
    elif payload_data[2]=="END OF THE TURN":
        end_turn_n()
        
# ╔══════════════════════════════════════╗
# ║    7. Handling the start message     ║
# ╚══════════════════════════════════════╝

# ────────────────[Received the start message]───────────────
# [------------------------------------------------------]
# 1. We received a start message from the server containing all the data required
# 2. We are gonna extract : 
# - number_of_turn_total
# - model_id
# - hubs, the list of hubs used
# - dataset_id_array, containing the id of the dataset for each turn
# - typeOfSelection_array, containing the way to treat the dataset for each turn
# - numberOfParts_array, containing the number of parts to cut the dataset for each turn
# - rulesList_array, containing the rules for each turn if the cut mode is class
# - parameter
# - mode_of_execution, which define the mode we are currently in
# [------------------------------------------------------]   
def received_start_message_server(payload_data):
    global number_of_turn, number_of_turn_total, model_id, dataset_id_array, hubs, typeOfSelection_array, rulesList_array, parameter, numberOfParts_array, mode_of_execution
    try:
        # >>> Number of turn & Number of turn total
        number_of_turn=0
        number_of_turn_total=int(payload_data[3].split("numberOfTurn:")[1].split("|")[0])
        conditionDataset=True
        # >>> is federated Learning ?
        mode_of_execution = payload_data[3].split("Mode:")[1].split("|")[0]
        # >>> model_id & dataset_id_array
        model_id = payload_data[3].split("model:",1)[1].split("|")[0]
        dataset_id_array = payload_data[3].split("dataset:", 1)[1].split("|")[0].split(",")
        # >>> parameter
        parameter=payload_data[3].split("parameter:", 1)[1].split("|")[0] 
        # >>> typeOfSelection_array & number_of_parts_array
        typeOfSelection_array=[]
        numberOfParts_array=[]
        for i in range(number_of_turn_total):
            if payload_data[3].split("selectionByClass:",1)[1].split("|")[0].split(",")[i]=="True":
                typeOfSelection_array.append(True)
                numberOfParts_array.append(0)
            else:
                typeOfSelection_array.append(False)
                numberOfParts_array.append(int(payload_data[3].split("numberOfParts:",1)[1].split("|")[0].split(",")[i]))
        # >>> hubs
        temporary_hub = re.findall(r"\{(.*?)\}",payload_data[3])[0].split('|')
        hubs = [h.split(",") for h in temporary_hub]
        # >>> rulesList
        rulesList_array = [[] for _ in range(number_of_turn_total)]
        temporary_rules_array = re.findall(r"\{(.*?)\}",payload_data[3])[1].split('$')
        # >>> if temporary_rules_array is empty then we redefine it
        if temporary_rules_array!=['']:
            for i in range(number_of_turn_total):
                    if typeOfSelection_array[i] and temporary_rules_array[i]!=[]:
                        temporary_rules=temporary_rules_array[i].split("|")
                        rulesList_array[i]=([r.split(",") for r in temporary_rules])
    except Exception as e:
        number_of_turn=-1
        insert_logs("An error has happened during the start program. Exception : "+e)
        conditionDataset=False 
    if conditionDataset:
        for hub in hubs:
            if mode_of_execution!="MA":
                update_user_status(hub[0],"DATASETS")
            else:
                update_user_status(hub[0],"MODELS")
        create_work_into_database()
        insert_logs("[START] Start message received")
        start_turn_n()

def create_work_into_database():
    global work_id
    sql_execute("INSERT INTO jobs (hubs, datasets, model_id, status) VALUES (%s, %s, %s, %s);", ([hub[0] for hub in hubs], dataset_id_array, model_id, "WORKING") )
    work_id=sql_get_single("SELECT * FROM jobs ORDER BY start_time DESC LIMIT 1;")
    if work_id=="NOT FOUND" or work_id==None:
        raise Exception ("Problem with the work_id")
# ────────────────[Start a new turn]───────────────
# [------------------------------------------------------]
# 1. We're gonna define, for each turn : 
# - dataset_id, the dataset for this turn
# - typeOfSelection, if we are doing a class, or a classic mode
# - rulesList, the list of rules for this turn
# - numberOfParts, the number of parts to cut the dataset into for this turn
# [------------------------------------------------------]   
def start_turn_n():
    global dataset_id, typeOfSelection, rulesList, numberOfParts, number_of_turn
    os.makedirs(default_path / "Result", exist_ok=True)
    for file in (default_path / "Result").iterdir():
        os.remove(file)
    os.makedirs(default_path / "logs" / str(work_id) / str(number_of_turn) / "result",exist_ok=True)
    os.makedirs(default_path / "logs" / str(work_id) / str(number_of_turn) / "logs",exist_ok=True)
    if len(dataset_id_array)>number_of_turn:
        dataset_id=dataset_id_array[number_of_turn]
    if len(typeOfSelection_array)>number_of_turn:
        typeOfSelection=typeOfSelection_array[number_of_turn]
    if len(rulesList_array)>number_of_turn:
        rulesList=rulesList_array[number_of_turn]
    if len(numberOfParts_array)>number_of_turn:
        numberOfParts=numberOfParts_array[number_of_turn]
    insert_logs("======== Tour "+str(number_of_turn+1)+" ========")
    if number_of_turn==0 and mode_of_execution=="FL":
        federated_learning_preparation()
    elif mode_of_execution!="MA":
        adapt_dataset()
    else:
        download_models()

def end_turn_n():
    global list_dataset, hubs, number_of_turn, mode_of_execution
    number_of_turn+=1
    if number_of_turn==number_of_turn_total:
    # >>> We finished the last turn
        number_of_turn=-1
        insert_logs("Cycle finished. End of the start program.")
        for hub in hubs:
            update_user_status(hub[0],"ONLINE")
            client.publish(f"hubs/{hub[0]}/commands",construct_message(hub[0],"END OF THE START PROGRAM"))
        mode_of_execution="None"
    else:

        # >>> We haven't done the last turn yet
        if mode_of_execution!="MA":
            for dataset in list_dataset:
                dataset[1]="None"
            for hub in hubs:
                    update_user_status(hub[0],"DATASETS")
            else:
                for hub in hubs:
                    update_user_status(hub[0],"MODELS") 
        start_turn_n()


# ────────────────[Start the initialisation thread]───────────────
def federated_learning_preparation():
    t=Thread(target=federated_learning_preparation_thread).start()

# ────────────────[Initialisation Thread]───────────────
# [------------------------------------------------------]
# 1. We're gonna :
# - If a initial model is given, we use it
# - else, if the program is given on the side, use it
# - else, use the model with the correct parameter required
# [------------------------------------------------------]   
def federated_learning_preparation_thread():
    if is_initialized_model_given:
        print("ici on doit faire")
    else:
        insert_logs("Initializing the weight : ")
        model_path=  sql_get_single("SELECT path FROM models WHERE model_id="+model_id+";")
        weight_path= str(default_path / "Weights" / "server_weight.pth")
        try:
            p=subprocess.Popen(["python3", model_path,
                           "--mode","init",
                           "--input-dim",str(input_dim),
                           "--output-path",weight_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True
                            )
            for line in p.stdout:
                insert_logs(line.rstrip(),"Initialisation")
            insert_logs("Finished treating the weight.")
            shutil.copyfile(weight_path,default_path / "logs" / str(work_id) / str(number_of_turn) / "result" / "weight_server.pth")
            client.publish("Data/Server",construct_message("0","ADAPT DATASETS"))
        except Exception as e:
            insert_logs("Erreur dans l'initialisation. Fin du programme. Vérifiez le -in. Stacktrace : "+str(e))

# ╔══════════════════════════════════════╗
# ║         8. Dataset preparation       ║
# ╚══════════════════════════════════════╝

# ────────────────[Start the adapting dataset thread]───────────────
def adapt_dataset():
    t=Thread(target=adapt_dataset_thread).start()

# ────────────────[Adapting dataset thread]───────────────
# [------------------------------------------------------]
# 1. We first prepare the variable (list_dataset, dataset_path, dataset_dir ...)
# 2. We then clean the old folder, and open the csv obtained, get the header (name of column) and the rows (all the lines)
# 3. Then, we check the mode (classic or class), and we cut the dataset corresponding to that
# [------------------------------------------------------] 
def adapt_dataset_thread():
    insert_logs("[INFO] Preparing the datasets.")
    # >>> Preparing the variable
    global list_dataset
    list_dataset=[]
    # >>> Path variable
    dataset_dir = default_path / "Datasets" / str(dataset_id)
    dataset_string_path= sql_get_single("SELECT path FROM datasets WHERE dataset_id="+dataset_id+";")
    dataset_path=Path(dataset_string_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {dataset_path}")
    # >>> Deleting all the old files
    for file in dataset_dir.iterdir():
        if file.is_file() and file.name != dataset_string_path.split("/")[-1]:
            os.remove(file)
    # >>> Opening the file an getting the headers and rows of the file
    with open(dataset_path, newline='', encoding="utf-8") as f:
        csv_reader = list(csv.reader(f))
        header, rows = csv_reader[0], csv_reader[1:]
    # >>> Classic mode : n files of equal size
    if not typeOfSelection:
        # >>> Variable number_lines_per_file & number_lines_total
        number_lines_total = len(rows)
        number_lines_per_file = number_lines_total / numberOfParts
        # >>> For each file : 
        # >>> - We compute the start & end
        # >>> - Get the corresponding lines
        # >>> - Put them in a file Dataset{i}.csv
        # >>> - Insert it into list_dataset to know who's gonna treat it
        for i in range(numberOfParts):
            start=int(i * number_lines_per_file) 
            end = int((i+1)* number_lines_per_file)
            temp_file_line = rows[start:end]
            if not temp_file_line:
                break
            temp_filename = f"Dataset{i+1}.csv"
            temp_path = dataset_dir / temp_filename
            # >>> Writing part
            with open(temp_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(temp_file_line)
            list_dataset.append([str(temp_path),str("None")])
    else:
        i=1
        # >>> For each hub : 
        # >>> - We check, for each rule, if it is for this hub
        # >>> - If it is, we add the line corresponding to the parameter to the hub list of lines
        # >>> - After all the rules have been checked, we add the lines to the file
        for hub in hubs:
            hub_rows = []
            for rule in rulesList:
                hub_name, headerRule, value, freq = rule
                if hub_name != hub[0]:
                    continue
                # >>> Here, the rules is for the hub, so we choose the lines
                matching = [r for r in rows if r[header.index(headerRule)].strip().lower() == value.strip().lower()]
                if float(freq) < 1.0 and len(matching) > 0:
                    nb_to_keep = int(len(matching) * float(freq))
                    matching = random.sample(matching, nb_to_keep)
                hub_rows.extend(matching)
            hub_rows = [list(x) for x in {tuple(r) for r in hub_rows}]
            output_file = dataset_dir / ("Dataset"+str(i)+".csv") 
            i+=1
            with open(output_file, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(hub_rows)
            list_dataset.append([str(output_file),hub[0]])
    client.publish("Data/Server",construct_message("0","DOWNLOAD DATASET"))

# ╔══════════════════════════════════════╗
# ║          9. Sending datasets         ║
# ╚══════════════════════════════════════╝

# ────────────────[Send the download message & launch the dataset reception Thread]───────────────
# [------------------------------------------------------]
# 1. If the last dataset has been treated : 
# - we launch the aggregation if we are in federated learning
# - We then check if we are at the last turn. If yes, we disconnect everyone, else we relaunch a turn
# 2. If the last dataset hasn't been treated : 
# - For each hub in hubs, we check if a dataset is available (classic mode) or linked to him (class mode)
# - If we can send him a dataset, we send him one, else we tell him to wait for the next turn
# [------------------------------------------------------] 
def download_datasets():
    # >>> Variables used
    global list_dataset, number_of_turn, number_of_turn_total
    dataset_extension=  sql_get_single("SELECT path FROM datasets WHERE dataset_id="+dataset_id+";").split(".")[1]
    # >>> Case 1 : All the dataset has been treated
    all_dataset_treated=True
    for i in range(len(list_dataset)):
        if list_dataset[i][1]!="Done":
                all_dataset_treated=False
                break
    if all_dataset_treated:
        insert_logs("A turn has been finished. Gonna see if another turn is planned")
        if mode_of_execution=="FL":
            launch_aggregation_federated_learning()
        else:
            client.publish("Data/Server",construct_message("0","END OF THE TURN"))
    # >>> Case 2 : Some dataset hasn't been treated
    elif number_of_turn<number_of_turn_total:
        # >>> Classic Mode
        if not typeOfSelection:

            for hub in hubs:
                for i in range(0,len(list_dataset)+1):
                    # >>> No dataset available, putting the client on hold
                    if i==len(list_dataset):
                        insert_logs(f"{hub[0]} waiting for the next turn.")
                        update_user_status(hub[0],"WAITING")
                    # >>> At least one dataset available, we give it to the first client
                    elif list_dataset[i][1]=="None":
                        list_dataset[i][1]=hub[0]
                        client.publish("hubs/"+hub[0]+"/commands",construct_message(hub[0],"DOWNLOAD DATASETS","id:"+dataset_id+"| part_number:"+list_dataset[i][0].split("/")[-1].split(".csv")[0].split("Dataset")[1]+"|name:Dataset."+dataset_extension))
                        break
        # >>> Class mode
        else:
            for hub in hubs:
                for i in range (0,len(list_dataset)+1):
                    # >>> The client already treated his dataset for his turn (Normally we never come here, it is mostly a security)
                    if i==len(list_dataset):
                        update_user_status(hub[0],"WAITING")
                    # >>> The client didn't treated his dataset yet
                    elif list_dataset[i][1]==hub[0]:
                        client.publish("hubs/"+hub[0]+"/commands",construct_message(hub[0],"DOWNLOAD DATASETS","id:"+dataset_id+"| part_number:"+list_dataset[i][0].split("/")[-1].split(".csv")[0].split("Dataset")[1]+"|name:Dataset."+dataset_extension))
                        break 
        # >>> We then start the dataset reception thread to check the download state
        t=Thread(target=(download_dataset_check_thread)).start()

# ────────────────[Dataset reception Thread]───────────────
# [------------------------------------------------------]
# 1. We wait 5 Seconds
# 2. We check the state of each hubs. If the user is found and the state show that it downloaded the dataset, skip it
# 3. If the user isn't recognized (=disconnected), we :
# - Classic mode : remove it from the active hub list and remove his dataset. If he was the last one, the start program is over
# - Class Mode : Since one user is down, we totally stop the start program
# 4. If all the user are ready to move on, we continue. Else, we restart from #1
# [------------------------------------------------------] 
def download_dataset_check_thread():
        insert_logs("[INFO] Sending the datasets")
        while(True):
            time.sleep(5)
            i=0
            for hub in hubs:
                print(user_array[0].status + "ici a la fin de dataset_adapt ("+str(len(user_array))+")")
                j=0
                # >>> Checking for each hub if he is still registered and his status is correct
                for k in range(len(user_array)):
                    if user_array[k].name==hub[0] and (user_array[k].status=="WAITING" or user_array[k].status=="DATASETS" or user_array[k].status=="MODELS"):
                        if user_array[k].status=="MODELS" or user_array[k].status=="WAITING":
                            i+=1
                        break
                    else:
                        j+=1
                if j==len(user_array):
                    # >>> The user is not found, or the status is incorrect, so we're gonna remove him from the hub active list
                    # >>> Classic mode : we remove the user
                    if not typeOfSelection:
                        for dataset in list_dataset:
                            if dataset[1]==hub[0]:
                                dataset[1]="None"
                                break
                        hubs.remove(hub)
                        insert_logs(f"[INFO] {hub[0]} removed due to inactivity. Continuing without it.")
                        if len(hubs)==0:
                            # >>> No more active hub, so we stop the start program
                            insert_logs("[ERROR] No more users active left. End of the start program.")
                            return
                    # >>> Class mode : We stop the start program
                    else:
                        insert_logs("[ERROR] One user disconnected. End of the start program.")
                        for hub in hubs:
                            for user in user_array:
                                if user.name == hub[0]:
                                    update_user_status(user.name,"ONLINE")
                        return
            # >>> All the active hub have finished their part
            if i==len(hubs):
                client.publish("Data/Server",construct_message("0","MODEL READY"))
                return

# ╔══════════════════════════════════════╗
# ║          10. Sending models          ║
# ╚══════════════════════════════════════╝

# ────────────────[Send the download message & launch the model reception Thread]───────────────
# [------------------------------------------------------]
# 1. For each hub that is working, we send him to download the model
# [------------------------------------------------------] 
def download_models():
    insert_logs("[INFO] Sending the models")
    model_extension=  sql_get_single("SELECT path FROM models WHERE model_id="+model_id+";").split(".")[1]
    for hub in hubs:
        if get_user_status(hub[0])!="WAITING":
            client.publish("hubs/"+hub[0]+"/commands",construct_message(hub[0],"DOWNLOAD MODELS","id:"+str(model_id)+"|name:Model."+model_extension))
    t=Thread(target=(download_model_check_thread)).start()

# ────────────────[Model reception Thread]───────────────
# [------------------------------------------------------]
# 1. We wait 5 Seconds
# 2. We check the state of each hubs. If the user is found and the state show that it downloaded the model, skip it
# 3. If the user isn't recognized (=disconnected), we :
# - Classic mode : remove it from the active hub list and remove his dataset. If he was the last one, the start program is over
# - Class Mode : Since one user is down, we totally stop the start program
# 4. If all the user are ready to move on, we continue. Else, we restart from #1
# [------------------------------------------------------] 
def download_model_check_thread():
    while(True):
        time.sleep(5)
        i=0
        for hub in hubs:
            j=0
            # >>> Checking for each hub if he is still registered and his status is correct
            for k in range(len(user_array)):
                if user_array[k].name==hub[0] and (user_array[k].status=="WAITING" or user_array[k].status=="MODELS" or user_array[k].status=="WEIGHT" or user_array[k].status=="READY"):
                    if user_array[k].status=="READY" or user_array[k].status=="WEIGHT" or user_array[k].status=="WAITING":
                        i+=1
                    break
                else:
                    j+=1
            if j==len(user_array):
                # >>> The user is not found, or the status is incorrect, so we're gonna remove him from the hub active list
                # >>> Classic mode : we remove the user
                    if not typeOfSelection:
                        for dataset in list_dataset:
                            if dataset[1]==hub[0]:
                                dataset[1]="None"
                                break
                        hubs.remove(hub)
                        insert_logs(f"[INFO] {hub[0]} removed due to inactivity. Continuing without it.")
                        if len(hubs)==0:
                            # >>> No more active hub, so we stop the start program
                            insert_logs("[ERROR] No more users. End of the start program.")
                            return
                    # >>> Class mode : We stop the start program
                    else:
                        insert_logs("[ERROR] One user disconnected. End of the start program.")
                        for hub in hubs:
                            for user in user_array:
                                if user.name == hub[0]:
                                    update_user_status(user.name,"ONLINE")
                        return
        if i==len(hubs):
            # >>> All the active hub have finished their part
            if mode_of_execution=="FL":
                client.publish("Data/Server",construct_message("0","DOWNLOAD THE WEIGHT"))
            else:
                client.publish("Data/Server",construct_message("0","START THE EXECUTION"))
            return
        
# ╔══════════════════════════════════════╗
# ║         11. Launch execution         ║
# ╚══════════════════════════════════════╝

# ────────────────[Send the execution message & launch the Execution reception Thread]───────────────
# [------------------------------------------------------]
# 1. For each hub that is working, we send him to launch the model
# [------------------------------------------------------] 
def launch_execution():
    insert_logs("[INFO] [Launching the execution]")
    for hub in hubs:
        if get_user_status(hub[0])!="WAITING":
            client.publish("hubs/"+hub[0]+"/commands",construct_message(hub[0],"LAUNCH THE MODEL","Mode:"+mode_of_execution))
            update_user_status(hub[0],"WORKING")
    t=Thread(target=(thread_check_execution)).start()

# ────────────────[Execution reception Thread]───────────────
# [------------------------------------------------------]
# 1. We wait 5 Seconds
# 2. We check the state of each hubs. If the user is found and the state show that it finished the execution, skip it
# 3. If the user isn't recognized (=disconnected), we :
# - Classic mode : remove it from the active hub list and remove his dataset. If he was the last one, the start program is over
# - Class Mode : Since one user is down, we totally stop the start program
# 4. If all the user are ready to move on, we continue. Else, we restart from #1
# [------------------------------------------------------] 
def thread_check_execution():
    global list_dataset
    while(True):
        time.sleep(5)
        i=0
        for hub in hubs:
            j=0
            # >>> Checking for each hub if he is still registered and his status is correct
            for k in range(len(user_array)):
                if user_array[k].name==hub[0] and (user_array[k].status=="WAITING" or user_array[k].status=="WORKING" or user_array[k].status=="FINISHED"):
                    if user_array[k].status=="FINISHED"or user_array[k].status=="WAITING":
                        i+=1
                        if user_array[k].status=="FINISHED":
                            insert_logs(f"{user_array[k].name} finished treating.")
                    break
                else:
                    j+=1
            if j==len(user_array):
                # >>> The user is not found, or the status is incorrect, so we're gonna remove him from the hub active list
                # >>> Classic mode : we remove the user
                    if not typeOfSelection:
                        for dataset in list_dataset:
                            if dataset[1]==hub[0]:
                                dataset[1]="None"
                                break
                        hubs.remove(hub)
                        insert_logs(f"[INFO] {hub[0]} removed due to inactivity. Continuing without it.")
                        if len(hubs)==0:
                            # >>> No more active hub, so we stop the start program
                            insert_logs("[ERROR] No more users. End of the start program.")
                            return
                    # >>> Class mode : We stop the start program
                    else:
                        insert_logs("[ERROR] One user disconnected. End of the start program.")
                        for hub in hubs:
                            for user in user_array:
                                if user.name == hub[0]:
                                    update_user_status(user.name,"ONLINE")
                        return
        if i==len(hubs):
            if mode_of_execution!="MA":
                    # >>> All the active hub have finished their part
                    insert_logs("Execution finished with success. Checking if more datasets need to be executed")

                    for i in range(0,len(list_dataset)):
                        if list_dataset[i][1]!="None" and list_dataset[i][1]!="Done":
                            list_dataset[i][1]="Done"
                    client.publish("Data/Server",construct_message(str(0),"RELAUNCH THE EXECUTION"))
            else:
                    client.publish("Data/Server",construct_message("0","END OF THE TURN"))
            return

# ╔══════════════════════════════════════╗
# ║   12. Federated Learning - Weights   ║
# ╚══════════════════════════════════════╝

# ────────────────[Send the weight message & launch the weight reception Thread]───────────────
# [------------------------------------------------------]
# 1. For each hub that is working, we send him to launch the model
# [------------------------------------------------------] 
def download_weight():
    insert_logs("[INFO] Sending the Weight")
    for hub in hubs:
        if get_user_status(hub[0])!="WAITING":
            client.publish("hubs/"+hub[0]+"/commands",construct_message(hub[0],"DOWNLOAD WEIGHT"))
    t=Thread(target=(download_weight_check_thread)).start()
       
# ────────────────[Weight reception Thread]───────────────
# [------------------------------------------------------]
# 1. We wait 5 Seconds
# 2. We check the state of each hubs. If the user is found and the state show that it finished the execution, skip it
# 3. If the user isn't recognized (=disconnected), we :
# - Classic mode : remove it from the active hub list and remove his dataset. If he was the last one, the start program is over
# - Class Mode : Since one user is down, we totally stop the start program
# 4. If all the user are ready to move on, we continue. Else, we restart from #1
# [------------------------------------------------------] 
def download_weight_check_thread():
    while(True):
        time.sleep(5)
        i=0
        for hub in hubs:
            j=0            
            # >>> Checking for each hub if he is still registered and his status is correct
            for k in range(len(user_array)):
                if user_array[k].name==hub[0] and (user_array[k].status=="WAITING" or user_array[k].status=="WEIGHT" or user_array[k].status=="READY"):
                    if user_array[k].status=="READY" or user_array[k].status=="WAITING":
                        i+=1
                    break
                else:
                    j+=1
            if j==len(user_array):
                # >>> The user is not found, or the status is incorrect, so we're gonna remove him from the hub active list
                # >>> Classic mode : we remove the user
                    if not typeOfSelection:
                        for dataset in list_dataset:
                            if dataset[1]==hub[0]:
                                dataset[1]="None"
                                break
                        hubs.remove(hub)
                        insert_logs(f"[INFO] {hub[0]} removed due to inactivity. Continuing without it.")
                        if len(hubs)==0:
                            # >>> No more active hub, so we stop the start program
                            insert_logs("[ERROR] No more users. End of the start program.")
                            return
                    # >>> Class mode : We stop the start program
                    else:
                        insert_logs("[ERROR] One user disconnected. End of the start program.")
                        for hub in hubs:
                            for user in user_array:
                                if user.name == hub[0]:
                                    update_user_status(user.name,"ONLINE")
                        return
        if i==len(hubs):
            # >>> All the active hub have finished their part
            client.publish("Data/Server",construct_message("0","START THE EXECUTION"))
            return

# ╔══════════════════════════════════════╗
# ║ 13. Federated Learning - Aggregation ║
# ╚══════════════════════════════════════╝
# ────────────────[Launch the aggregation program]───────────────
# [------------------------------------------------------]
# 1. We wait 5 Seconds
# 2. We check the state of each hubs. If the user is found and the state show that it finished the execution, skip it
# 3. If the user isn't recognized (=disconnected), we :
# - Classic mode : remove it from the active hub list and remove his dataset. If he was the last one, the start program is over
# - Class Mode : Since one user is down, we totally stop the start program
# 4. If all the user are ready to move on, we continue. Else, we restart from #1
# [------------------------------------------------------] 
def launch_aggregation_federated_learning():
    t=Thread(target=aggregation_federated_learning_thread).start()

def aggregation_federated_learning_thread():
        result_file= default_path / "Result"
        output_path= default_path / "Weights" / "server_weight.pth"
        model_path=  sql_get_single("SELECT path FROM models WHERE model_id="+model_id+";")
        p = subprocess.Popen([
        "python3", 
        model_path,
        "--mode", "aggregate", 
        "--weights-dir",    result_file,
        "--output-path", output_path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
        )
        for line in p.stdout:
            insert_logs(line.rstrip(),"Aggregation")
        p.wait()
        insert_logs("Finished treating the Aggregation.")
        os.makedirs(default_path / "logs" / str(work_id) / str(number_of_turn) / "result", exist_ok=True)
        shutil.copy(output_path,default_path / "logs" / str(work_id) / str(number_of_turn) / "result" / "weight_server.pth")
        client.publish("Data/Server",construct_message("0","END OF THE TURN"))

# ╔══════════════════════════════════════╗
# ║         14. Files of the logs        ║
# ╚══════════════════════════════════════╝

def logs_to_file(message, user="Server"):
    if mode_of_execution!="MA" and mode_of_execution!="None" and user!="Server" :
        if user!="Initialisation" and user!="Aggregation":
            for dataset in list_dataset:
                if dataset[1]==user:
                    name_of_file=dataset[0].split("/")[-1]
                    file_directory=default_path / "logs" / str(work_id) / str(number_of_turn) / "logs"
                    file_path= file_directory / (name_of_file.split(".")[0]+".txt")
        else:
            file_directory=default_path / "logs" / str(work_id) / str(number_of_turn) / "logs"
            file_path= file_directory / "Server.txt"
    else:
        if number_of_turn==-1:
            file_directory=default_path / "logs" / "Server" 
            file_path=default_path / "logs" / "Server" / "Server.txt"
        elif mode_of_execution=="MA" and user!="Server" and user!="Initialisation" and user!="Aggregation":
            file_directory=default_path / "logs" / str(work_id) / str(number_of_turn) / "logs"
            file_path= file_directory / ("execution.txt")
        else:
            file_directory=default_path / "logs" / str(work_id) / str(number_of_turn) / "logs"
            file_path= file_directory / "Server.txt"
    os.makedirs(file_directory, exist_ok=True)
    with open(file_path,"a") as f:
        f.write(message +"\n")
    



def decrypt_message(payload_data):
    """
    Prend une chaîne Base64 et recrée le fichier binaire.
    """
    try:
        # 1. Ré-encoder la chaîne de caractères en octets
        encoded_bytes = payload_data[3].split("inside:")[1].encode('utf-8')
        
        # 2. Décoder les octets Base64 pour obtenir le contenu binaire original
        binary_data = base64.b64decode(encoded_bytes)
        file_name=payload_data[3].split("name:")[1].split("|")[0]

        BASE_DIR = default_path / "Result"
    
        # 2. Construire le chemin complet du fichier de sortie
        output_path = os.path.join(BASE_DIR, file_name)

        # 3. Créer le répertoire s'il n'existe pas
        os.makedirs(BASE_DIR, exist_ok=True)
        # 3. Écrire les données binaires dans un nouveau fichier
        with open(output_path, "wb") as file:
            file.write(binary_data)
            
        print(f"Fichier recréé avec succès : {output_path}")
        shutil.copyfile(output_path,default_path / "logs" / str(work_id) / str(number_of_turn) / "result" / file_name)
    except Exception as e:
        print(f"Erreur lors du décodage et de l'écriture du fichier : {e}")

# ╔══════════════════════════════════════╗
# ║        15. Handling exceptions       ║
# ╚══════════════════════════════════════╝




# ╔══════════════════════════════════════╗
# ║            16. Main Program          ║
# ╚══════════════════════════════════════╝

def main():
    #  Part to accept the argument -v, in order to have some visual log
    global verbose
    parser = argparse.ArgumentParser(description="Script with global verbose flag")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    verbose = args.verbose
    verbose=True
    # Function to launch the connexion to the sql database
    connect_sql()


if __name__=="__main__":
    main()



# A FAIRE : SUPPRIMER LES FICHIERS DU DATASET ET DU DOSSIER MODEL DU COTE CLIENT POUR , QUAND IL LE DOWNLOAD, IL Y EN A QU'UN
