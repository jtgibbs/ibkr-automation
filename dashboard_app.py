from flask import Flask, render_template_string
import boto3
import json
from datetime import datetime, timedelta

app = Flask(__name__)
s3 = boto3.client('s3')

DATA_BUCKET = "jgs3-automation-data"
REPORTS_BUCKET = "jgs3-automation-reports"

def get_latest_account_data():
    """Find the most recent account summary in S3."""
    today = datetime.now()
    for days_back in range(7):
        date = today - timedelta(days=days_back)
        key = f"ibkr/account/{date.strftime('%Y/%m/%d')}/summary.json"
        try:
            resp = s3.get_object(Bucket=DATA_BUCKET, Key=key)
            return json.loads(resp['Body'].read()), date.strftime('%Y-%m-%d')
        except:
            continue
    return None, None

def get_pipeline_history():
    """Get recent pipeline log entries."""
    logs = []
    today = datetime.now()
    for days_back in range(7):
        date = today - timedelta(days=days_back)
        prefix = f"pipeline_logs/{date.strftime('%Y/%m/%d')}/"
        try:
            resp = s3.list_objects_v2(Bucket="jgs3-automation-logs", Prefix=prefix)
            for obj in resp.get('Contents', []):
                log_resp = s3.get_object(Bucket="jgs3-automation-logs", Key=obj['Key'])
                log_entry = json.loads(log_resp['Body'].read())
                logs.append(log_entry)
        except:
            continue
    return sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)[:20]

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IBKR Automation Dashboard</title>
    <meta http-equiv="refresh" content="300">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #0f1923; color: #e0e0e0; }
        .header {
            background: linear-gradient(135deg, #1B3A5C, #2d5f8a);
            padding: 30px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 24px; color: white; }
        .header .status {
            background: #28a745;
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
        }
        .header .status.error { background: #dc3545; }
        .container { max-width: 1100px; margin: 30px auto; padding: 0 20px; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card {
            background: #1a2833;
            border-radius: 10px;
            padding: 24px;
            border: 1px solid #2a3f50;
        }
        .card .label { font-size: 12px; color: #7a8d9e; text-transform: uppercase; letter-spacing: 1px; }
        .card .value { font-size: 28px; font-weight: bold; margin-top: 8px; color: white; }
        .card .value.green { color: #28a745; }
        .card .value.red { color: #dc3545; }
        .section {
            background: #1a2833;
            border-radius: 10px;
            padding: 24px;
            border: 1px solid #2a3f50;
            margin-bottom: 20px;
        }
        .section h2 { font-size: 16px; color: #7a8d9e; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1px; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 10px; color: #7a8d9e; font-size: 12px; text-transform: uppercase; border-bottom: 1px solid #2a3f50; }
        td { padding: 10px; border-bottom: 1px solid #1f3040; font-size: 14px; }
        .log-info { color: #4da6ff; }
        .log-error { color: #dc3545; }
        .footer { text-align: center; padding: 30px; color: #4a5568; font-size: 12px; }
        .infra-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
        .infra-item {
            background: #0f1923;
            padding: 14px;
            border-radius: 8px;
            text-align: center;
        }
        .infra-item .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #28a745; margin-right: 6px; }
        .infra-item .name { font-size: 13px; color: #7a8d9e; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>IBKR Automation Dashboard</h1>
            <p style="color:#7a8d9e;margin-top:4px;font-size:13px">Paper Trading | DU7726760</p>
        </div>
        <div class="status {{ 'error' if not account_data else '' }}">
            {{ 'LIVE' if account_data else 'NO DATA' }}
        </div>
    </div>

    <div class="container">
        {% if account_data %}
        <div class="cards">
            <div class="card">
                <div class="label">Net Liquidation</div>
                <div class="value">${{ "{:,.2f}".format(account_data.get('NetLiquidation', 0)) }}</div>
            </div>
            <div class="card">
                <div class="label">Cash</div>
                <div class="value">${{ "{:,.2f}".format(account_data.get('TotalCashValue', 0)) }}</div>
            </div>
            <div class="card">
                <div class="label">Unrealized P&L</div>
                {% set upnl = account_data.get('UnrealizedPnL', 0) %}
                <div class="value {{ 'green' if upnl >= 0 else 'red' }}">${{ "{:+,.2f}".format(upnl) }}</div>
            </div>
            <div class="card">
                <div class="label">Buying Power</div>
                <div class="value">${{ "{:,.2f}".format(account_data.get('BuyingPower', 0)) }}</div>
            </div>
        </div>

        <div class="section">
            <h2>Data As Of</h2>
            <p>{{ data_date }} — {{ account_data.get('timestamp', 'N/A')[:19] }}</p>
        </div>
        {% endif %}

        <div class="section">
            <h2>Infrastructure Status</h2>
            <div class="infra-grid">
                <div class="infra-item"><span class="dot"></span><span class="name">EC2 Instance</span></div>
                <div class="infra-item"><span class="dot"></span><span class="name">IB Gateway</span></div>
                <div class="infra-item"><span class="dot"></span><span class="name">S3 Storage</span></div>
                <div class="infra-item"><span class="dot"></span><span class="name">Lambda Monitor</span></div>
                <div class="infra-item"><span class="dot"></span><span class="name">SES Email</span></div>
                <div class="infra-item"><span class="dot"></span><span class="name">Cron Scheduler</span></div>
            </div>
        </div>

        <div class="section">
            <h2>Recent Pipeline Activity</h2>
            <table>
                <tr><th>Timestamp</th><th>Source</th><th>Level</th><th>Message</th></tr>
                {% for log in logs[:15] %}
                <tr>
                    <td>{{ log.get('timestamp', 'N/A')[:19] }}</td>
                    <td>{{ log.get('source', 'pipeline') }}</td>
                    <td class="{{ 'log-error' if log.get('level') == 'ERROR' else 'log-info' }}">{{ log.get('level', 'INFO') }}</td>
                    <td>{{ log.get('message', '') }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <div class="footer">
        Built with Python, Flask, AWS (EC2, S3, Lambda, SES, CloudWatch) | Auto-refreshes every 5 minutes
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    account_data, data_date = get_latest_account_data()
    logs = get_pipeline_history()
    return render_template_string(TEMPLATE,
                                  account_data=account_data,
                                  data_date=data_date,
                                  logs=logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
