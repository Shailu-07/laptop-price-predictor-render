# Your laptop predictor: Docker explained step by step

Prepared on 18 October 2026.

## 1. What we achieved

Your laptop price predictor now runs inside a Docker container on your computer.

Open **http://localhost:8501** in your browser.

I checked your existing Dockerfile, built an image from it, started a container, and tested the application's prediction button. The test returned a predicted price of **35610** for the default inputs. The health endpoint returned **ok**.

At the time I prepared this guide, the container was running.

**I did not change your project's Dockerfile, .dockerignore, Python code, trained models, or requirements during this check.** Those files already existed and worked together. This guide is the new documentation I added afterward.

## 2. What Docker means in simple terms

Your app needs Python, Streamlit, machine-learning libraries, and saved model files. If another computer has different versions or missing libraries, the app might fail.

Docker packages an application and its dependencies into a repeatable environment.

| Term | Meaning in your project |
| --- | --- |
| Docker Desktop | The Windows application that manages Docker's Linux environment and containers. |
| Dockerfile | The recipe describing how to package your app. |
| Image | The packaged app and dependencies created from that recipe. Yours is `laptop-price-predictor:local`. |
| Container | An instance created from an image. Yours is named `laptop-price-predictor`. It can be running or stopped. |
| Build | Follow the Dockerfile to create an image. |
| Port | A numbered network endpoint. Streamlit uses port `8501` here. |
| Build context | The project files Docker is allowed to use during a build, filtered by `.dockerignore`. |

The sequence is:

**Project files + Dockerfile → docker build → image → docker run → container → browser**

Docker runs the app; it does not retrain your model or improve prediction accuracy.

## 3. Which project and files I used

Your project folder is:

```text
D:\Projects\laptop-price-predictor
```

These are the important files:

```text
laptop-price-predictor/
├── Dockerfile
├── .dockerignore
├── requirements-local.txt
├── app_local.py
└── local_model/
    ├── pipe.pkl
    ├── df.pkl
    └── metrics.json
```

- `app_local.py`: the Streamlit application actually launched by Docker.
- `requirements-local.txt`: the dependency versions installed inside the image.
- `local_model/pipe.pkl`: the saved prediction pipeline.
- `local_model/df.pkl`: the saved data used by the app, including dropdown choices.
- `metrics.json`: model metrics, copied with the folder but not needed by the app's startup code.

**Important: the `app.py` tab open in your editor is not the file this container runs.** For this Docker setup, edit `app_local.py`. The older root-level `pipe.pkl` and `df.pkl` are also not used by the container.

## 4. Exactly what I did

### Step 1: Located your actual VS Code project

This chat initially pointed to a different workspace containing IntelliRAG. I located the laptop predictor folder and confirmed the open VS Code window matched it. The two projects are separate.

### Step 2: Read the configuration and application

I checked the Dockerfile, `.dockerignore`, both requirements files, `app.py`, `app_local.py`, and the model folder. I confirmed that the files referenced by the Dockerfile existed.

### Step 3: Checked Docker

I checked the Docker server and existing containers. The Docker server responded with version `29.8.2`, so it was ready to build.

In our earlier, separate troubleshooting task, I had restarted Docker Desktop to clear its stuck startup. No Windows feature change was needed then. The IntelliRAG changes from that earlier task do not apply to this laptop project.

### Step 4: Built your image

From the laptop project folder, I ran the equivalent of:

```powershell
docker build -t laptop-price-predictor:local .
```

- `docker build`: creates an image using the Dockerfile.
- `-t laptop-price-predictor:local`: gives it a name and a tag. `local` is just the tag we chose.
- `.`: uses the current folder as the build context. The final dot matters.

Docker downloaded the Python base image, installed system and Python dependencies, copied your app and model files, and saved the resulting image. I also verified that the image existed afterward.

The first build took time because it downloaded large dependencies. In particular, the pinned XGBoost package also downloaded an NVIDIA NCCL library. This did not mean your application required a GPU; I retained the existing dependencies while validating your saved model.

I saved the build output at:

```text
C:\Users\asus1\OneDrive\Documents\New project\tmp\laptop-docker-build.log
```

### Step 5: Started the container

I ran:

```powershell
docker run -d --name laptop-price-predictor -p 127.0.0.1:8501:8501 laptop-price-predictor:local
```

- `run`: creates and starts a new container.
- `-d`: runs it in the background.
- `--name`: assigns the container a convenient name.
- `-p 127.0.0.1:8501:8501`: connects port 8501 on your computer's localhost address to port 8501 inside the container.
- The final argument identifies the image to use.

This makes the app available locally at **http://localhost:8501**. I did not publish it to the internet.

### Step 6: Tested the app inside the container

Using Streamlit's `AppTest` tool, I loaded `/app/app_local.py`, checked for application exceptions, clicked the first button (`Predict Price`), and checked that a prediction appeared without an exception.

Result: **The predicted price of this configuration is 35610**.

I also requested:

```text
http://localhost:8501/_stcore/health
```

Result: **ok**.

This verifies that the server responds and that the app can load its model and make one prediction. It is not a model-accuracy evaluation or a test of every input combination.

## 5. Your Dockerfile explained

### Choose the starting environment

```dockerfile
FROM python:3.10-slim
```

Start with a small Linux image containing Python 3.10. Your container uses this Python, not your Windows `.venv`.

### Set the working folder inside the container

```dockerfile
WORKDIR /app
```

Following commands run from `/app`. This is a folder inside the container, not your Windows project path.

### Set Python options

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
```

The first option prevents Python from writing bytecode cache files. The second makes Python log output appear promptly.

### Install a system library

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
```

`libgomp1` provides the GNU OpenMP runtime used by native numerical libraries. The final command removes package-list files from the image after installation. It runs inside the image build, not against your Windows files.

### Install Python dependencies

```dockerfile
COPY requirements-local.txt .
RUN pip install --no-cache-dir -r requirements-local.txt
```

Your pinned dependencies are:

```text
numpy==1.26.4
pandas==2.2.3
scikit-learn==1.5.2
xgboost==2.1.4
streamlit==1.41.1
```

Version compatibility matters for saved machine-learning models. Keep this requirements file paired with the local model files that were tested.

Copying requirements before application code lets Docker reuse the dependency installation layer when only application code changes.

### Create an unprivileged user and copy the application

```dockerfile
RUN useradd --create-home --shell /usr/sbin/nologin appuser
COPY --chown=appuser:appuser app_local.py .
COPY --chown=appuser:appuser local_model/ ./local_model/
USER appuser
```

These lines create `appuser`, copy your app and saved models with that ownership, and run the application as that user instead of Linux's administrator (`root`).

### Document the application's port

```dockerfile
EXPOSE 8501
```

This declares the intended container port. It does not publish the port on your computer by itself. The `-p` option in `docker run` does that.

### Start Streamlit when the container starts

```dockerfile
CMD ["streamlit", "run", "app_local.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false"]
```

- Runs `app_local.py` with Streamlit.
- `0.0.0.0` lets Streamlit accept connections through the container's network interface.
- Uses port `8501`.
- Headless mode avoids trying to open a browser inside the container.
- Disables Streamlit usage statistics.

`RUN` commands execute while building the image. `CMD` specifies what starts when you run a container from that image.

## 6. What .dockerignore does

This file excludes unnecessary files from the build context. It does not delete them from your computer.

Your file excludes:

- `.git`, `.vscode`, and `.campusx-local-setup`: local repository/editor/setup information.
- `.venv`: Windows dependencies, which must not replace the Linux dependencies installed in the image.
- Python caches and notebooks: unnecessary for running this saved-model app.
- `laptop_data.csv` and `train_local.py`: training inputs/code, not needed for inference here.
- `/pipe.pkl` and `/df.pkl`: the older models at the project root.

The leading `/` in those last two patterns limits them to the context root. **The models inside `local_model/` remain available to copy.**

## 7. Commands you can use now

Open a PowerShell terminal in VS Code. For build commands, first enter the project folder:

```powershell
cd D:\Projects\laptop-price-predictor
```

### See running containers

```powershell
docker ps
```

See running and stopped containers:

```powershell
docker ps -a
```

### Stop your app

```powershell
docker stop laptop-price-predictor
```

### Start the existing container again

```powershell
docker start laptop-price-predictor
```

Then visit http://localhost:8501. Make sure Docker Desktop is running first.

### See application logs

```powershell
docker logs --tail 50 laptop-price-predictor
```

Follow new logs as they arrive:

```powershell
docker logs -f laptop-price-predictor
```

Press Ctrl+C to stop following logs. This does not stop the background container.

### Check the server's health

```powershell
Invoke-RestMethod http://localhost:8501/_stcore/health
```

Expected response: `ok`.

## 8. What to do after changing your code

This setup copies code into the image. It does not mount your project folder into the container. Saving a local file therefore does not update the running app automatically.

After editing `app_local.py`, rebuild first:

```powershell
cd D:\Projects\laptop-price-predictor
docker build -t laptop-price-predictor:local .
```

**Only after the build succeeds**, replace the old container:

```powershell
docker stop laptop-price-predictor
docker rm laptop-price-predictor
docker run -d --name laptop-price-predictor -p 127.0.0.1:8501:8501 laptop-price-predictor:local
```

`docker rm` deletes the stopped container and any changes stored only inside it. It does not delete your Windows project files or the image. This app currently reads its bundled models and has no configured persistent data volume.

Simply restarting the old container does not switch it to the newly built image; you must recreate it.

## 9. Common beginner problems

| Message or symptom | What to check |
| --- | --- |
| Cannot connect to Docker daemon | Open Docker Desktop, wait for the engine, then run `docker version`. |
| Dockerfile not found | Run the build from `D:\Projects\laptop-price-predictor` and include the final `.`. |
| Container name already in use | The container already exists. Use `docker start laptop-price-predictor`, or follow the rebuild/recreate steps above. |
| Port 8501 is already allocated | Check `docker ps`. Another app may be using the port. For a new container, you can map `127.0.0.1:8502:8501` and open localhost:8502 instead. |
| Changes to app.py do not show | This Dockerfile launches `app_local.py`. Edit that file and rebuild/recreate. |
| Model file not found | Ensure `local_model/pipe.pkl` and `local_model/df.pkl` exist and are not excluded by `.dockerignore`. |
| First build is slow | Large dependency downloads and image export take time. Later builds can reuse cached layers. |
| Browser cannot connect | Check `docker ps` and `docker logs`; the container may be stopped or still starting. |

## 10. What was not done

- No cloud deployment or Docker Hub upload.
- No model retraining or accuracy improvement.
- No changes to the project's existing source/configuration during validation.
- No automatic startup policy configured for this container; use `docker start` when needed.
- No exhaustive input testing or production security review.

You have achieved a **working local Docker deployment**: the application, dependencies, and saved model are packaged into an image, and a running container serves the app on your computer.

Official reference: [Streamlit's Docker tutorial](https://docs.streamlit.io/deploy/tutorials/docker).

---

## 11. Deploy this project on Render: beginner walkthrough

Instructions checked against Render documentation on 18 October 2026. Dashboard labels can change.

**Status: the application has been tested locally in Docker. These are instructions for you to deploy it; I have not uploaded your project or created a Render service.**

### A. What deployment means

Right now, your Docker container runs on your laptop. `localhost` means the computer of the person opening the link, so sending someone your localhost link will not open your app on their computer.

Deployment puts the app on a remote computer managed by a hosting provider. In this guide, GitHub stores your project files and Render runs them:

```text
Your project folder
        |
        | Upload the required files
        v
Your GitHub repository
        |
        | Render reads the Dockerfile and builds an image
        v
Render runs a container
        |
        v
Visitors open your public HTTPS website
```

Visitors only need a browser. Your laptop does not need to stay on once deployment succeeds. Render builds its own image from GitHub; it does not copy the container currently running on your laptop. You do not need Docker Hub or a `.tar` export for this approach. [Render Docker documentation](https://render.com/docs/docker)

### B. Prepare your own GitHub repository

I checked the local project: its `origin` remote points to:

```text
https://github.com/campusx-official/laptop-price-predictor-regression-project.git
```

That is the original CampusX repository. Your local Dockerfile, `app_local.py`, and `local_model` files were untracked when checked, meaning they had not been committed to Git. Connecting Render directly to the original repository would not include these local additions.

For this first deployment, use the GitHub website to create your own repository and upload only the deployment files:

1. Sign in at https://github.com.
2. Create a new repository named `laptop-price-predictor-render` under your own account.
3. Choose Private if you want the source to remain private. Render can access a private repository when you grant it access. The deployed web app will still be public.
4. Initialize the repository with a README so it is easy to navigate. In the README, credit the original CampusX project and describe your local adaptation.
5. Open the new repository and choose **Add file → Upload files**.
6. From `D:\Projects\laptop-price-predictor`, upload the following four files and the complete `local_model` folder. Upload the files themselves at the repository root, not an outer project folder.

```text
Dockerfile
.dockerignore
requirements-local.txt
app_local.py
local_model/
    pipe.pkl
    df.pkl
    metrics.json
```

7. Commit the upload with a message such as `Add Docker laptop predictor app`.
8. Inspect the repository in your browser. Confirm that the filename is exactly `Dockerfile`, and that `local_model/pipe.pkl` and `local_model/df.pkl` appear inside the folder.

Your model file is currently about 19 MB. Upload the actual binary file, not a text file containing its path. Preserve any applicable license and attribution files when sharing the project.

Do not upload `.venv`, `.git`, `.vscode`, Python caches, secrets, or a Docker image archive. The training CSV and notebook are optional source materials, not runtime requirements for this deployment.

**`.dockerignore` and `.gitignore` are different:** the first filters Docker build inputs; the second filters what Git offers to track. Your existing `.gitignore` only contains `venv`, so it does not exclude your `.venv` folder. The selective upload above avoids accidentally uploading it. Do not use `git add .` blindly in the existing folder.

Uploading through the browser does not change the existing local Git remote. Keep using this upload workflow for now, or later clone your new repository into a separate folder before adopting a Git push workflow.

### C. Connect Render

1. Sign in at https://dashboard.render.com.
2. Choose **New → Web Service**.
3. Choose **Git Provider**, connect GitHub, and grant access to your new repository.
4. Select **your-account/laptop-price-predictor-render**.

Use a Web Service because this app executes Python to generate predictions. [Render web service setup](https://render.com/docs/web-services)

### D. Enter these settings

These values are tailored to your current files:

| Setting | Value |
| --- | --- |
| Name | `laptop-price-predictor` or another available name |
| Region | Choose an available region near your users |
| Branch | The branch containing your uploaded files, usually `main` |
| Language / Runtime | **Docker** |
| Root Directory | Leave empty because the Dockerfile is at the repository root |
| Dockerfile Path | `./Dockerfile` |
| Docker Build Context, if shown | `.` |
| Docker Command | Leave empty to use the Dockerfile's `CMD` |
| Health Check Path | `/_stcore/health` |
| Environment variable | Key: `PORT`, value: `8501` |

Docker supplies the build steps and startup command. Do not enter a separate `pip install -r requirements.txt` command: your Dockerfile deliberately installs `requirements-local.txt`. [Docker runtime settings](https://render.com/docs/docker)

### E. Understand the port setting

Your Dockerfile starts Streamlit on `0.0.0.0:8501`. Set Render's `PORT` variable to `8501` to match it. Render's default is `10000`, but it supports overriding that value. No Dockerfile change is needed for the settings in this guide. [Render port configuration](https://render.com/docs/web-services#port-binding)

The `PORT` variable does not rewrite your Dockerfile: its startup command still explicitly selects 8501. Keep the two settings consistent.

Locally you used `docker run -p ...`. On Render, the platform handles public routing. Visitors use the HTTPS URL shown in the dashboard without adding `:8501`.

The app does not currently require an API key or a database. It loads its saved model from the image.

### F. Choose a compute plan

For a learning experiment, you can try Free if offered. Free currently provides **512 MB RAM and 0.1 CPU**. I have not verified that your model and dependencies fit within that limit under real usage. Image size and runtime memory are different measurements. [Render compute plans](https://render.com/docs/compute-plans)

If the app fails with an out-of-memory message, inspect the logs and metrics. You may need to reduce memory use or select a plan with more RAM. Check the price before choosing a paid plan. Selecting a paid 512 MB plan would not increase the memory limit.

Free services sleep after 15 minutes without incoming traffic. A later visit wakes them, which can take about a minute. Free usage also has monthly limits. Files written during runtime are temporary; they can disappear on restart or redeploy. Your bundled models remain available because they are part of the image. [Free service limitations](https://render.com/docs/free)

### G. Deploy and watch the logs

After reviewing the settings, click **Create Web Service / Deploy**. Follow the build and deployment output in the dashboard. [Render deployment walkthrough](https://render.com/docs/your-first-deploy)

For this project, expect Docker to:

1. Download the Python base image.
2. Install `libgomp1`.
3. Install the packages from `requirements-local.txt`.
4. Copy `app_local.py` and `local_model`.
5. Save the image and start Streamlit.

The large XGBoost and NVIDIA dependency downloads made your first local build slow. A first cloud build can also take time; inspect the latest log lines rather than assuming it has failed.

### H. Test your public website

When Render reports the deployment is live, open the URL displayed in the dashboard. It will resemble:

```text
https://your-service-name.onrender.com
```

This is an example, not a URL that I created.

Check all of these:

1. The Laptop Predictor page loads.
2. The brand, CPU, and other dropdowns appear.
3. Clicking **Predict Price** displays a number.
4. Changing RAM or storage and predicting again works.
5. Opening the URL on a phone using mobile data works.
6. The health URL, formed by adding `/_stcore/health`, returns `ok`.

A successful health check only confirms that the Streamlit server is responding. Test the prediction button too: model-loading errors can appear when the app script runs for a visitor.

Only after these checks should you treat the cloud deployment as verified. A successful local test alone cannot prove that Render has enough resources.

### I. Update the deployed app later

For the browser-upload workflow:

1. Edit `app_local.py` on your computer.
2. Test locally using the rebuild steps in section 8.
3. Upload the changed file to the same path in your GitHub repository and commit it.
4. Check your Render service's auto-deploy setting. If enabled for that branch, a push triggers a deployment; otherwise use the dashboard's manual deploy action.
5. Read the logs and repeat the prediction test on the public URL.

Render deploys from the linked repository branch, so saving a file only on your laptop is not enough. [Render deployment behavior](https://render.com/docs/deploys)

Remember: this Dockerfile runs `app_local.py`, so editing only `app.py` will not change the deployed app.

### J. Troubleshooting for this project

| Problem | What to check |
| --- | --- |
| Dockerfile or requirements-local.txt not found | Check the GitHub upload and repository root. Confirm the Dockerfile path is `./Dockerfile`. |
| COPY local_model fails | The model folder may exist only on your laptop. Confirm both `.pkl` files are actually in GitHub. |
| Error installing sklearn | Check that Runtime is Docker and the build uses `requirements-local.txt`. The older requirements.txt is not the file we tested. |
| No open port detected | Check for an earlier startup error, verify `PORT=8501`, and keep the existing `0.0.0.0` bind address. |
| App starts but prediction fails | Read the Python traceback. Keep the tested local model files and pinned dependency versions together. |
| Process killed / out of memory | Check runtime memory metrics; 512 MB may be insufficient. A larger image alone does not tell you the RAM requirement. |
| First visit is slow after inactivity | This can be normal Free-plan wake-up behavior. |
| Changes do not appear | Check the selected repository and branch, uploaded file, latest deployment, and whether you edited app_local.py. |

### K. What you will have achieved

After you complete and verify these steps, you will have a public laptop-price predictor running in a Docker container on Render. People can use it from a browser without installing Docker or Python, and without your laptop staying on.

**What I completed for this request:** checked the current Render documentation, inspected your Git setup and Dockerfile, and added this tailored guide. **What remains:** you must upload the files to your own GitHub repository, connect Render, select a plan, deploy, and test the public URL. No cloud service has been created or billed by me.
