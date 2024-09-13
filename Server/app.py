from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/manual')
def manual_control():
    return render_template('manual_control.html')

@app.route('/automatic')
def automatic_mode():
    return render_template('automatic_mode.html')

@app.route('/following')
def following_mode():
    return render_template('following_mode.html')

if __name__ == '__main__':
    app.run(debug=True)
