import csv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List, Optional
import psycopg2
import os
from datetime import datetime
import json
from pathlib import Path
import shutil
import time 
import paho.mqtt.client as mqtt 

#==============================================#
#================ Configuration =================#
#==============================================#

# Chemins Fichiers
# CECI DOIT CORRESPONDRE AU CHEMIN INTERNE DU CONTENEUR DÉFINI DANS LE BIND MOUNT (/app/FL)
BASE_DIR = Path("/app/FL") 

# Variables de connexion globales
connexion_sql = None

#==============================================#
#================ Fonctions SQL =================#
#==============================================#

def connect_sql():
    global connexion_sql
    try:
        connexion_sql = psycopg2.connect(
            database="FL", 
            user="program",
            host="postgresql", 
            password="program"
        )
        print("Connexion à la base de données établie avec succès.")
    except Exception as e:
        print(f"Exception lors du lancement de la base de données (Hôte: {DB_HOST}) : {e}")

connect_sql()

# Detect TimescaleDB availability once
TIMESCALE_AVAILABLE = False
try:
    with connexion_sql.cursor() as _cur:
        _cur.execute("SELECT 1 FROM pg_extension WHERE extname='timescaledb'")
        TIMESCALE_AVAILABLE = _cur.fetchone() is not None
except Exception:
    TIMESCALE_AVAILABLE = False

#==============================================#
#================  API App  ===================#
#==============================================#
API_app = FastAPI(title="Hub Management API", version="1.2")

API_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Autoriser TOUTES les origines
    allow_credentials=True,     
    allow_methods=["*"],        # Autoriser TOUTES les méthodes
    allow_headers=["*"],        
)

#==============================================#
#=============== API PATH : Hub & Fichiers (Non Modifiés) ===============#
#==============================================#

@API_app.post("/hub")
async def upload_hub(
    type:str=Form(...),
    mac_address:str=Form(...),
):
    try:
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute("SELECT hub_id FROM hubs WHERE mac_address='"+mac_address+"';")
            if cursol_sql.fetchone() is None:
                i=0
                while True:
                    i+=1
                    if i < 10 :
                        name= type+"0"+str(i)
                    else:
                        name=type+str(i)
                    cursol_sql.execute("SELECT hub_id FROM hubs WHERE name='"+name+"';")
                    if cursol_sql.fetchone() is None:
                        cursol_sql.execute("INSERT INTO hubs (mac_address, name, type, stockage, status) VALUES (%s, %s, %s, %s, %s)",(mac_address,name,type,'0',"OFFLINE"))
                        connexion_sql.commit()
                        break
        return
    except Exception as e:
        print("Error inserting hubs : ",e)

@API_app.get("/hubs")
def list_hubs():
    try:
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute("SELECT hub_id, mac_address, name, type, status, stockage FROM hubs")
            rows = cursol_sql.fetchall()
            return [{"id": r[0], "mac": r[1], "name": r[2], "type": r[3], "status": r[4], "stockage": r[5]} for r in rows]
    except Exception as e:
        print("Erreur list_hubs:", e)
        return []

@API_app.post("/upload")
async def upload_model_dataset(
    type_of_upload: str = Form(...),
    file_name: str = Form(...),
    uploaded_by: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...)
):
    try:
        table_name = "models" if type_of_upload == "models" else "datasets"
        id_column = "model_id" if type_of_upload == "models" else "dataset_id"
        
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute(
                f"INSERT INTO {table_name} (name, path, upload_date, uploaded_by, description) VALUES (%s, %s, %s, %s, %s) RETURNING {id_column}",
                (file_name, "", datetime.now(), uploaded_by, description)
            )
            upload_id = cursol_sql.fetchone()[0]
        
        upload_dir = BASE_DIR / (type_of_upload.capitalize()) / str(upload_id)
        os.makedirs(upload_dir, exist_ok=True)
        upload_path = upload_dir / file.filename

        with open(upload_path, "wb") as f:
            f.write(await file.read())

        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute(
                f"UPDATE {table_name} SET path=%s WHERE {id_column}=%s",
                (str(upload_path), upload_id)
            )
        connexion_sql.commit()
        return {"status": "uploaded", "id": upload_id, "filename": file.filename, "path": str(upload_path)}
    except Exception as e:
        connexion_sql.rollback()
        print("Erreur upload_dataset:", e)
        raise HTTPException(status_code=500, detail="Erreur serveur lors de l'upload du fichier")

@API_app.post("/update")
async def modify_model_dataset(
    id: str = Form(...),
    type_of_upload: str = Form(...),
    file_name: str = Form(...),
    uploaded_by: str = Form(...),
    description: str = Form(None),
    upload_date: str = Form(None),
    selectedFile:str=Form(...),
    file: UploadFile = File(None)
):
    try:
        table_name = "models" if type_of_upload == "models" else "datasets"
        id_column = "model_id" if type_of_upload == "models" else "dataset_id"
        upload_dt = datetime.fromisoformat(upload_date)
        
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute(
                f"UPDATE {table_name} SET name=%s, upload_date=%s, uploaded_by=%s, description=%s WHERE {id_column}=%s;",
                (file_name, upload_dt, uploaded_by, description, id)
            )
            
        if selectedFile=="true" and file:
            upload_dir = BASE_DIR / (type_of_upload.capitalize()) / str(id)
            
            if upload_dir.exists() and str(BASE_DIR) in str(upload_dir):
                shutil.rmtree(upload_dir)
                
            os.makedirs(upload_dir,exist_ok=True)
            update_path=upload_dir / file.filename
            
            with open(update_path, "wb") as f:
                f.write(await file.read())
                
            with connexion_sql.cursor() as cursol_sql:
                cursol_sql.execute(
                    f"UPDATE {table_name} SET path=%s WHERE {id_column}=%s",
                    (str(update_path), id)
                )
        
        connexion_sql.commit()
        print("Modification réussie")

        return {"status": "success"}

    except Exception as e:
        connexion_sql.rollback()
        print("Erreur:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour")

class deletePayload(BaseModel):
    type:str
    id:str

@API_app.delete("/delete")
async def delete_model_dataset(payload:deletePayload):
    try:
        table_name = payload.type
        id_column = "model_id" if table_name == "models" else "dataset_id"
        
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute(f"SELECT path FROM {table_name} WHERE {id_column}=%s", (payload.id,))
            row = cursol_sql.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"{table_name.capitalize()} non trouvé")
            path = Path(row[0])
            dir_to_delete = path.parent
            
            if dir_to_delete.exists() and str(BASE_DIR) in str(dir_to_delete):
                shutil.rmtree(dir_to_delete)
                print(f"Dossier supprimé : {dir_to_delete}")
            
            cursol_sql.execute(f"DELETE FROM {table_name} WHERE {id_column}=%s", (payload.id,))
            
        connexion_sql.commit()
        return {"status": "deleted", "id": payload.id}
    except Exception as e:
        connexion_sql.rollback()
        print("Erreur delete:", e)
        raise HTTPException(status_code=500, detail="Erreur serveur lors de la suppression")

#==============================================#
#============= API PATH : Models (Non Modifiés) ==============#
#==============================================#

@API_app.get("/models")
def list_models():
    try:
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute(
                "SELECT model_id, name, path, upload_date, uploaded_by, description FROM models"
            )
            rows = cursol_sql.fetchall()
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "path": r[2],
                    "upload_date": r[3],
                    "uploaded_by": r[4],
                    "description": r[5],
                }
                for r in rows
            ]
    except Exception as e:
        print("Erreur list_models:", e)
        return []


@API_app.get("/model/{id}")
def download_model(id: int):
    try:
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute("SELECT name, path FROM models WHERE model_id=%s", (id,))
            row = cursol_sql.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Model not found")
        return FileResponse(path=row[1], filename=row[0], media_type="application/octet-stream")
    except Exception as e:
        print("Erreur download_model:", e)
        raise HTTPException(status_code=500, detail="Erreur serveur lors du téléchargement du modèle")


@API_app.get("/weight")
def download_weight():
    try:
        weight_path=str(BASE_DIR / "Weights" / "server_weight.pth")
        return FileResponse(path=weight_path, filename="server_weight.pth", media_type="application/octet-stream")
    except Exception as e:
        print("Erreur download_weight:", e)
        raise HTTPException(status_code=500, detail="Erreur serveur lors du téléchargement de la weight")


#==============================================#
#============= API PATH : Datasets (Non Modifiés) ============#
#==============================================#
@API_app.get("/datasets")
def list_datasets():
    try:
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute(
                "SELECT dataset_id, name, path, upload_date, uploaded_by, description FROM datasets"
            )
            rows = cursol_sql.fetchall()
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "path": r[2],
                    "upload_date": r[3],
                    "uploaded_by": r[4],
                    "description": r[5],
                }
                for r in rows
            ]
    except Exception as e:
        print("Erreur list_datasets:", e)
        return []


@API_app.get("/dataset/{id}")
def download_dataset(id: int):
    try:
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute("SELECT name, path FROM datasets WHERE dataset_id=%s", (id,))
            row = cursol_sql.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Dataset not found")
        return FileResponse(path=row[1], filename=row[0], media_type="application/octet-stream")
    except Exception as e:
        print("Erreur download_dataset:", e)
        raise HTTPException(status_code=500, detail="Erreur serveur lors du téléchargement du dataset")


@API_app.get("/dataset/{id}/{part_number}")
def get_dataset_part(id: int, part_number: int):
    try:
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute("SELECT path FROM datasets WHERE dataset_id=%s", (id,))
            row = cursol_sql.fetchone()
        print("ici")
        if not row:
            raise HTTPException(status_code=404, detail="Dataset not found")

        dataset_dir = Path(row[0]).parent
        part_filename = f"Dataset{part_number}.csv"
        part_path = dataset_dir / part_filename
        print(part_path)

        if not part_path.exists():
            raise HTTPException(status_code=404, detail=f"Part {part_number} not found for dataset {id}")

        return FileResponse(path=part_path, filename=part_filename, media_type="application/octet-stream")
    except Exception as e:
        print("Erreur get_dataset_part:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du sous-dataset")


#==============================================#
#============== API PATH : CSV Read et Logs (Non Modifiés) ===#
#==============================================#

class CsvReadRequest(BaseModel):
    path: str 

@API_app.post("/read-csv")
def read_csv(req: CsvReadRequest):
    full_path = req.path
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"Fichier non trouvé: {full_path}")
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            first_line = next(reader, None)
            if not first_line:
                raise HTTPException(status_code=400, detail="CSV vide")
            columns = [col.strip() for col in first_line]
        return {"columns": columns}
    except Exception as e:
        print("Erreur read_csv:", e)
        raise HTTPException(status_code=500, detail=f"Erreur lecture CSV: {str(e)}")


class LogsRequest(BaseModel):
    from_timestamp: str

@API_app.post("/logs")
def get_recent_logs(body: LogsRequest):
    from_timestamp = body.from_timestamp # Cette variable contient maintenant la chaîne UTC (ex: "...Z")

    try:
        with connexion_sql.cursor() as cursol_sql:
            cursol_sql.execute(
                """
                SELECT log_id, hub_name, logs, type, timestamp
                FROM logs
                WHERE timestamp >= CAST(%s AS timestamptz)
                ORDER BY timestamp ASC;
                """,
                # Le type PostgreSQL 'timestamptz' (timestamp with time zone) 
                # gère correctement la chaîne UTC (avec 'Z') envoyée par le frontend.
                (from_timestamp,) 
            )

            rows = cursol_sql.fetchall()

            # IMPORTANT : La colonne timestamp dans 'rows' est maintenant un objet datetime 
            # conscient du fuseau horaire, généralement en UTC.
            
            return [
                {
                    "log_id": r[0],
                    "hub_name": r[1],
                    "logs": r[2],
                    "type": r[3],
                    "timestamp": r[4] # FastAPI sérialisera correctement cet objet datetime en JSON ISO 8601
                }
                for r in rows
            ]

    except Exception as e:
        print("Erreur get_recent_logs:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des logs")


#==============================================#
#============== API PATH : Start (MQTT Simplifié) =#
#==============================================#

class Hub(BaseModel): 
    id: int
    name: str
    type: str
    status: str 
    selected: bool

class StartPayload(BaseModel):
    modelId: int
    datasetId: List[int] 
    hubs: List[Any] 
    parameter: str
    selectionByClass: List[bool]
    rulesList: List[List[Any]] 
    NumberOfParts: List[Optional[int]] 
    modeOfExecution: str
    numberOfTurn: int

@API_app.post("/start")
def start_program(payload: StartPayload):
    try:
        # --- 1. Préparation des Données ---
        
        datasets_str = ",".join(map(str, payload.datasetId))
        selection_class_str = ",".join(map(str, payload.selectionByClass))
        parts_str = ",".join(["None" if p is None else str(p) for p in payload.NumberOfParts])
        
        # Construction de la chaîne rulesList (format $ et |)
        all_turns_rules_string = []
        for turn_rules in payload.rulesList:
            single_turn_rule_strings = []
            for rule in turn_rules:
                if len(rule) == 4:
                    rule_str = ",".join(map(str, rule))
                    single_turn_rule_strings.append(rule_str)
            turn_rules_string = "|".join(single_turn_rule_strings)
            all_turns_rules_string.append(turn_rules_string)
        rules_list_str = "$".join(all_turns_rules_string)
        
        # --- 2. Construction du Message MQTT ---
        
        main_part = (
            "model:" + str(payload.modelId) + 
            "|dataset:" + datasets_str + 
            "|selectionByClass:" + selection_class_str + 
            "|numberOfParts:" + parts_str + 
            "|parameter:" + payload.parameter + 
            "|Mode:" + payload.modeOfExecution + 
            "|numberOfTurn:" + str(payload.numberOfTurn)
        )
        hubs_part = "{" + "|".join([h["name"] + "," + h["type"] for h in payload.hubs]) + "}"
        rules_part = "{" + rules_list_str.rstrip("$").rstrip("|") + "}" if rules_list_str else "{}"

        # Message final [Version][Turn][Type][Main|Hubs|Rules]
        mqtt_message = "[1][0][START][" + main_part + "|" + hubs_part + "|"  + rules_part + "]"
        
        
        # --- 3. Connexion, Publication, Déconnexion (sur demande) ---
        
        # Configuration MQTT locale à la fonction
        broker_host = os.getenv("MQTT_HOST", "host.docker.internal")
        broker_port = int(os.getenv("MQTT_PORT", 1883))
        topic = "Data/Server"
        
        client = mqtt.Client()
        try:
            client.connect(broker_host, broker_port)
            client.publish(topic, mqtt_message)
            client.disconnect() 
        except Exception as e:
            print(f"Erreur MQTT : Hôte={broker_host}, Port={broker_port}. Détail: {e}")
            raise HTTPException(status_code=503, detail="Erreur lors de l'envoi du message de démarrage MQTT. Le broker est-il disponible?")
            
        return {"status": "Program started successfully via MQTT"}
    except HTTPException as e:
        raise e
    except Exception as e:
        print("Erreur start_program (globale):", e)
        raise HTTPException(status_code=500, detail=f"Erreur serveur lors du démarrage du programme: {e}")


#==============================================#
#============== API PATH : Realtime (Nouveaux) =#
#==============================================#

@API_app.get("/v1/devices")
def api_list_devices():
    try:
        with connexion_sql.cursor() as cur:
            cur.execute(
                """
                SELECT device_id, COALESCE(name,''), COALESCE(type,''), COALESCE(location,''), created_at
                FROM devices
                ORDER BY created_at DESC
                """
            )
            rows = cur.fetchall()
            return [
                {
                    "device_id": r[0],
                    "name": r[1],
                    "type": r[2],
                    "location": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]
    except Exception as e:
        print("Erreur /v1/devices:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des devices")


@API_app.get("/v1/devices/{device_id}/latest")
def api_device_latest(device_id: str):
    try:
        with connexion_sql.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (sensor) sensor, value, unit, place, ts, received_at
                FROM measurements
                WHERE device_id = %s
                ORDER BY sensor, ts DESC
                """,
                (device_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "sensor": r[0],
                    "value": r[1],
                    "unit": r[2],
                    "place": r[3],
                    "ts": r[4],
                    "received_at": r[5],
                }
                for r in rows
            ]
    except Exception as e:
        print("Erreur /v1/devices/{id}/latest:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération du dernier état")


@API_app.get("/v1/measurements")
def api_measurements(
    device_id: Optional[str] = Query(None),
    sensor: Optional[str] = Query(None),
    fr: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=10000),
):
    try:
        where = []
        params: List[Any] = []
        if device_id:
            where.append("device_id = %s")
            params.append(device_id)
        if sensor:
            where.append("sensor = %s")
            params.append(sensor)
        if fr:
            where.append("ts >= CAST(%s AS timestamptz)")
            params.append(fr)
        if to:
            where.append("ts <= CAST(%s AS timestamptz)")
            params.append(to)
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        sql = (
            "SELECT device_id, sensor, value, unit, place, msg_id, ts, received_at, meta "
            + "FROM measurements" + where_sql + " ORDER BY ts DESC LIMIT %s"
        )
        params.append(limit)
        with connexion_sql.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [
                {
                    "device_id": r[0],
                    "sensor": r[1],
                    "value": r[2],
                    "unit": r[3],
                    "place": r[4],
                    "msg_id": r[5],
                    "ts": r[6],
                    "received_at": r[7],
                    "meta": r[8],
                }
                for r in rows
            ]
    except Exception as e:
        print("Erreur /v1/measurements:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des mesures")


def _parse_bucket_to_seconds(bucket: str) -> int:
    try:
        if bucket.endswith("ms"):
            return max(1, int(bucket[:-2])) // 1000
        if bucket.endswith("s"):
            return max(1, int(bucket[:-1]))
        if bucket.endswith("m"):
            return int(bucket[:-1]) * 60
        if bucket.endswith("h"):
            return int(bucket[:-1]) * 3600
        if bucket.endswith("d"):
            return int(bucket[:-1]) * 86400
        return int(bucket) * 60
    except Exception:
        return 300


@API_app.get("/v1/measurements/aggregate")
def api_measurements_aggregate(
    device_id: str = Query(...),
    sensor: str = Query(...),
    bucket: str = Query("5m"),
    agg: str = Query("avg"),
    fr: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
):
    agg = agg.lower()
    if agg not in ("avg", "min", "max"):
        raise HTTPException(status_code=400, detail="agg must be one of avg|min|max")
    try:
        with connexion_sql.cursor() as cur:
            params: List[Any] = [device_id, sensor]
            where = ["device_id = %s", "sensor = %s"]
            if fr:
                where.append("ts >= CAST(%s AS timestamptz)")
                params.append(fr)
            if to:
                where.append("ts <= CAST(%s AS timestamptz)")
                params.append(to)
            where_sql = " WHERE " + " AND ".join(where)

            if TIMESCALE_AVAILABLE:
                sql = (
                    f"SELECT time_bucket(%s::interval, ts) AS bucket, {agg}(value) AS v "
                    f"FROM measurements {where_sql} "
                    f"GROUP BY bucket ORDER BY bucket ASC LIMIT %s"
                )
                params2 = [bucket] + params + [limit]
                cur.execute(sql, params2)
            else:
                bucket_sec = _parse_bucket_to_seconds(bucket)
                sql = (
                    f"SELECT to_timestamp(floor(extract(epoch from ts)/%s)*%s) AT TIME ZONE 'UTC' AS bucket, {agg}(value) AS v "
                    f"FROM measurements {where_sql} "
                    f"GROUP BY bucket ORDER BY bucket ASC LIMIT %s"
                )
                params2 = [bucket_sec, bucket_sec] + params + [limit]
                cur.execute(sql, params2)

            rows = cur.fetchall()
            return [{"bucket": r[0], "value": r[1]} for r in rows]
    except Exception as e:
        print("Erreur /v1/measurements/aggregate:", e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'agrégation des mesures")