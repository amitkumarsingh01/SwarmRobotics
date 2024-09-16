from flask import Flask, render_template, redirect, url_for
import paramiko

app = Flask(__name__)

'''
def execute_on_pi(command):
    pi_ip = '192.168.216.58'
    pi_username = 'sujith'
    pi_password = 'Subramanya@12'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(pi_ip, username=pi_username, password=pi_password)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    ssh.close()
    return output

@app.route('/automatic')
def automatic():
    # Command to execute the script on the Pi
    command = 'python3 /home/sujith/FinalBlueAutonomous.py'
    
    # Execute the command on the Raspberry Pi
    output = execute_on_pi(command)
    
    # Optionally handle output or errors
    print(output)
    
    # Redirect to another page or provide feedback
    return redirect(url_for('index'))
'''
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

@app.route('/manual_bot')
def manual_bot():
    return render_template('manual_bot.html')

@app.route('/manual_main')
def manual_main():
    return render_template('manual_main.html')

@app.route('/manual_green')
def manual_green():
    return render_template('manual_green.html')

@app.route('/manual_pink')
def manual_pink():
    return render_template('manual_pink.html')

if __name__ == '__main__':
    app.run(debug=True)
