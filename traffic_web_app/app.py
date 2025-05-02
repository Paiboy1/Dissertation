from flask import Flask, render_template, request
import subprocess
import sys
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        date = request.form['date']
        hour = int(request.form['hour'])
        start = request.form['start']
        end = request.form['end']

        # Get current file directory and build path to route_planner.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        route_script = os.path.join(base_dir, 'route_planner.py')

        # Run the full script
        result = subprocess.run(
            [sys.executable, route_script, start, end, date, str(hour)],
            capture_output=True, text=True
        )
        travel_time = result.stdout.strip()

        return render_template('result.html', travel_time=travel_time)

    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)