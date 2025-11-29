from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import subprocess
import sys


# Register Arial fonts
pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "arialbd.ttf"))




def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)




def print_with_sumatra(pdf_path, copies=1):
    sumatra_path = r"C:\Program Files\SumatraPDF\SumatraPDF.exe"  # adjust if needed

    try:
        subprocess.run([
            sumatra_path,
            "-print-to-default",
            "-print-settings", f"{copies}x",  # e.g., "2x" means 2 copies
            pdf_path
        ], check=True)
        print(f"Sent {copies} copy/copies to the printer.")
    except subprocess.CalledProcessError as e:
        print("Failed to print:", e)




def generate_receipt_pdf(receipt_data, copies=1, notes=""):

    # === Helper for wrapped lines ===
    def draw_wrapped_line(label, value, row, max_width):
        y = body_y - row * line_spacing
        label_x = start_x
        value_x = start_x + label_gap

        c.setFont(label_font, font_size)
        c.drawString(label_x, y, label)

        c.setFont(value_font, font_size)
        words = str(value).split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if pdfmetrics.stringWidth(test_line, value_font, font_size) < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            c.drawString(value_x, y - i * (font_size + 2), line)

        return len(lines) - 1

    # === Create folder & file ===
    output_folder = "Receipts"
    os.makedirs(output_folder, exist_ok=True)
    safe_name = str(receipt_data['received_from']).replace(" ", "_")
    filename = f"Αποδειξη-{receipt_data['number']}-{safe_name}.pdf"
    filepath = os.path.join(output_folder, filename)

    # === Setup PDF ===
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # Logo
    logo_path = resource_path("logo.png")
    try:
        logo = ImageReader(logo_path)
        c.drawImage(logo, x=20*mm, y=height - 55*mm, width=40*mm, preserveAspectRatio=True, mask='auto')
    except:
        c.setFont("Arial", 10)
        c.drawString(20*mm, height - 20*mm, "LOGO PLACEHOLDER")

    # Contact info
    contact_info = [
        "Company Information Placeholder"
    ]
    c.setFont("Arial", 10)
    contact_y = height - 20*mm
    for line in contact_info:
        c.drawRightString(width - 20*mm, contact_y, line)
        contact_y -= 5*mm

    # Title
    c.setFont("Arial-Bold", 16)
    c.drawCentredString(width / 2, height - 65*mm, "ΑΠΟΔΕΙΞΗ ΕΙΣΠΡΑΞΗΣ")

    # Body
    label_font = "Arial"
    value_font = "Arial-Bold"
    font_size = 12
    body_y = height - 90*mm
    line_spacing = 10*mm
    start_x = 30*mm
    label_gap = 50*mm

    def draw_line(label, value, row):
        y = body_y - row * line_spacing
        c.setFont(label_font, font_size)
        c.drawString(start_x, y, label)
        c.setFont(value_font, font_size)
        c.drawString(start_x + label_gap, y, str(value))

    row = 0
    draw_line("Αρ. Απόδειξης:", receipt_data['number'], row); row += 1
    draw_line("Ημερομηνία:", receipt_data['date'], row); row += 1
    extra_rows = draw_wrapped_line("Εισπράξαμε Από:", receipt_data['received_from'], row, 120*mm)
    row += 1 + extra_rows

    # Payment method
    if "payment_method" in receipt_data:
        draw_line("Τρόπος Πληρωμής:", receipt_data['payment_method'], row)
        row += 1
        if str(receipt_data['payment_method']).strip().lower() == "επιταγή":
            if "check_number" in receipt_data and str(receipt_data["check_number"]).strip():
                draw_line("Αρ. Επιταγής:", receipt_data["check_number"], row)
                row += 1

    draw_line("Το Ποσό των:", "€" + str(receipt_data['amount']), row); row += 1
    extra_rows = draw_wrapped_line("Ολογράφως:", receipt_data['written_amount'], row, 120*mm)
    row += 1 + extra_rows

    # === Signature (right under receipt details) ===
    ypos_sig = body_y - row * line_spacing - 60
    c.setFont("Arial", 12)
    c.drawRightString(width - 30*mm, ypos_sig, "Name Placeholder")
    c.drawRightString(width - 30*mm, ypos_sig + 20, "Υπογραφή")

    # === Notes (below signature, wrapped) ===
    if notes.strip():
        notes_font = "Arial"
        notes_font_size = 11
        max_width = 150 * mm
        line_height = notes_font_size + 2  # spacing in points

        # wrap text properly
        words = notes.split()
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if pdfmetrics.stringWidth(test, notes_font, notes_font_size) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        # draw lines starting below signature
        notes_start_y = ypos_sig - 15
        c.setFont("Arial-Bold", notes_font_size)
        c.drawString(start_x, notes_start_y, "Σημειώσεις:")
        c.setFont(notes_font, notes_font_size)
        for i, line in enumerate(lines):
            c.drawString(start_x + 10*mm, notes_start_y - 15 - i * line_height, line)

    c.save()

    try:
        print_with_sumatra(filepath, copies=copies)
    except:
        print("[ERROR] Failed to print")









