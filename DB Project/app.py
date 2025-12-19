from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

#  APP & DATABASE INITIALIZATION

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///corebank.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "replace_this_with_a_random_string"  # required for sessions and flash messages

db = SQLAlchemy(app)

#  DATABASE ENTITIES

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(100), unique=True, nullable=False)
    upass = db.Column(db.String(255), nullable=False)


class Customer(db.Model):
    __tablename__ = "clients"
    cid = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, db.ForeignKey("users.id"))
    cname = db.Column(db.String(100), nullable=False)
    cnic = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)


class Account(db.Model):
    __tablename__ = "bank_accounts"
    acc_no = db.Column(db.Integer, primary_key=True)
    cust_id = db.Column(db.Integer, db.ForeignKey("clients.cid"))
    mail = db.Column(db.String(120), nullable=False)
    acc_type = db.Column(db.String(20), nullable=False)
    funds = db.Column(db.Float, default=0.0)

    holder = db.relationship("Customer", backref="accs")


class Txn(db.Model):
    __tablename__ = "txn_history"
    tid = db.Column(db.Integer, primary_key=True)
    debit = db.Column(db.Integer, nullable=True)
    credit = db.Column(db.Integer, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    nature = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    uid = db.Column(db.Integer)

#audit class
class Audit(db.Model):
    __tablename__ = "audit_trail"
    lid = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(20), nullable=False)
    target = db.Column(db.String(30), nullable=False)
    actor = db.Column(db.String(30), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)


#  AUTH HELPERS

def login_required(view):
    @wraps(view)
    def secured(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return view(*args, **kwargs)
    return secured


def confirm_credentials(u, p):
    record = User.query.filter_by(uname=u).first()
    if record and check_password_hash(record.upass, p):
        return record
    return None


def register_user(u, p):
    encrypted = generate_password_hash(p)
    acc = User(uname=u, upass=encrypted)
    try:
        db.session.begin_nested()      # SAVEPOINT
        db.session.add(acc)
        db.session.commit()
    except Exception:
        db.session.rollback()          # ROLLBACK
        return None
    return acc


def add_audit(activity, table, actor):
    entry = Audit(action=activity, target=table, actor=actor)
    db.session.add(entry)
    db.session.commit()


#  ROOT ROUTE

@app.route("/")
def root():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


# ---------------------------------------------------------
#  AUTH ROUTES
# ---------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if User.query.filter_by(uname=u).first():
            flash("Username already taken.", "danger")
            return redirect("/signup")

        register_user(u, p)
        flash("Account created. You may log in.", "success")
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        auth = confirm_credentials(u, p)
        if auth:
            session["user_id"] = auth.id
            session["username"] = auth.uname
            return redirect("/dashboard")

        flash("Invalid login details.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect("/login")

#  DASHBOARD

@app.route("/dashboard")
@login_required
def home():
    uid = session["user_id"]

    custs = Customer.query.filter_by(owner=uid).all()
    accs = Account.query.join(Customer).filter(Customer.owner == uid).all()
    total = sum(a.funds for a in accs)

    last_txn = Txn.query.filter_by(uid=uid).order_by(Txn.timestamp.desc()).limit(5).all()

    return render_template(
        "index.html",
        cust_count=len(custs),
        acc_count=len(accs),
        total_balance=total,
        recent=last_txn
    )

#  CUSTOMER MODULE
@app.route("/clients")
@login_required
def list_clients():
    data = Customer.query.filter_by(owner=session["user_id"]).all()
    return render_template("customer.html", customers=data)


@app.route("/clients/new", methods=["POST"])
@login_required
def new_client():
    name = request.form["name"]
    cnic = request.form["cnic"]
    ph = request.form["contact"]
    uid = session["user_id"]

    if Customer.query.filter_by(cnic=cnic).first():
        flash("CNIC already registered.", "warning")
        return redirect("/clients")

    record = Customer(cname=name, cnic=cnic, phone=ph, owner=uid)
    db.session.add(record)
    add_audit("CREATE", "Customer", session["username"])
    db.session.commit()

    flash("Customer added.", "success")
    return redirect("/clients")


@app.route("/clients/remove/<int:cid>")
@login_required
def wipe_client(cid):
    uid = session["user_id"]

    row = Customer.query.filter_by(cid=cid, owner=uid).first()
    if not row:
        return redirect("/clients")

    linked = Account.query.filter_by(cust_id=cid).first()
    if linked:
        flash("Cannot delete customer with active accounts.", "danger")
        return redirect("/clients")

    db.session.delete(row)
    add_audit("DELETE", "Customer", session["username"])
    db.session.commit()

    flash("Customer removed.", "success")
    return redirect("/clients")

#  ACCOUNT MODULE


@app.route("/bank")
@login_required
def accounts():
    uid = session["user_id"]
    acc = Account.query.join(Customer).filter(Customer.owner == uid).all()
    cust = Customer.query.filter_by(owner=uid).all()
    return render_template("account.html", accounts=acc, customers=cust)


@app.route("/bank/new", methods=["POST"])
@login_required
def add_account():
    cid = request.form["customer_id"]
    typ = request.form["type"]
    bal = float(request.form["balance"])
    email = request.form["email"]

    uid = session["user_id"]
    verify = Customer.query.filter_by(cid=cid, owner=uid).first()
    if not verify:
        flash("Invalid customer selection.", "danger")
        return redirect("/bank")

    acc = Account(cust_id=cid, acc_type=typ, funds=bal, mail=email)
    db.session.add(acc)

    add_audit("CREATE", "Account", session["username"])

    initial_txn = Txn(credit=None, amount=bal, nature="Deposit", uid=uid)
    db.session.add(initial_txn)

    db.session.commit()

    flash("Account created.", "success")
    return redirect("/bank")

#  TRANSACTION MODULE


@app.route("/transactions")
@login_required
def txns():
    uid = session["user_id"]
    history = Txn.query.filter_by(uid=uid).order_by(Txn.timestamp.desc()).all()
    accs = Account.query.join(Customer).filter(Customer.owner == uid).all()

    return render_template("transactions.html", txns=history, accounts=accs)


@app.route("/transactions/new", methods=["POST"])
@login_required
def do_txn():
    mode = request.form["type"]
    val = float(request.form["amount"])
    uid = session["user_id"]

    # ------- Deposit / Withdraw -------
    if mode in ["Deposit", "Withdraw"]:
        acc_id = int(request.form["account"])
        target = Account.query.join(Customer, Account.cust_id == Customer.cid)\
            .filter(Account.acc_no == acc_id, Customer.owner == uid).first()

        if not target:
            flash("Invalid account.", "danger")
            return redirect("/transactions")

        if mode == "Deposit":
            target.funds += val
            txn = Txn(credit=acc_id, amount=val, nature="Deposit", uid=uid)
        else:
            if target.funds < val:
                flash("Insufficient balance.", "danger")
                return redirect("/transactions")
            target.funds -= val
            txn = Txn(debit=acc_id, amount=val, nature="Withdraw", uid=uid)

        db.session.add(txn)
        db.session.commit()
        flash(f"{mode} completed.", "success")
        return redirect("/transactions")

    # ------- Transfer -------
    else:
        s = int(request.form["from_account"])
        d = int(request.form["to_account"])

        src = Account.query.join(Customer, Account.cust_id == Customer.cid)\
            .filter(Account.acc_no == s, Customer.owner == uid).first()
        dst = Account.query.get(d)

        if not src or not dst:
            flash("Invalid transfer accounts.", "danger")
            return redirect("/transactions")
        if src.funds < val:
            flash("Insufficient balance.", "danger")
            return redirect("/transactions")

        src.funds -= val
        dst.funds += val

        txn = Txn(debit=s, credit=d, amount=val, nature="Transfer", uid=uid)
        db.session.add(txn)
        db.session.commit()

        flash("Transfer completed.", "success")
        return redirect("/transactions")

#  AUDIT TRAIL


@app.route("/trail")
@login_required
def audit_log():
    logs = Audit.query.order_by(Audit.time.desc()).limit(50).all()
    return render_template("audit.html", logs=logs)

#  BOOTSTRAP

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # create DB tables if not exist
    app.run(debug=True)
