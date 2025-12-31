import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expenses = db.relationship('Expense', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expenses = db.relationship('Expense', backref='category', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Fixed for SQLAlchemy 2.0

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create default categories for new user
        default_categories = ['Food', 'Transportation', 'Entertainment', 'Utilities', 'Shopping', 'Healthcare']
        for cat_name in default_categories:
            category = Category(name=cat_name, user_id=user.id)
            db.session.add(category)
        
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get expenses for the current month
    today = datetime.now()
    first_day = today.replace(day=1).date()  # Convert to date() for comparison
    
    monthly_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= first_day
    ).all()
    
    total_monthly = sum(exp.amount for exp in monthly_expenses)
    
    # Get category-wise breakdown
    categories = Category.query.filter_by(user_id=current_user.id).all()
    category_data = []
    for category in categories:
        # Convert expense.date to string for comparison or use date() method
        category_total = sum(exp.amount for exp in category.expenses 
                          if exp.date >= first_day)  # Now both are date objects
        if category_total > 0:
            category_data.append({
                'name': category.name,
                'total': category_total
            })
    
    # Recent expenses
    recent_expenses = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(Expense.date.desc()).limit(5).all()
    
    # Calculate highest spending category
    highest_category = None
    if category_data:
        highest_category = max(category_data, key=lambda x: x['total'])
    
    return render_template('dashboard.html',
                         total_monthly=total_monthly,
                         category_data=category_data,
                         recent_expenses=recent_expenses,
                         current_month=today.strftime('%B %Y'),
                         highest_category=highest_category,
                         today=today)

@app.route('/expenses')
@login_required
def expenses():
    expenses_list = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(Expense.date.desc()).all()
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('expenses.html', expenses=expenses_list, categories=categories)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        category_id = int(request.form['category_id'])
        
        expense = Expense(
            amount=amount,
            description=description,
            date=date,
            user_id=current_user.id,
            category_id=category_id
        )
        
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense added successfully!')
        return redirect(url_for('expenses'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    today = datetime.now()  # Add this line
    return render_template('add_expense.html', categories=categories, today=today)  # Pass today

@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    
    if expense.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('expenses'))
    
    if request.method == 'POST':
        expense.amount = float(request.form['amount'])
        expense.description = request.form['description']
        expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        expense.category_id = int(request.form['category_id'])
        
        db.session.commit()
        flash('Expense updated successfully!')
        return redirect(url_for('expenses'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    today = datetime.now()  # Add this line
    return render_template('add_expense.html', expense=expense, categories=categories, today=today)  # Pass today

@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    
    if expense.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('expenses'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!')
    return redirect(url_for('expenses'))

@app.route('/categories')
@login_required
def categories():
    categories_list = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', categories=categories_list)

@app.route('/add_category', methods=['POST'])
@login_required
def add_category():
    name = request.form['name']
    
    if Category.query.filter_by(name=name, user_id=current_user.id).first():
        flash('Category already exists')
        return redirect(url_for('categories'))
    
    category = Category(name=name, user_id=current_user.id)
    db.session.add(category)
    db.session.commit()
    
    flash('Category added successfully!')
    return redirect(url_for('categories'))

@app.route('/delete_category/<int:id>')
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    if category.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('categories'))
    
    if category.expenses:
        flash('Cannot delete category with existing expenses')
        return redirect(url_for('categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully!')
    return redirect(url_for('categories'))

@app.route('/api/monthly_stats')
@login_required
def monthly_stats():
    today = datetime.now()
    monthly_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= today.replace(day=1)
    ).all()
    
    total = sum(exp.amount for exp in monthly_expenses)
    
    return jsonify({
        'total': total,
        'count': len(monthly_expenses)
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)