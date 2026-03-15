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
)

matplotlib.use("Agg")


# Repartition des eleves par classe pour l'annee scolaire en cours
def generate_students_by_class_chart():
    data = get_students_count_by_classe()

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
def generate_students_by_class_chart_file():
    buffer = generate_students_by_class_chart()

    graphic_name = f"students_by_class_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)

    with open(path, "wb") as f:
        f.write(buffer.getvalue())

    return graphic_name


# Repartition des eleves par sexe pour l'annee scolaire en cours
def generate_students_by_gender_chart():
    data = get_students_count_by_gender()

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
def generate_students_by_gender_chart_file():
    buffer = generate_students_by_gender_chart()

    graphic_name = f"students_by_gender_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)

    with open(path, "wb") as f:
        f.write(buffer.getvalue())

    return graphic_name


def generate_students_by_locality_chart():
    data = get_students_count_by_locality()

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


def generate_students_by_locality_chart_file():
    buffer = generate_students_by_locality_chart()

    graphic_name = f"students_by_locality_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join("statistics", graphic_name)

    with open(path, "wb") as f:
        f.write(buffer.getvalue())

    return graphic_name

