from flask import Flask, render_template, request, jsonify, Response
import json
import io
import csv
from datetime import datetime, timedelta

app = Flask(__name__)

# Dados mockados
mock_data = {
    "commits": [
        {"author": "luis@company.com", "commits": 25, "repo": "backend-api"},
        {"author": "maria@company.com", "commits": 18, "repo": "backend-api"},
        {"author": "joao@company.com", "commits": 22, "repo": "frontend"},
        {"author": "ana@company.com", "commits": 15, "repo": "frontend"},
        {"author": "carlos@company.com", "commits": 12, "repo": "mobile"},
        {"author": "pedro@company.com", "commits": 8, "repo": "mobile"}
    ],
    "prs": [
        {"author": "luis@company.com", "prs": 8, "avg_merge_time": 4.2, "repo": "backend-api"},
        {"author": "maria@company.com", "prs": 6, "avg_merge_time": 3.8, "repo": "backend-api"},
        {"author": "joao@company.com", "prs": 7, "avg_merge_time": 5.1, "repo": "frontend"},
        {"author": "ana@company.com", "prs": 5, "avg_merge_time": 2.9, "repo": "frontend"},
        {"author": "carlos@company.com", "prs": 4, "avg_merge_time": 6.2, "repo": "mobile"},
        {"author": "pedro@company.com", "prs": 3, "avg_merge_time": 4.5, "repo": "mobile"}
    ],
    "releases": [
        {"repo": "backend-api", "releases": 4},
        {"repo": "frontend", "releases": 3},
        {"repo": "mobile", "releases": 2}
    ]
}

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/commits')
def commits_page():
    return render_template('commits.html')

@app.route('/prs')
def prs_page():
    return render_template('prs.html')

@app.route('/releases')
def releases_page():
    return render_template('releases.html')

@app.route('/api/commits')
def api_commits():
    data = mock_data["commits"]
    
    chart_data = {
        "data": [{
            "x": [item["author"] for item in data],
            "y": [item["commits"] for item in data],
            "type": "bar"
        }],
        "layout": {"title": "Commits por Desenvolvedor"}
    }
    
    return jsonify({
        'chart': json.dumps(chart_data),
        'data': data
    })

@app.route('/api/prs')
def api_prs():
    data = mock_data["prs"]
    
    chart_data = {
        "data": [
            {
                "x": [item["author"] for item in data],
                "y": [item["prs"] for item in data],
                "type": "bar",
                "name": "PRs"
            },
            {
                "x": [item["author"] for item in data],
                "y": [item["avg_merge_time"] for item in data],
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Tempo Médio (h)",
                "yaxis": "y2"
            }
        ],
        "layout": {
            "title": "PRs e Tempo de Merge",
            "yaxis2": {"overlaying": "y", "side": "right"}
        }
    }
    
    return jsonify({
        'chart': json.dumps(chart_data),
        'data': data
    })

@app.route('/api/releases')
def api_releases():
    data = mock_data["releases"]
    
    chart_data = {
        "data": [{
            "x": [item["repo"] for item in data],
            "y": [item["releases"] for item in data],
            "type": "bar"
        }],
        "layout": {"title": "Releases por Repositório"}
    }
    
    return jsonify({
        'chart': json.dumps(chart_data),
        'data': data
    })

@app.route('/export/<metric>')
def export_csv(metric):
    data = mock_data.get(metric, [])
    
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={metric}_metrics.csv'}
    )
    return response

if __name__ == '__main__':
    print("🚀 Iniciando Git Metrics Dashboard...")
    print("📊 Acesse: http://localhost:5000")
    print("📈 Dados mockados carregados com sucesso!")
    app.run(debug=True, port=5000)
