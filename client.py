import json
import time
import xmlrpc.client
from flask import Flask,request,jsonify

# Create Flask app
app = Flask(__name__)

# Create an RPC client
RPC = xmlrpc.client.ServerProxy("http://127.0.0.1:22116/")

def RpcCall(username: str = "mai1", appid: str = "wx60786665cba15416", function_name: str = "wx.login()",
            timeout: int = 5, **kwargs):
    result = RPC.call(username, appid, function_name, timeout, json.dumps(kwargs))
    try:
        return json.loads(result)
    except Exception as e:
        return {"data": result, "err_msg": str(e)}

@app.route('/call', methods=['POST'])
def call():
    # 获取JSON请求体
    request_data = request.get_json()

    # 判断必填参数 'appid' 和 'username' 是否存在
    appid = request_data.get('appid')
    username = request_data.get('username')

    if not appid:
        return jsonify({"error": "'appid' parameter is required"}), 400
    if not username:
        return jsonify({"error": "'username' parameter is required"}), 400

    # 获取其他动态参数（除了 appid 和 username）
    kwargs = {key: value for key, value in request_data.items() if key not in ['appid', 'username']}

    # 调用 RpcCall 函数，传入动态的参数
    result = RpcCall(
        username=username,
        appid=appid,
        **kwargs
    )

    # 返回结果作为 JSON 响应
    return jsonify(result)


if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(debug=True, host='0.0.0.0', port=12218)
