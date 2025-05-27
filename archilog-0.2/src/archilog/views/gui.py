from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import archilog.models as models
from src.archilog import services
import io

web_ui = Blueprint('web_ui', __name__)

@web_ui.route("/")
def index():
    entries = models.get_all_entries()
    return render_template("home.html", entries=entries)

@web_ui.route("/create", methods=["GET", "POST"])
def create_entry():
    if request.method == "POST":
        name = request.form["name"]
        amount = request.form["amount"]
        category = request.form.get("category", None)

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Le montant doit être un nombre positif.", "danger")
            else:
                models.create_entry(name, amount, category)
                flash("Entrée ajoutée avec succès!", "success")
        except ValueError:
            flash("Le montant doit être un nombre valide.", "danger")

        return redirect(url_for("web_ui.index"))

    return render_template("home.html")


@web_ui.route("/delete/<uuid:id>", methods=["POST"])
def delete_entry(id):
    try:
        models.delete_entry(id)
        flash("Entrée supprimée avec succès!", "success")
    except Exception as e:
        flash(f"Erreur: {e}", "danger")
    return redirect(url_for("web_ui.index"))

@web_ui.route("/update/<uuid:id>", methods=["POST"])
def update_entry(id):
    entry = models.get_entry(id)
    if not entry:
        flash("Entrée non trouvée.", "danger")
        return redirect(url_for("web_ui.index"))
    
    name = request.form["name"]
    amount = request.form["amount"]
    category = request.form.get("category", None)

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


@web_ui.route("/export", methods=["GET"])
def export_entries():
    csv_data = services.export_to_csv()
    return send_file(
        io.BytesIO(csv_data.getvalue().encode('utf-8')),
        download_name="entries.csv",
        as_attachment=True,
        mimetype="text/csv"
    )


@web_ui.route("/import", methods=["POST"])
def import_entries():
    if "csv_file" not in request.files:
        flash("Aucun fichier CSV fourni.", "danger")
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
