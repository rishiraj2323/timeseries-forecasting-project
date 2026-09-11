from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

model = joblib.load('timeseries_xgb_model.pkl')
feature_cols = joblib.load('timeseries_feature_cols.pkl')
store_latest_features = joblib.load('store_latest_features.pkl')
state_holiday_mapping = joblib.load('state_holiday_mapping.pkl')

@app.route('/')
def home():
    return "Time Series Sales Forecasting API is running"

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()

    store_id = int(data['store_id'])
    date = pd.to_datetime(data['date'])
    promo = int(data['promo'])
    state_holiday = str(data.get('state_holiday', '0'))
    school_holiday = int(data.get('school_holiday', 0))

    store_row = store_latest_features[store_latest_features['Store'] == store_id]
    if store_row.empty:
        return jsonify({'error': f'Store {store_id} not found'}), 404
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
    prediction = model.predict(X_input)[0]

    return jsonify({
        'store_id': store_id,
        'date': str(data['date']),
        'predicted_sales': round(float(prediction), 2)
    })

if __name__ == '__main__':
    app.run(debug=True)