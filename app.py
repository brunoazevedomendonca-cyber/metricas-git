from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
import json
from datetime import datetime
import io
import csv

app = Flask(__name__)

class MetricsAnalyzer:
    def __init__(self, db_path="metrics.db"):
        self.db_path = db_path
    
    def get_commits_by_dev(self, start_date=None, end_date=None, repo=None):
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT author, COUNT(*) as commits, repo FROM commits WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if repo:
            query += " AND repo = ?"
            params.append(repo)
            
        query += " GROUP BY author, repo ORDER BY commits DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def get_pr_metrics(self, start_date=None, end_date=None, repo=None):
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT author, COUNT(*) as prs, AVG(merge_time_hours) as avg_merge_time, repo 
            FROM pulls WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        if repo:
            query += " AND repo = ?"
            params.append(repo)
            
        query += " GROUP BY author, repo"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def get_releases_count(self, start_date=None, end_date=None, repo=None):
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT repo, COUNT(*) as releases FROM releases WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if repo:
            query += " AND repo = ?"
            params.append(repo)
            
        query += " GROUP BY repo"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

analyzer = MetricsAnalyzer()

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
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    repo = request.args.get('repo')
    
    df = analyzer.get_commits_by_dev(start_date, end_date, repo)
    
    fig = go.Figure(data=[
        go.Bar(x=df['author'], y=df['commits'])
    ])
    fig.update_layout(title='Commits por Desenvolvedor')
    
    return jsonify({
        'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        'data': df.to_dict('records')
    })

@app.route('/api/prs')
def api_prs():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    repo = request.args.get('repo')
    
    df = analyzer.get_pr_metrics(start_date, end_date, repo)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='PRs', x=df['author'], y=df['prs']))
    fig.add_trace(go.Scatter(name='Tempo Médio (h)', x=df['author'], y=df['avg_merge_time'], yaxis='y2'))
    
    fig.update_layout(
        title='PRs e Tempo de Merge',
        yaxis2=dict(overlaying='y', side='right')
    )
    
    return jsonify({
        'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        'data': df.to_dict('records')
    })

@app.route('/api/releases')
def api_releases():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    repo = request.args.get('repo')
    
    df = analyzer.get_releases_count(start_date, end_date, repo)
    
    fig = go.Figure(data=[
        go.Bar(x=df['repo'], y=df['releases'])
    ])
    fig.update_layout(title='Releases por Repositório')
    
    return jsonify({
        'chart': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        'data': df.to_dict('records')
    })

@app.route('/export/<metric>')
def export_csv(metric):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    repo = request.args.get('repo')
    
    if metric == 'commits':
        df = analyzer.get_commits_by_dev(start_date, end_date, repo)
    elif metric == 'prs':
        df = analyzer.get_pr_metrics(start_date, end_date, repo)
    elif metric == 'releases':
        df = analyzer.get_releases_count(start_date, end_date, repo)
    
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{metric}_metrics.csv'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
