from pathlib import Path
import pandas as pd
import sqlalchemy
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[2]  # ajustar conforme layout

@lru_cache(maxsize=4)
def get_engine(database_url: str):
    try:
        engine = sqlalchemy.create_engine(database_url)
        # quick smoke test
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        return engine
    except Exception:
        return None

def fetch_metrics(database_url: str = None):
    """
    Retorna dict com sensor count, umidade média, alerts pendentes e últimas leituras.
    Usa DB se disponível, senão CSV fallback.
    """
    result = {
        "sensors_active": 0,
        "umidade_media": None,
        "alerts_pending": 0,
        "latest_readings": pd.DataFrame()
    }
    # DB path
    engine = get_engine(database_url) if database_url else None
    if engine:
        try:
            q_active = """
            SELECT sensor_id, MAX(ts) as last_ts
            FROM sensors
            GROUP BY sensor_id
            HAVING MAX(ts) >= (now() - interval '15 minutes')
            """
            df_active = pd.read_sql_query(sqlalchemy.text(q_active), con=engine)
            result["sensors_active"] = int(df_active.shape[0])
        except Exception:
            result["sensors_active"] = 0

        try:
            q_um = "SELECT umidade FROM sensors WHERE umidade IS NOT NULL ORDER BY ts DESC LIMIT 100"
            df_um = pd.read_sql_query(sqlalchemy.text(q_um), con=engine)
            if not df_um.empty:
                result["umidade_media"] = round(float(df_um['umidade'].mean()), 2)
        except Exception:
            result["umidade_media"] = None

        try:
            q_alerts = "SELECT COUNT(*) as pending FROM alerts WHERE resolved = false"
            df_alerts = pd.read_sql_query(sqlalchemy.text(q_alerts), con=engine)
            result["alerts_pending"] = int(df_alerts['pending'].iloc[0]) if not df_alerts.empty else 0
        except Exception:
            result["alerts_pending"] = 0

        try:
            q_latest = "SELECT sensor_id, umidade, nutriente, ts FROM sensors ORDER BY ts DESC LIMIT 20"
            df_latest = pd.read_sql_query(sqlalchemy.text(q_latest), con=engine)
            result["latest_readings"] = df_latest
        except Exception:
            result["latest_readings"] = pd.DataFrame()
    else:
        # CSV fallback (same logic que já discutimos)
        csv_candidates = [
            ROOT / "db" / "data_samples" / "sensors.csv",
            ROOT / "db" / "sensors.csv",
            ROOT / "db" / "sensors_data.csv",
        ]
        df = None
        for c in csv_candidates:
            if c.exists():
                try:
                    df = pd.read_csv(c)
                    break
                except Exception:
                    df = None
        if df is None:
            return result
        if 'ts' in df.columns:
            df['ts'] = pd.to_datetime(df['ts'], errors='coerce')
        try:
            now = pd.Timestamp.now()
            last_per_sensor = df.sort_values('ts').groupby('sensor_id').last().reset_index()
            recent = last_per_sensor[last_per_sensor['ts'] >= (now - pd.Timedelta(minutes=15))]
            result['sensors_active'] = int(recent.shape[0])
        except Exception:
            result['sensors_active'] = int(df['sensor_id'].nunique()) if 'sensor_id' in df.columns else 0
        if 'umidade' in df.columns:
            try:
                result['umidade_media'] = round(float(df['umidade'].dropna().astype(float).tail(100).mean()), 2)
            except Exception:
                result['umidade_media'] = None
        try:
            if 'ts' in df.columns:
                result['latest_readings'] = df.sort_values('ts', ascending=False).head(20)
            else:
                result['latest_readings'] = df.head(20)
        except Exception:
            result['latest_readings'] = df.head(20)
    return result
