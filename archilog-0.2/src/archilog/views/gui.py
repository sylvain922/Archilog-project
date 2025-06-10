from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import archilog.models as models
from archilog import services
import io
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField
from wtforms.validators import DataRequired
import logging

logging.warning("Watch out!")
logging.info("I told you so")

web_ui = Blueprint('web_ui', __name__)

auth = HTTPBasicAuth()
users = {
    "user": {"username" : "User", "password": generate_password_hash("hello"), "roles": "user"},
    "admin": {"username" : "Admin", "password": generate_password_hash("bye"), "roles": "admin"}
}

class Form(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    amount = FloatField('Montant', validators=[DataRequired()])
    category = StringField('Catégorie', validators=[DataRequired()])


@auth.verify_password
def verify_password(username, password):
    if username in users and \
        check_password_hash(users.get(username).get("password"), password):
        return users.get(username)


@auth.get_user_roles
def get_user_roles(user):
    return user.get("roles", [])


@web_ui.route("/logout")
def logout():
    return "", 401, {
        "WWW-Authenticate": 'Basic realm="Authentication Required"'
    }


@web_ui.route("/")
@auth.login_required
def index():
    form = Form()
    entries = models.get_all_entries()
    return render_template("home.html", entries=entries, form=form, user=auth.current_user()["username"])


@web_ui.errorhandler(500)
def handle_internal_error(error):
    flash("Erreur interne du serveur", "error")
    logging.exception(error)
    return redirect(url_for("web_ui.index"))


@web_ui.route("/create", methods=["GET", "POST"])
@auth.login_required(role="admin")
def create_entry():
    form = Form()
    if form.validate_on_submit():
        models.create_entry(form.name.data, form.amount.data, form.category.data)
        return redirect(url_for('web_ui.index'))
    return render_template("home.html", form=form)


@web_ui.route("/update/<uuid:id>", methods=["GET", "POST"])
@auth.login_required(role="admin")
def update_entry(id):
    form = Form()
    entry = models.get_entry(id)
    if not entry:
        flash("Entrée non trouvée.", "danger")
        return redirect(url_for("web_ui.index"))

    if request.method == "GET":
        form.name.data = entry.name
        form.amount.data = entry.amount
        form.category.data = entry.category
        return render_template("update.html", form=form)

    if form.validate_on_submit():
        name = form.name.data
        amount = form.amount.data
        category = form.category.data

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Le montant doit être un nombre positif.", "danger")
            else:
                models.update_entry(id, name, amount, category)
                flash("Entrée mise à jour avec succès!", "success")
        except ValueError:
            flash("Le montant doit être un nombre valide.", "danger")

    return redirect(url_for("web_ui.index"))


@web_ui.route("/delete/<uuid:id>", methods=["POST"])
@auth.login_required(role="admin")
def delete_entry(id):
    models.delete_entry(id)
    return redirect(url_for("web_ui.index"))


@web_ui.route("/export", methods=["GET"])
@auth.login_required
def export_entries():
    csv_data = services.export_to_csv()
    return send_file(
        io.BytesIO(csv_data.getvalue().encode('utf-8')),
        download_name="entries.csv",
        as_attachment=True,
        mimetype="text/csv"
    )


@web_ui.route("/import", methods=["POST"])
@auth.login_required(role="admin")
def import_entries():
    if "csv_file" not in request.files:
        return redirect(url_for("web_ui.index"))

    csv_file = request.files["csv_file"]

    if csv_file.filename == "":
        flash("Le fichier sélectionné est vide.", "danger")
        return redirect(url_for("web_ui.index"))

    try:
        csv_content = csv_file.read().decode("utf-8")
        csv_file_stream = io.StringIO(csv_content)

        services.import_from_csv(csv_file_stream)

        flash("Données importées avec succès!", "success")
    except Exception as e:
        flash(f"Erreur lors de l'importation des données : {e}", "danger")
        print(f"Erreur lors de l'importation des données : {e}")

    return redirect(url_for("web_ui.index"))
