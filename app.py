from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def check_vehicle():
    message = None
    if request.method == 'POST':
        plate_number = request.form.get('plate_number')

        # Connect to MySQL and check `verified_plates`
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="numberplate",
            port=3306
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM verified_plates WHERE numberplate = %s", (plate_number,))
        result = cursor.fetchone()
        connection.close()

        if result:
            message = f"Vehicle {plate_number} has passed the gateway."
        else:
            message = f"Vehicle {plate_number} has NOT passed the gateway."

    # Reset the message if the page is being reloaded (GET request)
    if request.method == 'GET':
        message = None

    return render_template('index.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)
