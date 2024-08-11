from flask import Flask, request, jsonify
import requests
import time
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.DEBUG)

# 定义模型 URL
SIMPLE_MODEL_URL = 'https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions'
ADVANCED_MODEL_URL = 'https://api.replicate.com/v1/models/black-forest-labs/flux-dev/predictions'

# 用于提交生成请求
@app.route('/generate', methods=['POST'])
def generate_image():
    api_key = request.headers.get('Authorization')
    if not api_key:
        app.logger.error('API key is missing in the request headers.')
        return jsonify({'error': 'API key is required'}), 400

    # 确保 API Key 以 'Bearer ' 开头
    if not api_key.startswith('Bearer '):
        app.logger.error('API key must start with "Bearer ".')
        return jsonify({'error': 'Invalid API key format'}), 400

    # 提取请求体
    request_data = request.get_json()
    prompt = request_data.get('prompt', '')
    num_outputs = request_data.get('num_outputs', 1)
    aspect_ratio = request_data.get('aspect_ratio', '1:1')
    output_format = request_data.get('output_format', 'webp')
    output_quality = request_data.get('output_quality', 90)
    model_type = request_data.get('model_type', 'simple')  # 新增参数 model_type

    app.logger.debug(f'model_type is : {model_type}')
    if model_type == 'flux-dev':
        model_url = ADVANCED_MODEL_URL
    else:
        model_url = SIMPLE_MODEL_URL
    app.logger.debug(f'using model to generate image : {model_url}')

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }
    data = {
        "input": {
            "prompt": prompt,
            "num_outputs": num_outputs,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "output_quality": output_quality
        }
    }

    app.logger.debug(f'Request headers: {headers}')
    app.logger.debug(f'Request body: {data}')

    try:
        response = requests.post(model_url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for bad HTTP status codes
        result = response.json()
        
        if 'id' in result:
            prediction_id = result['id']
            return jsonify({'prediction_id': prediction_id})
        else:
            app.logger.error(f'Failed to create prediction: {result}')
            return jsonify({'error': 'Failed to create prediction'}), 500
    except requests.exceptions.RequestException as e:
        app.logger.error(f'Request exception: {e}')
        return jsonify({'error': 'Request failed'}), 500

# 用于查询生成状态
@app.route('/status', methods=['GET'])
def check_status():
    api_key = request.headers.get('Authorization')
    if not api_key:
        app.logger.error('API key is missing in the request headers.')
        return jsonify({'error': 'API key is required'}), 400

    # 确保 API Key 以 'Bearer ' 开头
    if not api_key.startswith('Bearer '):
        app.logger.error('API key must start with "Bearer ".')
        return jsonify({'error': 'Invalid API key format'}), 400

    # 从查询参数获取 prediction_id
    prediction_id = request.args.get('prediction_id')
    if not prediction_id:
        app.logger.error('Prediction ID is required.')
        return jsonify({'error': 'Prediction ID is required'}), 400

    headers = {
        'Authorization': api_key,
    }
    status_url = f'https://api.replicate.com/v1/predictions/{prediction_id}'

    app.logger.debug(f'Status URL: {status_url}')
    app.logger.debug(f'Request headers: {headers}')

    timeout = 30  # 超时时间为30秒
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(status_url, headers=headers)
            response.raise_for_status()  # Raise an error for bad HTTP status codes
            result = response.json()

            status = result.get('status')
            if status == 'succeeded':
                output_url = result.get('output')
                return jsonify({'status': status, 'output': output_url})

            elif status == 'failed':
                app.logger.error(f'Prediction failed: {result}')
                return jsonify({'status': status, 'error': result.get('error')}), 500

            time.sleep(5)  # 每隔5秒查询一次状态
        except requests.exceptions.RequestException as e:
            app.logger.error(f'Request exception: {e}')
            return jsonify({'error': 'Request failed'}), 500

    app.logger.error('The process timed out.')
    return jsonify({'status': 'timeout', 'message': 'The process timed out'}), 504

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8055, debug=True)

