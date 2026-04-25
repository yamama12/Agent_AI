import io
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



from database.eleve_repository import (
    get_students_count_by_classe,
    get_students_count_by_gender,
    get_students_count_by_locality,
    get_average_grades_by_class,
    get_average_grades_by_subject,
    get_grades_distribution_by_trimestre,
    get_top_students_by_class,
)

matplotlib.use("Agg")
os.makedirs("statistics", exist_ok=True)


GRAPH_LABELS = {
    "students_by_class": "repartition des eleves par classe",
    "students_by_gender": "repartition des eleves par sexe",
    "students_by_locality": "repartition des eleves par localite",
    "average_grades_by_class": "moyennes des notes par classe",
    "average_grades_by_subject": "moyennes des notes par matiere",
    "grades_distribution": "distribution des notes par trimestre",
    "top_students_by_class": "meilleurs eleves par classe",
}


def _build_distribution_summary(data, label_key, note=None):
    items = []
    for row in data or []:
        label = str(row.get(label_key) or "Non specifie").strip() or "Non specifie"
        value = int(row.get("NombreEleves") or 0)
        items.append({"label": label, "value": value})

    items.sort(key=lambda item: (-item["value"], item["label"]))
    total = sum(item["value"] for item in items)

    for item in items:
        share = (item["value"] / total * 100) if total else 0
        item["share"] = round(share, 2)

    summary = {
        "total": total,
        "category_count": len(items),
        "items": items,
        "top_items": items[:3],
        "bottom_item": items[-1] if items else None,
    }
    if note:
        summary["note"] = note
    return summary


def _build_best_students_by_class(data):
    best_by_class = {}
    for row in data or []:
        classe = str(row.get("classe") or "Non specifie").strip() or "Non specifie"
        nom = str(row.get("nom_eleve") or "Non specifie").strip() or "Non specifie"
        moyenne = float(row.get("moyenne") or 0)

        current = best_by_class.get(classe)
        if current is None or moyenne > current["moyenne"]:
            best_by_class[classe] = {
                "nom": nom,
                "moyenne": round(moyenne, 2),
                "classe": classe,
            }

    best_students = list(best_by_class.values())
    best_students.sort(key=lambda item: (-item["moyenne"], item["classe"]))
    return best_students


def _build_top_students_summary(data):
    best_students = _build_best_students_by_class(data)
    items = [
        {
            "label": student["classe"],
            "value": student["moyenne"],
            "student": student["nom"],
        }
        for student in best_students
    ]
    average_value = (
        round(
            sum(student["moyenne"] for student in best_students) / len(best_students),
            2,
        )
        if best_students
        else 0
    )

    return {
        "total": len(best_students),
        "category_count": len(best_students),
        "items": items,
        "top_items": items[:3],
        "bottom_item": items[-1] if items else None,
        "average_value": average_value,
        "note": "Chaque valeur correspond a la moyenne du meilleur eleve de la classe.",
    }


# Repartition des eleves par classe pour l'annee scolaire en cours
def generate_students_by_class_chart(data=None):
    data = data if data is not None else get_students_count_by_classe()

    classes = [row["classe"] for row in data]
    totals = [row["NombreEleves"] for row in data]

    total_eleves = sum(totals)

    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(totals)))

    bars = ax.bar(
        classes,
        totals,
        color=colors,
        edgecolor="white",
        linewidth=1.5,
        alpha=0.9,
        width=0.7,
    )

    for bar, value in zip(bars, totals):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.5,
            f"{value}",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=11,
        )

    ax.set_xlabel("Classe", fontsize=13, fontweight="bold", labelpad=10)
    ax.set_ylabel("Nombre d'eleves", fontsize=13, fontweight="bold", labelpad=10)
    ax.set_title(
        f"Répartition des élèves par classe\nAnnée scolaire : 2025-2026\nTotal: {total_eleves} élèves",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )

    plt.xticks(rotation=45, ha="right", fontsize=11)
    plt.yticks(fontsize=11)

    ax.yaxis.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_alpha(0.3)
    ax.spines["bottom"].set_alpha(0.3)

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()

    buffer.seek(0)
    return buffer


# Sauvegarde le graphe dans le dossier "statistics"
def generate_students_by_class_chart_file(data=None):
    buffer = generate_students_by_class_chart(data=data)

    graphic_name = f"students_by_class_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)

    with open(path, "wb") as f:
        f.write(buffer.getvalue())

    return graphic_name


# Repartition des eleves par sexe pour l'annee scolaire en cours
def generate_students_by_gender_chart(data=None):
    data = data if data is not None else get_students_count_by_gender()

    labels = [row["sexe"] for row in data]
    values = [row["NombreEleves"] for row in data]
    total_eleves = sum(values)

    # Style minimaliste
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # Couleurs : rouge et bleu marine
    colors = ["#DC143C", "#000080"]  # Crimson red et Navy blue
    
    # Création du graphique simple et élégant
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct=lambda pct: f"{int(pct * total_eleves / 100)}\n({pct:.1f}%)",
        startangle=90,
        colors=colors,
        wedgeprops={
            "edgecolor": "white",
            "linewidth": 2,
        },
        textprops={"fontsize": 11, "fontweight": "bold"},
    )
    
    # Personnalisation des textes
    for i, (text, autotext) in enumerate(zip(texts, autotexts)):
        text.set_fontsize(12)
        text.set_fontweight("bold")
        text.set_color(colors[i])
        
        autotext.set_fontsize(10)
        autotext.set_color("white")
        autotext.set_fontweight("bold")
        autotext.set_bbox(dict(
            facecolor=colors[i],
            alpha=0.8,
            edgecolor='none',
            pad=2,
            boxstyle="round,pad=0.3"
        ))
    
    # Titre
    ax.set_title(
        f"Répartition des élèves par classe\nAnnée scolaire : 2025-2026",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    
    # Détails en bas
    details_text = ""
    for label, value in zip(labels, values):
        details_text += f"{label}: {value} élèves  "
    
    ax.text(
        0.5, -0.15,
        details_text,
        transform=ax.transAxes,
        ha='center',
        fontsize=11,
        color='#555555',
        weight='500'
    )
    
    # Total
    ax.text(
        0.5, -0.22,
        f"Total: {total_eleves} élèves",
        transform=ax.transAxes,
        ha='center',
        fontsize=12,
        color='#000080',
        weight='bold'
    )
    
    ax.axis("equal")
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(
        buffer, 
        format="png", 
        dpi=300, 
        bbox_inches="tight",
        facecolor='white'
    )
    plt.close()
    buffer.seek(0)
    return buffer


# Sauvegarde le graphe de repartition par sexe dans le dossier "statistics"
def generate_students_by_gender_chart_file(data=None):
    buffer = generate_students_by_gender_chart(data=data)

    graphic_name = f"students_by_gender_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)

    with open(path, "wb") as f:
        f.write(buffer.getvalue())

    return graphic_name


def generate_students_by_locality_chart(data=None):
    data = data if data is not None else get_students_count_by_locality()

    localites = [row["localite"] for row in data]
    totals = [row["NombreEleves"] for row in data]
    total_eleves = sum(totals)

    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(13, 7))

    colors = plt.cm.Greens(np.linspace(0.35, 0.9, len(totals)))
    bars = ax.barh(
        localites,
        totals,
        color=colors,
        edgecolor="white",
        linewidth=1.2,
        alpha=0.95,
    )

    for bar, value in zip(bars, totals):
        ax.text(
            value + 0.3,
            bar.get_y() + bar.get_height() / 2.0,
            str(value),
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
        )

    ax.invert_yaxis()
    ax.set_xlabel("Nombre d'élèves", fontsize=12, fontweight="bold")
    ax.set_ylabel("Localité", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Répartition des élèves par localité (Top 15)\nTotal: {total_eleves} élèves",
        fontsize=15,
        fontweight="bold",
        pad=16,
    )
    ax.xaxis.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    buffer.seek(0)
    return buffer


def generate_students_by_locality_chart_file(data=None):
    buffer = generate_students_by_locality_chart(data=data)

    graphic_name = f"students_by_locality_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)

    with open(path, "wb") as f:
        f.write(buffer.getvalue())

    return graphic_name




def generate_average_grades_by_class_chart(data=None):
    """Génère un graphique des moyennes par classe"""
    data = data if data is not None else get_average_grades_by_class()
    
    classes = [row["classe"] for row in data]
    moyennes = [float(row["MoyenneGenerale"]) if row["MoyenneGenerale"] else 0 for row in data]
    
    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(moyennes)))
    
    bars = ax.bar(classes, moyennes, color=colors, edgecolor="white", linewidth=1.5)
    
    # Ajouter une ligne de moyenne générale
    moyenne_globale = sum(moyennes) / len(moyennes) if moyennes else 0
    ax.axhline(y=moyenne_globale, color='red', linestyle='--', alpha=0.7, 
               label=f'Moyenne générale: {moyenne_globale:.2f}/20')
    
    for bar, value in zip(bars, moyennes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, height + 0.1,
                f"{value:.1f}", ha="center", va="bottom", fontweight="bold", fontsize=10)
    
    ax.set_xlabel("Classe", fontsize=13, fontweight="bold")
    ax.set_ylabel("Moyenne (/20)", fontsize=13, fontweight="bold")
    ax.set_title("Moyennes des notes par classe - Trimestre 1\nAnnée scolaire 2025-2026", 
                 fontsize=16, fontweight="bold", pad=20)
    ax.set_ylim(0, 20)
    ax.legend()
    
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    buffer.seek(0)
    return buffer


""" def generate_average_grades_by_subject_chart(data=None):
    data = data if data is not None else get_average_grades_by_subject()
    
    matieres = [row["matiere"] for row in data]
    moyennes = [float(row["Moyenne"]) if row["Moyenne"] else 0 for row in data]
    
    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = plt.cm.Purples(np.linspace(0.4, 0.9, len(moyennes)))
    
    bars = ax.barh(matieres, moyennes, color=colors, edgecolor="white", linewidth=1.2)
    
    for bar, value in zip(bars, moyennes):
        ax.text(value + 0.1, bar.get_y() + bar.get_height() / 2.0,
                f"{value:.1f}", va="center", fontsize=10, fontweight="bold")
    
    ax.set_xlabel("Moyenne (/20)", fontsize=13, fontweight="bold")
    ax.set_ylabel("Matière", fontsize=13, fontweight="bold")
    ax.set_title("Moyennes des notes par matière - Trimestre 1\nAnnée scolaire 2025-2026", 
                 fontsize=16, fontweight="bold", pad=20)
    ax.set_xlim(0, 20)
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    buffer.seek(0)
    return buffer
 """

def generate_grades_distribution_chart(data=None):
    """Génère un graphique de distribution des notes par trimestre"""
    data = data if data is not None else get_grades_distribution_by_trimestre()
    
    trimestres = [row["trimestre"] for row in data]
    moyennes = [float(row["MoyenneGenerale"]) if row["MoyenneGenerale"] else 0 for row in data]
    notes_min = [float(row["NoteMin"]) if row["NoteMin"] else 0 for row in data]
    notes_max = [float(row["NoteMax"]) if row["NoteMax"] else 0 for row in data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(trimestres))
    width = 0.35
    
    # Graphique en barres avec barres d'erreur pour min/max
    bars = ax.bar(x, moyennes, width, color='steelblue', edgecolor='white', linewidth=1.5,
                  yerr=[(m - min_val) for m, min_val in zip(moyennes, notes_min)],
                  capsize=5, alpha=0.8)
    
    # Ajouter les valeurs
    for i, (bar, moy, min_val, max_val) in enumerate(zip(bars, moyennes, notes_min, notes_max)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, height + 0.5,
                f"{moy:.1f}", ha="center", va="bottom", fontweight="bold", fontsize=11)
        ax.text(bar.get_x() + bar.get_width() / 2.0, min_val - 0.5,
                f"Min: {min_val:.1f}", ha="center", va="top", fontsize=9, alpha=0.7)
        ax.text(bar.get_x() + bar.get_width() / 2.0, max_val + 0.5,
                f"Max: {max_val:.1f}", ha="center", va="bottom", fontsize=9, alpha=0.7)
    
    ax.set_xlabel("Trimestre", fontsize=13, fontweight="bold")
    ax.set_ylabel("Moyenne (/20)", fontsize=13, fontweight="bold")
    ax.set_title("Distribution des notes par trimestre\nAnnée scolaire 2025-2026", 
                 fontsize=16, fontweight="bold", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(trimestres)
    ax.set_ylim(0, 20)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    buffer.seek(0)
    return buffer

# Changer le chart en tableau des meilleurs élèves par classe
def generate_top_students_chart(data=None):
    """
    Génère un tableau PNG des meilleurs élèves par classe
    """

    data = data if data is not None else get_top_students_by_class()

    # Cas vide
    if not data:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(
            0.5, 0.5,
            "Aucune donnée disponible.\nVeuillez saisir les notes du trimestre 1.",
            ha="center", va="center", fontsize=14, fontweight="bold"
        )
        ax.axis("off")

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
        plt.close()
        buffer.seek(0)
        return buffer

    # 🔥 Regrouper : meilleur élève par classe
    best_by_class = {}
    for row in data:
        classe = row["classe"]
        moyenne = float(row["moyenne"]) if row["moyenne"] else 0
        nom = row["nom_eleve"]

        if classe not in best_by_class or moyenne > best_by_class[classe]["moyenne"]:
            best_by_class[classe] = {
                "classe": classe,
                "nom": nom,
                "moyenne": moyenne
            }

    # Trier
    best_students = list(best_by_class.values())
    best_students.sort(key=lambda x: x["moyenne"], reverse=True)

    # 🔥 Construire le tableau (ordre modifié)
    table_data = []
    for i, s in enumerate(best_students, 1):
        table_data.append([
            s["nom"],           # 1. Élève
            s["classe"],        # 2. Classe
            f"{s['moyenne']:.2f}",  # 3. Moyenne
            i                   # 4. Classement
        ])

    columns = ["Élève", "Classe", "Moyenne", "Classement"]

    # 🔥 Création figure
    fig_height = max(6, len(table_data) * 0.4)
    fig, ax = plt.subplots(figsize=(12, fig_height))

    ax.axis("off")

    # Création du tableau
    table = ax.table(
        cellText=table_data,
        colLabels=columns,
        loc="center",
        cellLoc="center"
    )

    # 🔥 STYLE
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    # Header style
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#2E86C1')  # bleu
        else:
            if row % 2 == 0:
                cell.set_facecolor('#F2F3F4')  # gris clair

    # 🔥 Titre
    plt.title(
        f"Meilleurs élèves par classe ({len(table_data)} classes)\nTrimestre 1 - 2025/2026",
        fontsize=14,
        fontweight="bold",
        pad=20
    )

    # 🔥 Sauvegarde
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
    plt.close()
    buffer.seek(0)

    return buffer


# Fonctions de sauvegarde des graphiques
def generate_average_grades_by_class_chart_file(data=None):
    buffer = generate_average_grades_by_class_chart(data=data)
    graphic_name = f"avg_grades_class_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)
    with open(path, "wb") as f:
        f.write(buffer.getvalue())
    return graphic_name


""" def generate_average_grades_by_subject_chart_file(data=None):
    buffer = generate_average_grades_by_subject_chart(data=data)
    graphic_name = f"avg_grades_subject_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)
    with open(path, "wb") as f:
        f.write(buffer.getvalue())
    return graphic_name """


def generate_grades_distribution_chart_file(data=None):
    buffer = generate_grades_distribution_chart(data=data)
    graphic_name = f"grades_distribution_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)
    with open(path, "wb") as f:
        f.write(buffer.getvalue())
    return graphic_name


def generate_top_students_chart_file(data=None):
    buffer = generate_top_students_chart(data=data)
    graphic_name = f"top_students_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)
    with open(path, "wb") as f:
        f.write(buffer.getvalue())


# Mettre à jour la fonction generate_graph_bundle
def generate_graph_bundle(graph_type: str):
    if graph_type == "students_by_class":
        data = get_students_count_by_classe()
        return {
            "graphic_name": generate_students_by_class_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                **_build_distribution_summary(data, "classe"),
            },
        }

    if graph_type == "students_by_gender":
        data = get_students_count_by_gender()
        return {
            "graphic_name": generate_students_by_gender_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                **_build_distribution_summary(data, "sexe"),
            },
        }

    if graph_type == "students_by_locality":
        data = get_students_count_by_locality()
        return {
            "graphic_name": generate_students_by_locality_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                **_build_distribution_summary(
                    data,
                    "localite",
                    note="Top 15 localites avec au moins 5 eleves",
                ),
            },
        }
    
    # Nouveaux types de graphiques
    if graph_type == "average_grades_by_class":
        data = get_average_grades_by_class()
        items = [{"label": row["classe"], "value": float(row["MoyenneGenerale"])} for row in data]
        return {
            "graphic_name": generate_average_grades_by_class_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                "items": items,
                "total": len(data),
                "category_count": len(data),
                "note": "Moyennes sur 20"
            },
        }
    
    if graph_type == "average_grades_by_subject":
        data = get_average_grades_by_subject()
        items = [{"label": row["matiere"], "value": float(row["Moyenne"])} for row in data]
        return {
            "graphic_name": generate_average_grades_by_subject_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                "items": items,
                "total": len(data),
                "category_count": len(data),
                "note": "Moyennes sur 20"
            },
        }
    
    if graph_type == "grades_distribution":
        data = get_grades_distribution_by_trimestre()
        items = [{"label": row["trimestre"], "value": float(row["MoyenneGenerale"])} for row in data]
        return {
            "graphic_name": generate_grades_distribution_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                "items": items,
                "total": len(data),
                "category_count": len(data),
                "note": "Distribution des moyennes avec min et max"
            },
        }
    
    if graph_type == "top_students_by_class":
        data = get_top_students_by_class()
        # Compter le nombre d'élèves par classe
        classes = {}
        for row in data:
            classe = row["classe"]
            classes[classe] = classes.get(classe, 0) + 1
        
        return {
            "graphic_name": generate_top_students_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                "items": [{"label": f"{classe} ({count} élèves)", "value": count} 
                         for classe, count in classes.items()],
                "total": len(data),
                "category_count": len(classes),
                "note": f"Top 3 élèves par classe"
            },
        }

    return None


def generate_top_students_chart_file(data=None):
    buffer = generate_top_students_chart(data=data)
    graphic_name = f"top_students_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)
    with open(path, "wb") as f:
        f.write(buffer.getvalue())
    return graphic_name


def generate_graph_bundle(graph_type: str):
    if graph_type == "students_by_class":
        data = get_students_count_by_classe()
        return {
            "graphic_name": generate_students_by_class_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                **_build_distribution_summary(data, "classe"),
            },
        }

    if graph_type == "students_by_gender":
        data = get_students_count_by_gender()
        return {
            "graphic_name": generate_students_by_gender_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                **_build_distribution_summary(data, "sexe"),
            },
        }

    if graph_type == "students_by_locality":
        data = get_students_count_by_locality()
        return {
            "graphic_name": generate_students_by_locality_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                **_build_distribution_summary(
                    data,
                    "localite",
                    note="Top 15 localites avec au moins 5 eleves",
                ),
            },
        }

    if graph_type == "average_grades_by_class":
        data = get_average_grades_by_class()
        items = [{"label": row["classe"], "value": float(row["MoyenneGenerale"])} for row in data]
        return {
            "graphic_name": generate_average_grades_by_class_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                "items": items,
                "total": len(data),
                "category_count": len(data),
                "note": "Moyennes sur 20",
            },
        }

    if graph_type == "average_grades_by_subject":
        data = get_average_grades_by_subject()
        items = [{"label": row["matiere"], "value": float(row["Moyenne"])} for row in data]
        return {
            "graphic_name": generate_average_grades_by_subject_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                "items": items,
                "total": len(data),
                "category_count": len(data),
                "note": "Moyennes sur 20",
            },
        }

    if graph_type == "grades_distribution":
        data = get_grades_distribution_by_trimestre()
        items = [{"label": row["trimestre"], "value": float(row["MoyenneGenerale"])} for row in data]
        return {
            "graphic_name": generate_grades_distribution_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                "items": items,
                "total": len(data),
                "category_count": len(data),
                "note": "Distribution des moyennes avec min et max",
            },
        }

    if graph_type == "top_students_by_class":
        data = get_top_students_by_class()
        return {
            "graphic_name": generate_top_students_chart_file(data=data),
            "summary": {
                "graph_type": graph_type,
                "graph_label": GRAPH_LABELS[graph_type],
                **_build_top_students_summary(data),
            },
        }

    return None
