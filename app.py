from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

model = joblib.load('timeseries_xgb_model.pkl')
feature_cols = joblib.load('timeseries_feature_cols.pkl')
store_latest_features = joblib.load('store_latest_features.pkl')
state_holiday_mapping = joblib.load('state_holiday_mapping.pkl')

HTML_FORM = """
<!DOCTYPE html>
<html>
<head><title>Sales Forecast Demo</title></head>
<body style="font-family: Arial; max-width: 500px; margin: 50px auto;">
<h2>Retail Sales Forecasting Demo</h2>
<form method="POST" action="/">
    <label>Store ID (1-1115):</label><br>
    <input type="number" name="store_id" value="{store_id}" required><br><br>
    <label>Date:</label><br>
    <input type="date" name="date" value="{date}" required><br><br>
    <label>Promo running?</label><br>
    <select name="promo">
        <option value="1" {promo_1}>Yes</option>
        <option value="0" {promo_0}>No</option>
    </select><br><br>
    <label>State Holiday:</label><br>
    <select name="state_holiday">
        <option value="0" {sh_0}>None</option>
        <option value="a" {sh_a}>Public holiday</option>
        <option value="b" {sh_b}>Easter</option>
        <option value="c" {sh_c}>Christmas</option>
    </select><br><br>
    <label>School Holiday?</label><br>
    <select name="school_holiday">
        <option value="0" {sch_0}>No</option>
        <option value="1" {sch_1}>Yes</option>
    </select><br><br>
    <button type="submit">Predict Sales</button>
</form>
{result}
</body>
</html>
"""

def make_prediction(store_id, date_str, promo, state_holiday, school_holiday):
    date = pd.to_datetime(date_str)
    store_row = store_latest_features[store_latest_features['Store'] == store_id]
    if store_row.empty:
        return None
    store_row = store_row.iloc[0]

    day_of_week = date.dayofweek + 1
    is_weekend = 1 if day_of_week >= 6 else 0
    state_holiday_encoded = state_holiday_mapping.get(state_holiday, 0)

    input_row = {
        'Store': store_id,
        'DayOfWeek': day_of_week,
        'Promo': promo,
        'StateHoliday': state_holiday_encoded,
        'SchoolHoliday': school_holiday,
        'StoreType': store_row['StoreType'],
        'Assortment': store_row['Assortment'],
        'CompetitionDistance': store_row['CompetitionDistance'],
        'Month': date.month,
        'Day': date.day,
        'WeekOfYear': date.isocalendar().week,
        'IsWeekend': is_weekend,
        'lag_1': store_row['lag_1'],
        'lag_7': store_row['lag_7'],
        'lag_14': store_row['lag_14'],
        'rolling_mean_7': store_row['rolling_mean_7'],
        'rolling_std_7': store_row['rolling_std_7']
    }

    X_input = pd.DataFrame([input_row])[feature_cols]
    return round(float(model.predict(X_input)[0]), 2)

@app.route('/', methods=['GET', 'POST'])
def home():
    result_html = ""
    store_id_val = "769"
    date_val = "2015-08-15"
    promo_val = "1"
    sh_val = "0"
    sch_val = "0"

    if request.method == 'POST':
        store_id_val = request.form['store_id']
        date_val = request.form['date']
        promo_val = request.form['promo']
        sh_val = request.form['state_holiday']
        sch_val = request.form['school_holiday']

        prediction = make_prediction(int(store_id_val), date_val, int(promo_val), sh_val, int(sch_val))
        if prediction is None:
            result_html = f"<h3 style='color:red'>Store {store_id_val} not found (valid range: 1-1115)</h3>"
        else:
            result_html = f"<h3 style='color:green'>Predicted Sales: {prediction}</h3>"

    return HTML_FORM.format(
        store_id=store_id_val,
        date=date_val,
        promo_1="selected" if promo_val == "1" else "",
        promo_0="selected" if promo_val == "0" else "",
        sh_0="selected" if sh_val == "0" else "",
        sh_a="selected" if sh_val == "a" else "",
        sh_b="selected" if sh_val == "b" else "",
        sh_c="selected" if sh_val == "c" else "",
        sch_0="selected" if sch_val == "0" else "",
        sch_1="selected" if sch_val == "1" else "",
        result=result_html
    )

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    prediction = make_prediction(
        int(data['store_id']),
        data['date'],
        int(data['promo']),
        str(data.get('state_holiday', '0')),
        int(data.get('school_holiday', 0))
    )
    if prediction is None:
        return jsonify({'error': f"Store {data['store_id']} not found"}), 404
    return jsonify({
        'store_id': int(data['store_id']),
        'date': str(data['date']),
        'predicted_sales': prediction
    })

if __name__ == '__main__':
    app.run(debug=True)