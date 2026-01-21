# ╔══════════════════════════════════════╗
# ║                Modules               ║
# ╚══════════════════════════════════════╝
import base64
import os
from pathlib import Path
import shutil
from paho.mqtt import client as mqtt_client
import re, uuid, random,time
from threading import Thread, Event
from urllib.request import urlretrieve
import subprocess
# ╔══════════════════════════════════════╗
# ║             Présentation             ║
# ╚══════════════════════════════════════╝







# ╔══════════════════════════════════════╗
# ║──────────────────────────────────────║
# ╚══════════════════════════════════════╝

# ╔══════════════════════════════════════╗
# ║            Global Variable           ║
# ╚══════════════════════════════════════╝
# == IP & Port of the broker
broker = os.getenv('MQTT_HOST', '172.18.0.1')
port = 1883
# == Unique ID (MAC Address) for the first connexion
client_id='-1'
# MAC Address : ':'.join(re.findall('..', '%012x' % uuid.getnode()))
#Topic used by the MQTT Connexion
topicConnexion=""
topicCommande = ""
topicLog = ""
topicMetric = ""

global client

connexion_handled = False

last_hb_server=0
global server_alive

global part_number
global weight_path
global dataset_path, model_path, modeOfExecution
model_already_downloaded=False


API_HOST = os.getenv("API_HOST")
API_PORT = os.getenv("API_PORT")
GLOBAL_PATH = Path("/") / "app" / "FL_hub"

global current_thread
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
    if receiver_id==0:
        receiver_id=str(0)
    return "["+client_id+"] ["+receiver_id+"] ["+instructions+"] ["+details+"]"

# ╔══════════════════════════════════════╗
# ║    1. Handling the MQTT Connection   ║
# ╚══════════════════════════════════════╝
# ────────────────[Creating the mqtt client]───────────────
# [------------------------------------------------------]
# 1. Create the mqtt client, while redefining the :
# - on_connect
# - on_disconnect
# - on_message
# [------------------------------------------------------]
def connect_mqtt():
    # Client MQTT v3.1.1 (compatible avec tout broker standard)
    client = mqtt_client.Client(client_id=client_id)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    return client


# ────────────────[Connect to the mqtt client]───────────────
# [------------------------------------------------------]
# 1. Initialize the mqtt connection  : 
# - Connect to the broker
# - ask for his name, and wait for the answer
# - If he receives a name, start listening to the server
# - Else, wait 30 seconds and try reconnecting
# [------------------------------------------------------]
def launch_mqtt_connexion():
    global client_id,topicConnexion, client
    client_id=os.getenv("MAC_ADDRESS")
    topicConnexion="connexion/"+client_id
    client = connect_mqtt()
    while True:
        try:
            if not client.is_connected():
                client_id=os.getenv("MAC_ADDRESS")
                print("[INFO] Attempting to connect to broker...")
                client.connect(broker, port)
                ask_connexion()
                client.loop_forever()
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}. Waiting 30 seconds before a new try.")
            time.sleep(30)


def on_connect(client, userdata, flags, rc):
    """Callback exécuté lors de la connexion au broker MQTT"""
    if rc == 0:
        client.subscribe(topicConnexion)
        print(f"[INFO] Connected to MQTT Broker")
    else:
        print(f"[ERROR] Failed to connect, return code {rc}")

# Reprise de on_disconnect pour avoir un message lors de la déconnexion
def on_disconnect(client, userdata, rc):
    """Callback exécuté lors de la déconnexion du broker MQTT"""
    raise Exception("[Disconnected from the program (Error code "+str(rc)+")]")


#Fonction final_subscribe qui permet de s'abonner aux topics assignés aux clients
def final_subscribe():
    global topicCommande
    global topicLog
    global topicMetric
    topicCommande="hubs/"+client_id+"/commands"
    topicLog="hubs/"+client_id+"/logs"
    topicMetric="hubs/"+client_id+"/metrics"
    client.subscribe(topicCommande)
    client.subscribe(topicLog)
# ╔══════════════════════════════════════╗
# ║      2. Connexion to the server      ║
# ╚══════════════════════════════════════╝
# ────────────────[Ask to open a connexion]───────────────
# [------------------------------------------------------]
# 1. Ask the server to be connected and receive his username, with : 
# - His current MAC Address
# - His current stockage 
# 2. He then launch a thread to get the answer
# [------------------------------------------------------]
def ask_connexion():
        stat = shutil.disk_usage("/")
        free=str((int(str(stat).split("free=")[1].split(")")[0])/10**9)+2)
        msg=construct_message("0","Asking for connexion","CAPACITY:"+free+"GO")
        client.publish(topicConnexion,msg)
        Thread(target=is_connexion_handled).start()
        
# ────────────────[Waiting for an answer]───────────────
# [------------------------------------------------------]
# 1. Wait 8 Seconds and check if he is connected or not
# 2. If he isn't, he disconnect himself
# [------------------------------------------------------]
def is_connexion_handled():
    global connexion_handled
    connexion_handled=False
    time.sleep(8)
    if not connexion_handled:
        client.publish(topicConnexion,construct_message(client_id,"DISCONNECT"))
    else:
        return

# ────────────────[Getting an answer]───────────────
# [------------------------------------------------------]
# 1. Wait 8 Seconds and check if he is connected or not
# 2. If he isn't, he disconnect himself
# [------------------------------------------------------]
def received_connexion_message(payload_data):
        global connexion_handled
        if "NAME:" in payload_data[2]:
            connexion_handled=True
            global client_id
            # On split sur 'NAME:' pour récupérer le nom
            mac = payload_data[1]
            name = payload_data[2].split(":", 1)[1]
            if mac.lower() == client_id.lower():  # compare MAC
                client_id = name.strip()
                print(f"[INFO] Received client name:{client_id}.")
                global server_alive
                server_alive=True
                final_subscribe()
                start_heartbeat()
            else:
                print(f"[WARNING] MAC mismatch: {mac}")
        elif "NOT REGISTERED IN THE DATABASE" in payload_data[2]:
            print("[WARNING] Hub not registered in the database. End of connexion.")


# ╔══════════════════════════════════════╗
# ║             3. Heartbeats            ║
# ╚══════════════════════════════════════╝


#SENDING A HEARTBEAT MESSAGE EVERY 30 SECONDS
def sending_heartbeat():
    t=Thread(target=heartbeat_thread)
    t.start()


def heartbeat_thread():
    global server_alive
    while True:
        time.sleep(15)
        if not server_alive:
            return
        heartbeat_request()



def heartbeat_request():
    message=construct_message("0","HEARTBEAT")
    topic = "hubs/"+client_id+"/logs"
    client.publish(topic,message)
    print("[INFO] Sending Heartbeat.")

# CHECKING IF WE RECEIVED A HEARTBEAT MESSAGE


def update_heartbeat():
    global last_hb_server
    print("[INFO] Received Heartbeat.")
    last_hb_server=time.time()

def check_heartbeat():
    t=Thread(target=check_heartbeat_thread)
    t.start()

def check_heartbeat_thread():
    global last_hb_server
    global server_alive
    while server_alive:
        prev = last_hb_server
        time.sleep(15)
        if not server_alive:
            return
        if last_hb_server > prev:
            print("[INFO] Heartbeat detected without latency")
            # un heartbeat est arrivé pendant les 30s → on repart pour 30s
            continue
        for _ in range(3):
            time.sleep(2)
            if last_hb_server > prev:
                print("[INFO] Heartbeat detected with latency")
                break
        else:
            # si la boucle se termine sans break → aucun heartbeat reçu
            print("[ERROR] Server Dead. Relaunching a connexion.")
            server_alive=False
            client.publish(topicConnexion,construct_message(client_id,"DISCONNECT"))
            return

def start_heartbeat():
    sending_heartbeat()
    check_heartbeat()

# ╔══════════════════════════════════════╗
# ║          4.Received a message        ║
# ╚══════════════════════════════════════╝

def on_message(client,userdata,message):
    payload_data = re.findall(r"\[(.*?)\]",str(message.payload.decode("utf-8")))
    topic = message.topic
    if payload_data[0]!=client_id:
        print("[RECEIVED]"+message.payload.decode("utf-8"))
        if topic==topicConnexion:
            received_connexion_message(payload_data)
        elif topic==topicCommande:
            received_command_message(payload_data)
        elif topic==topicLog and payload_data[2]=="HEARTBEAT":
            update_heartbeat()
    else:
        if topic==topicConnexion and payload_data[2]=="DISCONNECT":
            client.disconnect()

def received_command_message(payload_data):
    global model_already_downloaded
    if payload_data[2]=="DOWNLOAD DATASETS":
        download_dataset(payload_data)
    elif payload_data[2]=="DOWNLOAD MODELS":
        download_model(payload_data)
    elif payload_data[2]=="DOWNLOAD WEIGHT":
        download_weight(payload_data)
    elif payload_data[2]=="LAUNCH THE MODEL":
        execution_model(payload_data)
    elif payload_data[2]=="END OF THE START PROGRAM":
        model_already_downloaded=False

# ╔══════════════════════════════════════╗
# ║        5. Receiving the dataset      ║
# ╚══════════════════════════════════════╝

def download_dataset(payload_data):
    global current_thread, current_thread
    current_thread=Thread(target=download_dataset_thread,args=(payload_data,)).start()

def download_dataset_thread(payload_data):
        global dataset_path, part_number, current_thread
        #D'abord on supprime les dossiers Dataset et Model   
        part_number=payload_data[3].split("|")[1].split("part_number:")[1]
        id=payload_data[3].split("|")[0].split("id:")[1]
        name=payload_data[3].split("name:")[1]
        print(str(f"http://{API_HOST}:{API_PORT}/dataset/"+str(id)+"/"+str(part_number)))
        url=f"http://{API_HOST}:{API_PORT}/dataset/"+str(id)+"/"+str(part_number)
        dataset_path=Path(str(GLOBAL_PATH) + "/Dataset/"+name).expanduser()
        dataset_path.parent.mkdir(parents=True,exist_ok=True)
        t=urlretrieve(url,dataset_path)
        client.publish(topicCommande,construct_message("0","DATASET DOWNLOADED"))
        current_thread=None
 
# ╔══════════════════════════════════════╗
# ║         6. Receiving the model       ║
# ╚══════════════════════════════════════╝
def download_model(payload_data):
    global current_thread
    current_thread=Thread(target=download_model_thread,args=(payload_data,)).start()

def download_model_thread(payload_data):
        global model_already_downloaded, current_thread
        if not model_already_downloaded:
            model_already_downloaded=True
            print("[#### DOWNLOADING MODEL ####]")
            global model_path
            id=payload_data[3].split("|")[0].split("id:")[1]
            name=payload_data[3].split("name:")[1]
            url=f"http://{API_HOST}:{API_PORT}/model/"+str(id)
            model_path=Path(str(GLOBAL_PATH) + "/Model/"+name).expanduser()
            model_path.parent.mkdir(parents=True,exist_ok=True)
            t=urlretrieve(url,model_path)
        client.publish(topicCommande,construct_message("0","MODEL DOWNLOADED"))
        current_thread=None

# ╔══════════════════════════════════════╗
# ║         7. Executing the model       ║
# ╚══════════════════════════════════════╝

def execution_model(payload_data):
    global current_thread
    current_thread=Thread(target=execution_model_thread, args=(payload_data,)).start()

def execution_model_thread(payload_data):
    global weight_path, modeOfExecution, current_thread
    modeOfExecution=payload_data[3].split("Mode:")[1]
    if modeOfExecution=="FL":
        p = subprocess.Popen(
            ["python3", "-u",str(model_path),
            "--dataset", str(dataset_path),
            "--model-path", str(weight_path),
            "--output-path",str( GLOBAL_PATH  / "Result" / ("dataset"+str(part_number)+".pth"))],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    elif modeOfExecution=="ML":
        p=subprocess.Popen(
            ["python3", "-u",str(model_path),
            str(dataset_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    else:
        p=subprocess.Popen(
            ["python3", "-u",str(model_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    for line in p.stdout:
        sending_log_to_server(line.rstrip())
    error=False
    for line in p.stderr:
        error=True
        sending_log_to_server("[ERROR]"+line.rstrip())
    if error==True:
        sending_log_to_server("[ERROR CAUGHT] Finishing the execution.")
    else:
        sending_log_to_server("Work finished. Waiting for another one.")
        if modeOfExecution=="FL":
            client.publish(topicCommande,construct_message(0,"WAITING FOR WORK","name:"+("dataset"+str(part_number)+".pth")+"|inside:"+encode_file_to_base64(GLOBAL_PATH  / "Result" / ("dataset"+str(part_number)+".pth"))))
        else:
            client.publish(topicCommande,construct_message(0,"WAITING FOR WORK"))
    current_thread=None

def sending_log_to_server(message):
    print("[Script:"+message+"]")
    client.publish(topicLog,construct_message("0",message))
    
# ╔══════════════════════════════════════╗
# ║         8. Receiving the weight      ║
# ╚══════════════════════════════════════╝


def download_weight(payload_data):
        global current_thread
        url=f"http://{API_HOST}:{API_PORT}/weight"
        global weight_path
        weight_path=Path(str(GLOBAL_PATH) + "/Weight/client_weight.pth").expanduser()
        print(str(weight_path) + "ici")
        weight_path.parent.mkdir(parents=True,exist_ok=True)
        t=urlretrieve(url,weight_path)
        client.publish(topicCommande,construct_message("0","WEIGHT DOWNLOADED"))

# ╔══════════════════════════════════════╗
# ║     9. Sending the result weight     ║
# ╚══════════════════════════════════════╝

def encode_file_to_base64(file_path):
    """
    Lit un fichier binaire et retourne son contenu encodé en Base64 (str).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier n'existe pas: {file_path}")

    with open(file_path, "rb") as file:
        # 1. Lire le contenu binaire
        binary_data = file.read()
        
        # 2. Encoder le contenu binaire en Base64
        encoded_bytes = base64.b64encode(binary_data)
        
        # 3. Convertir en chaîne de caractères (str) pour l'envoi MQTT
        encoded_string = encoded_bytes.decode('utf-8')
        
    return encoded_string

    
if __name__ == "__main__":
    launch_mqtt_connexion()

