from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import random
import statistics
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'paper-review-system-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paper_review.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
CORS(app)
jwt = JWTManager(app)

# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, expert, viewer
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    expertise = db.Column(db.Text)  # 专业领域，JSON格式
    status = db.Column(db.String(20), default='active')  # active, busy, vacation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    abstract = db.Column(db.Text)
    keywords = db.Column(db.String(200))
    file_path = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, assigned, reviewing, completed
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    field = db.Column(db.String(100))  # 研究领域

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='assigned')  # assigned, reviewing, completed
    
    paper = db.relationship('Paper', backref='assignments')
    expert = db.relationship('User', backref='assignments')
#1
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    innovation_score = db.Column(db.Integer)  # 学术创新性 30分
    feasibility_score = db.Column(db.Integer)  # 技术可行性 25分
    quality_score = db.Column(db.Integer)  # 论文质量 25分
    value_score = db.Column(db.Integer)  # 实用价值 20分
    total_score = db.Column(db.Integer)  # 总分
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    assignment = db.relationship('Assignment', backref='review')

# 初始化数据库函数
def init_database():
    db.create_all()
    
    # 创建默认管理员账户
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            name='系统管理员',
            email='admin@system.com',
            expertise=json.dumps(['系统管理'])
        )
        db.session.add(admin)
        db.session.commit()

# 认证相关API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'success': True,
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'role': user.role,
                'email': user.email
            }
        })
    
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

# 用户管理API
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.all()
    return jsonify({
        'success': True,
        'users': [{
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'expertise': json.loads(user.expertise) if user.expertise else [],
            'status': user.status,
            'created_at': user.created_at.isoformat()
        } for user in users]
    })

@app.route('/api/users', methods=['POST'])
@jwt_required()
def create_user():
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['username', 'password', 'name', 'email', 'role']
        for field in required_fields:
            if not data.get(field) or not data.get(field).strip():
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        
        # 验证用户名长度
        if len(data['username']) < 3:
            return jsonify({'success': False, 'message': '用户名至少需要3个字符'}), 400
        
        # 验证密码长度
        if len(data['password']) < 6:
            return jsonify({'success': False, 'message': '密码至少需要6个字符'}), 400
        
        # 验证邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400
        
        # 验证角色
        valid_roles = ['admin', 'expert', 'author']
        if data['role'] not in valid_roles:
            return jsonify({'success': False, 'message': f'无效的角色，必须是: {", ".join(valid_roles)}'}), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': '邮箱已被使用'}), 400
        
        # 创建用户
        user = User(
            username=data['username'].strip(),
            password_hash=generate_password_hash(data['password']),
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            role=data['role'],
            expertise=json.dumps(data.get('expertise', [])),
            status=data.get('status', 'active')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '用户创建成功'})
        
    except Exception as e:
        db.session.rollback()
        print(f"创建用户时发生错误: {str(e)}")  # 在服务器控制台打印详细错误
        return jsonify({'success': False, 'message': f'创建用户失败: {str(e)}'}), 500
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '用户创建成功'})

# 论文管理API
@app.route('/api/papers', methods=['GET'])
@jwt_required()
def get_papers():
    papers = Paper.query.all()
    result = []
    
    for paper in papers:
        # 获取分配的专家
        assignments = Assignment.query.filter_by(paper_id=paper.id).all()
        experts = [{
            'id': assignment.expert.id,
            'name': assignment.expert.name,
            'status': assignment.status
        } for assignment in assignments]
        
        # 计算平均分
        reviews = [assignment.review for assignment in assignments if assignment.review]
        avg_score = statistics.mean([review.total_score for review in reviews]) if reviews else None
        
        result.append({
            'id': paper.id,
            'title': paper.title,
            'author': paper.author,
            'abstract': paper.abstract,
            'keywords': paper.keywords,
            'field': paper.field,
            'status': paper.status,
            'submitted_at': paper.submitted_at.isoformat(),
            'experts': experts,
            'avg_score': round(avg_score, 2) if avg_score else None,
            'review_count': len(reviews)
        })
    
    return jsonify({'success': True, 'papers': result})

@app.route('/api/papers', methods=['POST'])
@jwt_required()
def create_paper():
    data = request.get_json()
    
    paper = Paper(
        title=data['title'],
        author=data['author'],
        abstract=data.get('abstract', ''),
        keywords=data.get('keywords', ''),
        field=data.get('field', '')
    )
    
    db.session.add(paper)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '论文添加成功', 'paper_id': paper.id})

# 智能分配算法
@app.route('/api/papers/<int:paper_id>/assign', methods=['POST'])
@jwt_required()
def assign_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    
    # 获取所有可用的专家
    experts = User.query.filter_by(role='expert', status='active').all()
    
    # 计算每个专家的当前工作量
    expert_workload = {}
    for expert in experts:
        current_assignments = Assignment.query.filter_by(
            expert_id=expert.id,
            status__in=['assigned', 'reviewing']
        ).count()
        expert_workload[expert.id] = current_assignments
    
    # 过滤出工作量未满的专家（少于10篇）
    available_experts = [expert for expert in experts if expert_workload[expert.id] < 10]
    
    if len(available_experts) < 3:
        return jsonify({'success': False, 'message': '可用专家不足，无法分配'}), 400
    
    # 智能分配算法
    def calculate_priority(expert):
        # 可用度权重(40%)
        availability = (10 - expert_workload[expert.id]) / 10 * 0.4
        
        # 专业匹配度权重(35%)
        expertise_list = json.loads(expert.expertise) if expert.expertise else []
        match_score = 0.5  # 默认匹配度
        if paper.field and paper.field in expertise_list:
            match_score = 1.0
        elif any(field in paper.field for field in expertise_list if paper.field):
            match_score = 0.8
        professional_match = match_score * 0.35
        
        # 负载均衡权重(25%)
        min_workload = min(expert_workload.values()) if expert_workload.values() else 0
        max_workload = max(expert_workload.values()) if expert_workload.values() else 0
        if max_workload == min_workload:
            balance_score = 1.0
        else:
            balance_score = (max_workload - expert_workload[expert.id]) / (max_workload - min_workload)
        load_balance = balance_score * 0.25
        
        return availability + professional_match + load_balance
    
    # 计算所有专家的优先级并排序
    expert_priorities = [(expert, calculate_priority(expert)) for expert in available_experts]
    expert_priorities.sort(key=lambda x: x[1], reverse=True)
    
    # 选择前3名专家
    selected_experts = [expert for expert, _ in expert_priorities[:3]]
    
    # 创建分配记录
    for expert in selected_experts:
        assignment = Assignment(
            paper_id=paper_id,
            expert_id=expert.id
        )
        db.session.add(assignment)
    
    # 更新论文状态
    paper.status = 'assigned'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '论文分配成功',
        'assigned_experts': [{
            'id': expert.id,
            'name': expert.name,
            'email': expert.email
        } for expert in selected_experts]
    })

# 评审相关API
@app.route('/api/my-assignments', methods=['GET'])
@jwt_required()
def get_my_assignments():
    expert_id = get_jwt_identity()
    assignments = Assignment.query.filter_by(expert_id=expert_id).all()
    
    result = []
    for assignment in assignments:
        result.append({
            'id': assignment.id,
            'paper': {
                'id': assignment.paper.id,
                'title': assignment.paper.title,
                'author': assignment.paper.author,
                'abstract': assignment.paper.abstract,
                'keywords': assignment.paper.keywords,
                'field': assignment.paper.field
            },
            'status': assignment.status,
            'assigned_at': assignment.assigned_at.isoformat(),
            'has_review': assignment.review is not None
        })
    
    return jsonify({'success': True, 'assignments': result})

@app.route('/api/assignments/<int:assignment_id>/review', methods=['POST'])
@jwt_required()
def submit_review(assignment_id):
    data = request.get_json()
    expert_id = get_jwt_identity()
    
    assignment = Assignment.query.filter_by(id=assignment_id, expert_id=expert_id).first()
    if not assignment:
        return jsonify({'success': False, 'message': '分配记录不存在'}), 404
    
    # 检查是否已经提交过评审
    if assignment.review:
        return jsonify({'success': False, 'message': '已经提交过评审'}), 400
    
    # 计算总分
    total_score = (
        data['innovation_score'] + 
        data['feasibility_score'] + 
        data['quality_score'] + 
        data['value_score']
    )
    
    review = Review(
        assignment_id=assignment_id,
        innovation_score=data['innovation_score'],
        feasibility_score=data['feasibility_score'],
        quality_score=data['quality_score'],
        value_score=data['value_score'],
        total_score=total_score,
        comments=data.get('comments', '')
    )
    
    db.session.add(review)
    assignment.status = 'completed'
    
    # 检查论文是否所有评审都完成
    paper_assignments = Assignment.query.filter_by(paper_id=assignment.paper_id).all()
    if all(a.status == 'completed' for a in paper_assignments):
        assignment.paper.status = 'completed'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': '评审提交成功'})

# 统计分析API
@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    # 基本统计
    total_papers = Paper.query.count()
    completed_papers = Paper.query.filter_by(status='completed').count()
    total_experts = User.query.filter_by(role='expert').count()
    total_reviews = Review.query.count()
    
    # 评审进度统计
    pending_papers = Paper.query.filter_by(status='pending').count()
    assigned_papers = Paper.query.filter_by(status='assigned').count()
    reviewing_papers = Paper.query.filter_by(status='reviewing').count()
    
    # 专家工作量统计
    expert_workload = []
    experts = User.query.filter_by(role='expert').all()
    for expert in experts:
        current_assignments = Assignment.query.filter_by(
            expert_id=expert.id,
            status__in=['assigned', 'reviewing']
        ).count()
        completed_reviews = Assignment.query.filter_by(
            expert_id=expert.id,
            status='completed'
        ).count()
        
        expert_workload.append({
            'name': expert.name,
            'current_assignments': current_assignments,
            'completed_reviews': completed_reviews,
            'total_assignments': current_assignments + completed_reviews
        })
    
    # 评分分布统计
    reviews = Review.query.all()
    score_distribution = {
        '90-100': 0,
        '80-89': 0,
        '70-79': 0,
        '60-69': 0,
        '0-59': 0
    }
    
    for review in reviews:
        score = review.total_score
        if score >= 90:
            score_distribution['90-100'] += 1
        elif score >= 80:
            score_distribution['80-89'] += 1
        elif score >= 70:
            score_distribution['70-79'] += 1
        elif score >= 60:
            score_distribution['60-69'] += 1
        else:
            score_distribution['0-59'] += 1
    
    return jsonify({
        'success': True,
        'statistics': {
            'basic': {
                'total_papers': total_papers,
                'completed_papers': completed_papers,
                'total_experts': total_experts,
                'total_reviews': total_reviews
            },
            'progress': {
                'pending': pending_papers,
                'assigned': assigned_papers,
                'reviewing': reviewing_papers,
                'completed': completed_papers
            },
            'expert_workload': expert_workload,
            'score_distribution': score_distribution
        }
    })

# 静态文件服务
@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    with app.app_context():
        init_database()
        print('数据库初始化完成')
        print('默认管理员账户: admin/admin123')
        print('系统启动中...')
        print('访问地址: http://localhost:5000')
    
    app.run(debug=True, host='0.0.0.0', port=5000)