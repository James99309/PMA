from flask import Flask, render_template, request, jsonify, redirect, url_for
from models.models import db, Project, Customer, Quotation, Score
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales_report.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

db.init_app(app)

# 常量定义
SCORE_RULES = {
    'design_institute': 10,
    'dealer': 20,
    'integrator': 50,
    'user': 30
}

PROJECT_TYPES = {
    'sales_focus': '销售重点',
    'channel_follow': '渠道跟进',
    'design_institute': '设计院阶段'
}

SOURCE_TYPES = {
    'design_institute': '设计院',
    'dealer': '经销商',
    'integrator': '系统集成商',
    'user': '用户'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/projects')
def projects():
    projects = Project.query.all()
    return render_template('projects.html', projects=projects)

@app.route('/project/<int:id>')
def project_detail(id):
    project = Project.query.get_or_404(id)
    return render_template('project_detail.html', project=project)

@app.route('/project/add', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        project = Project(
            project_number=request.form['project_number'],
            project_name=request.form['project_name'],
            current_stage=request.form['current_stage'],
            authorization_number=request.form['authorization_number'],
            distributor=request.form['distributor'],
            project_type=request.form['project_type'],
            source=request.form['source'],
            face_value=float(request.form['face_value'])
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('projects'))
    return render_template('add_project.html')

@app.route('/project/<int:id>/edit', methods=['GET', 'POST'])
def edit_project(id):
    project = Project.query.get_or_404(id)
    if request.method == 'POST':
        project.project_name = request.form['project_name']
        project.current_stage = request.form['current_stage']
        project.authorization_number = request.form['authorization_number']
        project.distributor = request.form['distributor']
        project.project_type = request.form['project_type']
        project.source = request.form['source']
        project.face_value = float(request.form['face_value'])
        project.update_time = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('project_detail', id=id))
    return render_template('edit_project.html', project=project)

@app.route('/customers')
def customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@app.route('/quotations')
def quotations():
    quotations = Quotation.query.all()
    return render_template('quotations.html', quotations=quotations)

@app.route('/scores')
def scores():
    scores = Score.query.all()
    return render_template('scores.html', scores=scores)

def calculate_project_score(project_type, source_type):
    base_score = 0
    
    # 根据项目类型计算基础积分
    if project_type == PROJECT_TYPES['sales_focus']:
        base_score = 50
    elif project_type == PROJECT_TYPES['channel_follow']:
        base_score = 30
    elif project_type == PROJECT_TYPES['design_institute']:
        base_score = 100
    
    # 根据来源类型计算额外积分
    if source_type == SOURCE_TYPES['design_institute']:
        base_score += SCORE_RULES['design_institute']
    elif source_type == SOURCE_TYPES['dealer']:
        base_score += SCORE_RULES['dealer']
    elif source_type == SOURCE_TYPES['integrator']:
        base_score += SCORE_RULES['integrator']
    elif source_type == SOURCE_TYPES['user']:
        base_score += SCORE_RULES['user']
    
    return base_score

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 