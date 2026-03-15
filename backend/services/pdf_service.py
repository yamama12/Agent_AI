from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from datetime import date
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
import os


# ATTESTATION D'INSCRIPTION
def generate_attestationInscri_pdf(data: dict, output_path: str = None) -> str:

    pdfmetrics.registerFont(TTFont('Amiri', 'assets/Amiri-Regular.ttf'))

    if output_path:
        dirpath = os.path.dirname(output_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        filename = os.path.basename(output_path)
    else:
        os.makedirs("files", exist_ok=True)
        filename = f"attestation_inscription_{data['Matricule']}.pdf"
        output_path = f"files/{filename}"

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # COULEURS
    PRIMARY_COLOR = HexColor('#1a365d')
    SECONDARY_COLOR = HexColor("#24282f")
    ACCENT_COLOR = HexColor('#d4af37')
    LIGHT_BG = HexColor('#f8fafc')

    # FOND
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # EN-TÊTE
    c.setFillColor(PRIMARY_COLOR)
    c.rect(0, height - 4*cm, width, 4*cm, fill=1, stroke=0)
    
    logo_image = "assets/logo_ise.png"
    if os.path.exists(logo_image):
        c.drawImage(
            logo_image,
            x=0.5 * cm,
            y=height - 3.5 * cm,
            width=6 * cm,
            height=3 * cm,
            preserveAspectRatio=True,
            mask='auto'
        )
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(6 * cm, height - 2 * cm, "INTERNATIONAL SCHOOL OF ELITE")
    c.setFont("Helvetica", 10)
    c.drawString(6 * cm, height - 2.5 * cm, "Nabeul - Tunisia")
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(6 * cm, height - 3 * cm, "Collège & Lycée ISE")

    # TEXTE ARABE 
    arabic_lines = [
        "الجمهورية التونسية",
        "وزارة التربية",
        "المندوبية الجهوية للتربية بنابل",
        "المدرسة الدولية للنخبة"
    ]

    c.setFont("Amiri", 11)
    c.setFillColorRGB(1, 1, 1)  

    y_ar = height - 1.5 * cm

    for line in arabic_lines:
        reshaped = arabic_reshaper.reshape(line)
        bidi_text = get_display(reshaped)
        c.drawRightString(width - 1 * cm, y_ar, bidi_text)
        y_ar -= 0.6 * cm

    # TITRE
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(PRIMARY_COLOR)
    c.drawCentredString(width / 2, height - 6 * cm, "ATTESTATION D'INSCRIPTION")
    
    c.setStrokeColor(ACCENT_COLOR)
    c.setLineWidth(1.5)
    c.line(width/2 - 4*cm, height - 6.4*cm, width/2 + 4*cm, height - 6.4*cm)
    
    c.setFont("Helvetica-Oblique", 12)
    c.setFillColor(SECONDARY_COLOR)
    c.drawCentredString(width / 2, height - 7 * cm, 
                       f"Année Scolaire {data['AnneeScolaire']}")

    # CONTENU
    y = height - 9 * cm
    
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor('#393d45'))
    
    intro_text = c.beginText(3.5 * cm, y)
    intro_text.setLeading(18)
    intro_text.setFont("Helvetica", 12)
    
    intro_text.textLine("Je soussignée, Mme Balkis Zrelli, Directrice du Collège et Lycée ISE,")
    intro_text.textLine("atteste que :")
    
    c.drawText(intro_text)
    
    y -= 2 * cm
    
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, f"{data['NomFr']} {data['PrenomFr']}")
    c.drawCentredString(width / 2, y - 1 * cm, f"Né(e) le : {data['DateNaissance']} à {data['LieuNaissance']}")
    
    y -= 2 * cm
    
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#393d45"))
    
    inscription_text = c.beginText(3.5 * cm, y)
    inscription_text.setLeading(18)
    inscription_text.setFont("Helvetica", 12)
    
    inscription_text.textLine(f"est inscrit(e) dans la classe {data['Classe']} pour l'année scolaire {data['AnneeScolaire']}.")
    
    c.drawText(inscription_text)

    # SIGNATURE ET CACHET
    y_signature = y - 4 * cm
    
    # Date 
    c.setFont("Helvetica", 11)
    c.setFillColor(SECONDARY_COLOR)
    c.drawString(3 * cm, y_signature, 
                f"Fait à Nabeul, le {date.today().strftime('%d/%m/%Y')}")
    
    # Ligne de signature 
    signature_line_y = y_signature - 2 * cm
    c.setStrokeColor(ACCENT_COLOR)
    c.setLineWidth(0.8)
    c.line(width/2 - 4*cm, signature_line_y, width/2 + 4*cm, signature_line_y)
    
    # Texte "Signature et Cachet" centré
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(PRIMARY_COLOR)
    c.drawCentredString(width/2, signature_line_y - 0.5*cm, "Signature et Cachet")
        
    # PIED DE PAGE
    c.setFillColor(PRIMARY_COLOR)
    c.rect(0, 0, width, 1.5*cm, fill=1, stroke=0)
    
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(width/2, 0.8*cm, "INTERNATIONAL SCHOOL OF ELITE - Avenue Mohamed V, Nabeul 8000, Tunisia")
    c.drawCentredString(width/2, 0.3*cm, "Tél: (+216) 99 555 222 • Email: contact@ise-college-lycee.com • www.ise-college-lycee.com")

    c.save()
    return filename


# ATTESTATION DE PRÉSENCE 
def generate_attestationPresence_pdf(data: dict, output_path: str = None) -> str:
        
    pdfmetrics.registerFont(TTFont('Amiri', 'assets/Amiri-Regular.ttf'))

    if output_path:
        dirpath = os.path.dirname(output_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        filename = os.path.basename(output_path)
    else:
        os.makedirs("files", exist_ok=True)
        filename = f"attestation_presence_{data['Matricule']}.pdf"
        output_path = f"files/{filename}"

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # COULEURS
    PRIMARY_COLOR = HexColor('#1a365d')
    SECONDARY_COLOR = HexColor("#24282f")
    ACCENT_COLOR = HexColor('#d4af37')
    LIGHT_BG = HexColor('#f8fafc')

    # FOND
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # EN-TÊTE
    c.setFillColor(PRIMARY_COLOR)
    c.rect(0, height - 4*cm, width, 4*cm, fill=1, stroke=0)
    
    logo_image = "assets/logo_ise.png"
    if os.path.exists(logo_image):
        c.drawImage(
            logo_image,
            x=0.5 * cm,
            y=height - 3.5 * cm,
            width=6 * cm,
            height=3 * cm,
            preserveAspectRatio=True,
            mask='auto'
        )
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(6 * cm, height - 2 * cm, "INTERNATIONAL SCHOOL OF ELITE")
    c.setFont("Helvetica", 10)
    c.drawString(6 * cm, height - 2.5 * cm, "Nabeul - Tunisia")
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(6 * cm, height - 3 * cm, "Collège & Lycée ISE")

    # TEXTE ARABE
    arabic_lines = [
        "الجمهورية التونسية",
        "وزارة التربية",
        "المندوبية الجهوية للتربية بنابل",
        "المدرسة الدولية للنخبة"
    ]

    c.setFont("Amiri", 11)
    c.setFillColorRGB(1, 1, 1)  

    y_ar = height - 1.5 * cm

    for line in arabic_lines:
        reshaped = arabic_reshaper.reshape(line)
        bidi_text = get_display(reshaped)
        c.drawRightString(width - 1 * cm, y_ar, bidi_text)
        y_ar -= 0.6 * cm

    # TITRE
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(PRIMARY_COLOR)
    c.drawCentredString(width / 2, height - 6 * cm, "ATTESTATION DE PRÉSENCE")
    
    c.setStrokeColor(ACCENT_COLOR)
    c.setLineWidth(1.5)
    c.line(width/2 - 4*cm, height - 6.4*cm, width/2 + 4*cm, height - 6.4*cm)
    
    c.setFont("Helvetica-Oblique", 12)
    c.setFillColor(SECONDARY_COLOR)
    c.drawCentredString(width / 2, height - 7 * cm, 
                       f"Année Scolaire {data['AnneeScolaire']}")

    # CONTENU
    y = height - 9 * cm
    
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor('#393d45'))
    
    intro_text = c.beginText(3.5 * cm, y)
    intro_text.setLeading(18)
    intro_text.setFont("Helvetica", 12)
    
    intro_text.textLine("Je soussignée, Mme Balkis Zrelli, Directrice du Collège et Lycée ISE,")
    intro_text.textLine("atteste que :")
    
    c.drawText(intro_text)
    
    y -= 2 * cm
    
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, f"{data['NomFr']} {data['PrenomFr']}")
    c.drawCentredString(width / 2, y - 1 * cm, f"Né(e) le : {data['DateNaissance']} à {data['LieuNaissance']}")
    
    y -= 2.5 * cm
    
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor("#393d45"))
    
    max_width = 14 * cm
    x_start = 3.5 * cm
    line_height = 16  
    
    phrase1 = f"est régulièrement inscrit(e) dans notre établissement et suit ses études au sein de la classe de {data['Classe']} pour l'année scolaire {data['AnneeScolaire']}."
    
    phrase2 = "Cette attestation est délivrée à la demande de l'intéressé(e) pour servir et valoir ce que de droit."

    def wrap_text(text, font_name, font_size, max_width_points):
        """Découpe un texte en plusieurs lignes selon la largeur max"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            test_width = pdfmetrics.stringWidth(test_line, font_name, font_size)
            
            if test_width > max_width_points:
                # Retirer le dernier mot et ajouter la ligne
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        
        # Ajouter la dernière ligne
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    lines1 = wrap_text(phrase1, "Helvetica", 12, max_width)
    lines2 = wrap_text(phrase2, "Helvetica", 12, max_width)
    
    presence_text = c.beginText(x_start, y)
    presence_text.setFont("Helvetica", 12)
    presence_text.setLeading(line_height)
    
    # Ajouter toutes les lignes de la première phrase
    for line in lines1:
        presence_text.textLine(line)
    
    # Ajouter un espace entre les deux phrases
    presence_text.moveCursor(0, 8)
    
    # Ajouter toutes les lignes de la deuxième phrase
    for line in lines2:
        presence_text.textLine(line)
    
    c.drawText(presence_text)

    # SIGNATURE ET CACHET
    total_lines = len(lines1) + len(lines2)
    y_signature = y - (total_lines * line_height) - 3 * cm
    
    # Date 
    c.setFont("Helvetica", 11)
    c.setFillColor(SECONDARY_COLOR)
    c.drawString(3 * cm, y_signature, 
                f"Fait à Nabeul, le {date.today().strftime('%d/%m/%Y')}")
    
    # Ligne de signature
    signature_line_y = y_signature - 2 * cm
    c.setStrokeColor(ACCENT_COLOR)
    c.setLineWidth(0.8)
    c.line(width/2 - 4*cm, signature_line_y, width/2 + 4*cm, signature_line_y)
    
    # Texte "Signature et Cachet" 
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(PRIMARY_COLOR)
    c.drawCentredString(width/2, signature_line_y - 0.5*cm, "Signature et Cachet")
        
    # PIED DE PAGE
    c.setFillColor(PRIMARY_COLOR)
    c.rect(0, 0, width, 1.5*cm, fill=1, stroke=0)
    
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(width/2, 0.8*cm, "INTERNATIONAL SCHOOL OF ELITE - Avenue Mohamed V, Nabeul 8000, Tunisia")
    c.drawCentredString(width/2, 0.3*cm, "Tél: (+216) 99 555 222 • Email: contact@ise-college-lycee.com • www.ise-college-lycee.com")

    c.save()
    return filename
