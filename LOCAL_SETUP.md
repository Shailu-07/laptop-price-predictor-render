# Run the laptop predictor

From the project folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If `.venv` already exists, skip the first command. The pinned dependencies
were verified locally with Python 3.12.10. `RUN_APP.cmd` launches the same app.

The app uses `local_model/`, reused from the `feature/laptop-predict` branch
and trained with scikit-learn 1.5.2. The original root `pipe.pkl` was saved
with scikit-learn 0.24.1 and is not used by this app.

To test startup, the screen-size label, and predictions:

```powershell
.\.venv\Scripts\python.exe -m unittest test_app.py
```

To rebuild the model from the included historical dataset:

```powershell
.\.venv\Scripts\python.exe train_local.py
```

Rebuilding replaces the files in `local_model/`. Its recorded held-out
mean absolute error is approximately 9,287 rupees; estimates are not current
retail quotes. Loading and prediction checks do not establish model accuracy.
