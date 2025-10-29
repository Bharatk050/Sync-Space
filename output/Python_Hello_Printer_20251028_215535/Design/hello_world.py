# Generated on: 2025-10-28 21:55:56

from flask import Flask

app = Flask(__name__)

@app.route('/hello', methods=['GET'])
def print_hello_world():
    """Prints 'hello world' to the console."""
    print('hello world')
    return 'hello world'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)