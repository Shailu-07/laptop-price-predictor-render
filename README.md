# Laptop Price Predictor

A Streamlit learning project that estimates laptop prices from brand, processor, memory, storage, display, and other specifications. Adapted from [CampusX's laptop price predictor](https://github.com/campusx-official/laptop-price-predictor-regression-project) with a locally rebuilt model, pinned dependencies, and a Docker setup.

Predictions reflect the historical training dataset, not current shop prices.

## Run with Docker

Install and start Docker Desktop, then run:

```bash
git clone --branch feature/laptop-predict https://github.com/Shailu-07/laptop-price-predictor-render.git
cd laptop-price-predictor-render
docker build -t laptop-price-predictor:local .
docker run -d --name laptop-price-predictor -p 127.0.0.1:8501:8501 laptop-price-predictor:local
```

Open [localhost:8501](http://localhost:8501), select specifications, and click **Predict Price**. The first build downloads large machine-learning dependencies.

```bash
docker logs -f laptop-price-predictor
docker stop laptop-price-predictor
docker start laptop-price-predictor
```

The `run` command creates a new container; use `start` for an existing stopped container.

## Run without Docker

Use Python 3.10. In Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-local.txt
.\.venv\Scripts\python.exe -m streamlit run app_local.py
```

## Project files

| File | Purpose |
| --- | --- |
| `app_local.py` | App launched by Docker; reads the rebuilt local models |
| `local_model/pipe.pkl` | Trained prediction pipeline |
| `local_model/df.pkl` | Feature data used for the app's choices |
| `local_model/metrics.json` | Recorded evaluation results |
| `requirements-local.txt` | Pinned runtime dependencies |
| `Dockerfile` | Python 3.10 image, system dependencies, non-root user, Streamlit startup |
| `.dockerignore` | Excludes local environments and unnecessary build inputs |
| `train_local.py` | Rebuilds models from the CSV and regenerates app_local.py |
| `DOCKER_BEGINNER_GUIDE.md` | Detailed Docker explanation and Render walkthrough |

The original `app.py`, root-level models, notebook, and `requirements.txt` remain as source project material. The Docker build uses **app_local.py**, **local_model/**, and **requirements-local.txt**.

## Deploy on Render

Local Docker execution has been verified. A Render deployment has not yet been verified.

Create a Render **Web Service**, connect this GitHub repository, and use:

| Setting | Value |
| --- | --- |
| Branch | `feature/laptop-predict` initially; select `main` after merging the changes there |
| Runtime | Docker |
| Root Directory | Empty |
| Dockerfile Path | `./Dockerfile` |
| Docker Command | Empty; use the Dockerfile CMD |
| Environment variable | `PORT=8501` |
| Health Check Path | `/_stcore/health` |

The current app needs no API keys or database. Select a compute plan after reviewing available memory and pricing; fitting within the free plan has not been verified. After deployment, test both the page and a prediction. See the [beginner guide](DOCKER_BEGINNER_GUIDE.md#11-deploy-this-project-on-render-beginner-walkthrough) and [Render Docker documentation](https://render.com/docs/docker).

## Updating the local container

After editing app_local.py, build a replacement image:

```bash
docker build -t laptop-price-predictor:local .
```

After a successful build:

```bash
docker stop laptop-price-predictor
docker rm laptop-price-predictor
docker run -d --name laptop-price-predictor -p 127.0.0.1:8501:8501 laptop-price-predictor:local
```

Removing the container deletes changes made only inside it, not your project files. Local edits are not automatically copied into an existing container.

## Model and validation

The pipeline uses categorical encoding and a stacking ensemble of Random Forest, Gradient Boosting, and XGBoost with a Ridge final estimator. It predicts log price, then converts the result back to the price scale.

Recorded metrics from `local_model/metrics.json`:

- Test rows: 196
- R² on log price: approximately 0.879
- Mean absolute error in rupees: approximately 9,287

These recorded metrics were not recomputed during Docker validation. Local checks confirmed image creation, Streamlit health, and one default prediction through Streamlit AppTest. This is not exhaustive testing or a guarantee of prediction accuracy.

To retrain in the local Python environment:

```powershell
.\.venv\Scripts\python.exe train_local.py
```

This overwrites the files in `local_model/` and regenerates `app_local.py`; save any custom edits first. Only load pickle models from trusted sources.

## Branch workflow

```text
feature/laptop-predict -> pull request into dev -> pull request into main
```

Each branch should track its corresponding GitHub branch. Changes reach the next branch through reviewed merges, not through upstream tracking settings.

## Attribution

Original learning project: [CampusX](https://github.com/campusx-official/laptop-price-predictor-regression-project). This repository preserves the original project material and adds the local Docker deployment setup and documentation.
