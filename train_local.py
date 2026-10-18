"""Rebuild CampusX's final stacking pipeline using current pickle formats."""
from pathlib import Path
import json
import pickle
import re
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parent

def features(raw):
    df = raw.copy()
    df['Ram'] = df['Ram'].str.replace('GB', '', regex=False).astype(int)
    df['Weight'] = df['Weight'].str.replace('kg', '', regex=False).astype(float)
    df['Touchscreen'] = df['ScreenResolution'].str.contains('Touchscreen').astype(int)
    df['Ips'] = df['ScreenResolution'].str.contains('IPS').astype(int)
    resolution = df['ScreenResolution'].str.extract(r'(\d+)x(\d+)').astype(int)
    df['ppi'] = np.hypot(resolution[0], resolution[1]) / df['Inches']
    def cpu(text):
        name = ' '.join(text.split()[:3])
        if name in ['Intel Core i3', 'Intel Core i5', 'Intel Core i7']:
            return name
        return 'Other Intel Processor' if text.startswith('Intel') else 'AMD Processor'
    df['Cpu brand'] = df['Cpu'].map(cpu)
    def capacity(text, kind):
        total = 0
        for amount, unit, medium in re.findall(r'(\d+(?:\.\d+)?)\s*(GB|TB)\s*(SSD|HDD|Flash Storage|Hybrid)', text):
            if medium == kind:
                total += float(amount) * (1000 if unit == 'TB' else 1)
        return int(total)
    for kind in ['HDD', 'SSD']:
        df[kind] = df['Memory'].map(lambda value: capacity(value, kind))
    df['Gpu brand'] = df['Gpu'].str.split().str[0]
    df = df.loc[df['Gpu brand'] != 'ARM'].copy()
    def os_group(value):
        if value in ['Windows 10', 'Windows 7', 'Windows 10 S']:
            return 'Windows'
        return 'Mac' if value in ['macOS', 'Mac OS X'] else 'Others/No OS/Linux'
    df['os'] = df['OpSys'].map(os_group)
    columns = ['Company', 'TypeName', 'Ram', 'Weight', 'Touchscreen', 'Ips', 'ppi', 'Cpu brand', 'HDD', 'SSD', 'Gpu brand', 'os']
    return df[columns], np.log(df['Price'])

def main():
    X, y = features(pd.read_csv(ROOT / 'laptop_data.csv'))
    train, test, y_train, y_test = train_test_split(X.to_numpy(), y, test_size=0.15, random_state=2)
    # Same final model family and hyperparameters as the source notebook.
    # One CPU thread per learner keeps training usable on ordinary laptops.
    model = Pipeline([
        ('step1', ColumnTransformer([
            ('col_tnf', OneHotEncoder(sparse_output=False, drop='first', handle_unknown='ignore'), [0,1,7,10,11])
        ], remainder='passthrough')),
        ('step2', StackingRegressor(estimators=[
            ('rf', RandomForestRegressor(n_estimators=350, random_state=3, max_samples=0.5, max_features=0.75, max_depth=15, n_jobs=1)),
            ('gbdt', GradientBoostingRegressor(n_estimators=100, max_features=0.5, random_state=3)),
            ('xgb', XGBRegressor(n_estimators=25, learning_rate=0.3, max_depth=5, n_jobs=1, random_state=3))
        ], final_estimator=Ridge(alpha=100), n_jobs=1))
    ])
    print('Training the model from CSV. Please wait...', flush=True)
    model.fit(train, y_train)
    predicted = model.predict(test)
    assert np.isfinite(predicted).all()
    metrics = {'test_rows': len(test), 'r2_log_price': float(r2_score(y_test, predicted)), 'mae_rupees': float(mean_absolute_error(np.exp(y_test), np.exp(predicted)))}
    output = ROOT / 'local_model'
    output.mkdir(exist_ok=True)
    for name, value in [('pipe.pkl', model), ('df.pkl', X)]:
        with (output / name).open('wb') as handle:
            pickle.dump(value, handle)
    (output / 'metrics.json').write_text(json.dumps(metrics, indent=2))
    source = (ROOT / 'app.py').read_text()
    source = source.replace("open('pipe.pkl','rb')", "open('local_model/pipe.pkl','rb')")
    source = source.replace("open('df.pkl','rb')", "open('local_model/df.pkl','rb')")
    if "local_model/pipe.pkl" not in source or "local_model/df.pkl" not in source:
        raise RuntimeError('The upstream app changed; its model paths need review.')
    source = source.replace("st.number_input('Weight of the Laptop')", "st.number_input('Weight of the Laptop (kg)', min_value=0.1, max_value=10.0, value=2.0, step=0.1)")
    source = source.replace('np.array([company,type,ram,weight,touchscreen,ips,ppi,cpu,hdd,ssd,gpu,os])', 'np.array([company,type,ram,weight,touchscreen,ips,ppi,cpu,hdd,ssd,gpu,os], dtype=object)')
    source = source.replace('st.title("Laptop Predictor")', 'st.title("Laptop Predictor")\nst.caption("CampusX learning project. Estimates use the historical dataset, not live shop prices.")')
    (ROOT / 'app_local.py').write_text(source)
    print(json.dumps(metrics, indent=2), flush=True)
    print('Model ready. Original app.py and model files have been preserved.')

if __name__ == '__main__':
    main()
