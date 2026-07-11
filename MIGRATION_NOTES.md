\# Migration Notes — V2 Cloud Deployment



\## Airflow DAG → GitHub Actions (Open-Meteo daily fetch)



\*\*Why:\*\* Airflow requires its own scheduler/webserver running continuously somewhere. For a single daily fetch-and-store job, running a full Airflow deployment (Cloud Composer, MWAA, or a self-hosted VM) is heavy machinery for a simple task. GitHub Actions provides free, serverless, scheduled execution with no infrastructure to manage.



\*\*What changed:\*\* `dags/openmeteo\_pipeline.py` (Airflow DAG) was converted into `fetch\_openmeteo\_daily.py` (plain Python script), triggered by `.github/workflows/daily\_openmeteo\_fetch.yml` on a cron schedule.



\*\*The core logic — the Open-Meteo API call, the `psycopg2` connection, and the `INSERT ... ON CONFLICT` SQL — is byte-for-byte unchanged.\*\* Only Airflow's orchestration wrapper was removed:



| Removed | Why |

|---|---|

| `from airflow import DAG`, `from airflow.operators.python import PythonOperator` | No longer using Airflow — GitHub Actions handles scheduling instead |

| `default\_args` and the `with DAG(...) as dag:` block | Schedule (`0 15 \* \* \*`) moved into the GitHub Actions YAML `cron:` field instead |

| `PythonOperator` task definitions and `fetch\_task >> store\_task` | Task-dependency syntax replaced by plain sequential function calls |

| `ti` (TaskInstance) parameter, `ti.xcom\_push()` / `ti.xcom\_pull()` | Airflow's mechanism for passing data between isolated tasks. Since both steps now run as regular Python functions in the same script, the return value is passed directly instead |



\*\*What replaced it:\*\*

```python

def fetch\_openmeteo():

&#x20;   ...

&#x20;   return data



def store\_to\_postgres(data):

&#x20;   ...



if \_\_name\_\_ == "\_\_main\_\_":

&#x20;   weather\_data = fetch\_openmeteo()

&#x20;   store\_to\_postgres(weather\_data)

```



\*\*Credentials:\*\* Local runs still use `.env` (via `python-dotenv`). GitHub Actions runs use GitHub Secrets (`Settings → Secrets and variables → Actions`), injected as environment variables at workflow runtime — `os.getenv()` calls in the script work identically either way, just fed from a different source depending on where the script executes.



\*\*Why both files still exist in the repo:\*\* `dags/openmeteo\_pipeline.py` is kept for reference / local Airflow use (V1). `fetch\_openmeteo\_daily.py` is the cloud-scheduled version (V2). They are functionally equivalent — same data, same destination table, same conflict handling.


## No hosted Airflow instance exists

Important to note for future reference: this project does **not** have Airflow running anywhere in the cloud. Airflow only exists in one place — locally, via WSL (`airflow api-server`, `airflow scheduler`, `airflow dag-processor`), viewable at `http://localhost:8080` only when those services are manually started.

The original roadmap considered deploying real Airflow to the cloud (Google Cloud Composer or AWS MWAA), but that was deliberately skipped in favor of GitHub Actions — a full managed Airflow deployment is heavy, often paid infrastructure for what is just one daily fetch task.

GitHub Actions is **not** Airflow and does not have a DAG graph view. It shows a simpler linear step-by-step log (Checkout repo → Set up Python → Install dependencies → Run fetch script), visible under the repo's **Actions** tab. There is no "Airflow website" or hosted DAG graph for this project — only the local Airflow UI (when manually started) or the GitHub Actions run log (for the cloud-scheduled version).
## FastAPI deployment to Render — lessons learned

**Problem 1 — bloated `requirements.txt`:** the root `requirements.txt` was generated via `pip freeze` against the full local dev environment, which includes `apache-airflow` and its ~150 sub-dependencies. Render's build failed trying to resolve packages like `backports.strenum` that aren't needed by the API at all. `app.py` only imports `fastapi`, `pydantic`, `joblib`, and `numpy` (with `xgboost`/`scikit-learn` needed indirectly to unpickle the trained model). **Fix:** created a separate, minimal `requirements-api.txt` containing only what the API service actually needs, and pointed Render's Build Command at that file instead.

**Problem 2 — wrong Python version:** Render defaulted to Python 3.14, but the project (and pinned package versions like `numpy==1.24.1`) targets Python 3.10. A `runtime.txt` file (the Heroku convention) had no effect on Render. **Fix:** Render uses an environment variable instead — set `PYTHON_VERSION=3.10.11` under the service's Environment tab.

**Problem 3 — missing model file:** `elbrus_model.pkl` was excluded via `.gitignore` (`*.pkl`), which is good practice for large binaries, but this model is only ~44KB, so it was removed from `.gitignore` and committed directly so Render (which only has access to what's in the GitHub repo) could load it at runtime.

**Takeaway for future deployments (e.g. Streamlit to Streamlit Community Cloud):** always use a service-specific, minimal `requirements.txt` rather than the full local dev environment's `pip freeze` output, and check whether the target platform needs a Python version pinned via an environment variable rather than `runtime.txt`.