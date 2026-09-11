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