from flask import Flask, request, jsonify
from scl_code_generator import SCLCodeGenerator, SCLCodeGeneratorForFunction
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/', methods=['POST'])
def process_request():
    try:
        json_data = request.get_json()  # 解析请求包中的JSON数据

        logging.info("Request data: %s", json_data)

        name = json_data.get("name")

        if json_data["type"] == "FUNCTION":
            scl_code_generator = SCLCodeGeneratorForFunction()
        else:
            scl_code_generator = SCLCodeGenerator()

        code = scl_code_generator.generate_code(json_data)

        response = {
            "name": name,
            "code":code
        }

        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)