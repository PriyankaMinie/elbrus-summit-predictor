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
