import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import DateEntry
from ttkbootstrap.dialogs import Messagebox
from datetime import date
from numToText import int_to_en
import json
import os
from createPDF import generate_receipt_pdf
import tkinter as tk


FILENAME = "receipt_number.json"
INVALID_CHARS = set('\\/:*?"<>|')
CUSTOMERS_FILE = "customers.json"

def read_latest_receipt_number():
    if not os.path.exists(FILENAME):
        # File doesn't exist yet, start at 0 or 1
        return 0
    with open(FILENAME, "r") as f:
        data = json.load(f)
        return data.get("latest_receipt_number", 0)

def write_latest_receipt_number(number):
    with open(FILENAME, "w") as f:
        json.dump({"latest_receipt_number": number}, f, indent=4)



def load_customers():
    # If file doesn't exist, create it with empty customers
    if not os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"customers": []}, f, indent=4, ensure_ascii=False)
        return []

    # If file exists, try to load it safely
    try:
        with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("customers", [])
    except (json.JSONDecodeError, ValueError):
        # If the file is empty or corrupted, reset it
        with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"customers": []}, f, indent=4, ensure_ascii=False)
        return []


def save_customers(customers):
    with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"customers": customers}, f, indent=4, ensure_ascii=False)


def show_customer_list():
    customers = load_customers()

    popup = tb.Toplevel(app)
    popup.title("Διαχείριση Πελατών")
    popup.geometry("420x400")

    # --- Listbox ---
    lb = tk.Listbox(popup, font=("Segoe UI", 12))
    lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

    for c in customers:
        lb.insert(tk.END, c)

    # --- Add Customer Frame ---
    add_frame = tb.Frame(popup)
    add_frame.pack(fill=X, padx=10, pady=10)

    add_entry = tb.Entry(add_frame, font=("Segoe UI", 12))
    add_entry.pack(side=LEFT, fill=X, expand=True, padx=5)

    def add_customer():
        new_name = add_entry.get().strip()
        if not new_name:
            return

        # Check for invalid characters
        for char in new_name:
            if char in INVALID_CHARS:
                Messagebox.show_warning(
                    "Μη έγκυρος χαρακτήρας",
                    f"Ο χαρακτήρας '{char}' δεν επιτρέπεται στο όνομα του πελάτη."
                )
                return

        if new_name in customers:
            Messagebox.show_warning("Υπάρχει ήδη", "Αυτός ο πελάτης υπάρχει ήδη.")
            return

        customers.append(new_name)
        customers.sort()
        save_customers(customers)

        lb.delete(0, tk.END)
        for person in customers:
            lb.insert(tk.END, person)

        add_entry.delete(0, tk.END)

    add_btn = tb.Button(add_frame, text="+", bootstyle="success", width=3, command=add_customer)
    add_btn.pack(side=LEFT, padx=5)

    # --- Remove Customer Button ---
    def remove_customer():
        selected_index = lb.curselection()
        if not selected_index:
            return

        name = lb.get(selected_index[0])

        result = Messagebox.okcancel("Διαγραφή", f"Σίγουρα θέλετε να διαγράψετε τον πελάτη:\n\n{name}?")
        if result != "OK":  # Only proceed if OK was pressed
            return

        customers.remove(name)
        save_customers(customers)

        lb.delete(0, tk.END)
        for person in customers:
            lb.insert(tk.END, person)


    remove_btn = tb.Button(popup, text="Διαγραφή Επιλεγμένου", bootstyle="danger", command=remove_customer)
    remove_btn.pack(fill=X, padx=10, pady=(0, 10))

    # --- Double-click select customer ---
    def select_customer(event=None):
        if not lb.curselection():
            return
        selected = lb.get(lb.curselection())
        received_entry.delete(0, tk.END)
        received_entry.insert(0, selected)
        popup.destroy()

    lb.bind("<Double-1>", select_customer)
    popup.bind("<Return>", select_customer)



# Create the main window
app = tb.Window(themename="flatly")
app.title("Απόδειξη Είσπραξης")
app.geometry("1000x900")
app.resizable(True, True)

# Title
title_label = tb.Label(app, text="Δημιουργία Απόδειξης", font=("Segoe UI", 26, "bold"), bootstyle=PRIMARY)
title_label.pack(pady=30)

# Frame for form fields
form_frame = tb.Frame(app, padding=30)
form_frame.pack(fill=BOTH, expand=True, padx=30)

# Received From
received_label = tb.Label(form_frame, text="Εισπράχθηκε από:", font=("Segoe UI", 14))
received_label.grid(row=0, column=0, sticky=E, pady=20, padx=10)
received_entry = tb.Entry(form_frame, font=("Segoe UI", 14), width=40, bootstyle="info")
received_entry.grid(row=0, column=1, sticky=W, padx=10)
customer_btn = tb.Button(form_frame, text="📋", bootstyle="secondary", width=3, command=show_customer_list)
customer_btn.grid(row=0, column=2, sticky=W, padx=5)


# The Sum of
sum_label = tb.Label(form_frame, text="Ποσό (€):", font=("Segoe UI", 14))
sum_label.grid(row=1, column=0, sticky=E, pady=20, padx=10)

amount_frame = tb.Frame(form_frame)
amount_frame.grid(row=1, column=1, sticky=W, padx=10)

sum_entry = tb.Entry(amount_frame, font=("Segoe UI", 14), width=10, bootstyle="info")
sum_entry.pack(side=LEFT)

comma_label = tb.Label(amount_frame, text=",", font=("Segoe UI", 16))
comma_label.pack(side=LEFT, padx=(5, 5))

cent_entry = tb.Entry(amount_frame, font=("Segoe UI", 14), width=5, bootstyle="info")
cent_entry.pack(side=LEFT)
cent_entry.insert(0, "00")

# Date
date_label = tb.Label(form_frame, text="Ημερομηνία:", font=("Segoe UI", 14))
date_label.grid(row=2, column=0, sticky=E, pady=20, padx=10)
date_entry = DateEntry(
    form_frame,
    dateformat="%d/%m/%Y",
    firstweekday=0,
    bootstyle="info",
    width=20
)
date_entry.set_date(date.today())
date_entry.grid(row=2, column=1, sticky=W, padx=10)

# Receipt Number
number_label = tb.Label(form_frame, text="Αρ. Απόδειξης:", font=("Segoe UI", 14))
number_label.grid(row=3, column=0, sticky=E, pady=20, padx=10)

number_entry = tb.Entry(form_frame, font=("Segoe UI", 14), width=10, bootstyle="info")
number_entry.grid(row=3, column=1, sticky=W, pady=20, padx=10)
number_entry.insert(0, read_latest_receipt_number()+1)

# Payment Method
payment_label = tb.Label(form_frame, text="Τρόπος Πληρωμής:", font=("Segoe UI", 14))
payment_label.grid(row=4, column=0, sticky=E, pady=10, padx=10)

payment_var = tb.StringVar(value="Έμβασμα")  # Default to "Έμβασμα"

# Create a custom style to enlarge the dropdown box
style = tb.Style()
style.configure("Custom.TCombobox", padding=10)  # Makes the box taller

# Create the dropdown
payment_combo = tb.Combobox(
    form_frame,
    textvariable=payment_var,
    font=("Segoe UI", 16),  # Increases text size in entry box
    values=["Μετρητά", "Επιταγή", "Έμβασμα"],
    bootstyle="info",
    width=25,
    style="Custom.TCombobox"  # Apply custom style
)
payment_combo.grid(row=4, column=1, sticky=W, padx=10, pady=5)
payment_combo.config(state="normal")  # Allow typing custom value



# Check Number (conditionally shown)
check_label = tb.Label(form_frame, text="Αρ. Επιταγής:", font=("Segoe UI", 14))
check_entry = tb.Entry(form_frame, font=("Segoe UI", 14), width=20, bootstyle="info")

def toggle_check_entry(*args):
    value = payment_var.get().lower().strip()
    if value in ["check", "επιταγή", "επιταγη"]:
        check_label.grid(row=5, column=0, sticky=E, pady=10, padx=10)
        check_entry.grid(row=5, column=1, sticky=W, padx=10)
    else:
        check_label.grid_remove()
        check_entry.grid_remove()

payment_var.trace_add("write", toggle_check_entry)

# Note box

notes_label = tb.Label(form_frame, text="Σημειώσεις:", font=("Segoe UI", 14))
notes_label.grid(row=6, column=0, sticky=NE, pady=10, padx=10)

notes_entry = tk.Text(form_frame, font=("Segoe UI", 14), height=4, width=40)
notes_entry.grid(row=6, column=1, sticky=W, padx=10)




# Generate Button
generate_btn = tb.Button(app, text="Δημιουργία Απόδειξης", bootstyle="success", width=25)
generate_btn.pack(pady=20)
# --- Bottom Left Frame for Copies ---
bottom_frame = tb.Frame(app)
bottom_frame.pack(side=LEFT, anchor=S, padx=20, pady=10)

copies_label = tb.Label(bottom_frame, text="Αντίγραφα:", font=("Segoe UI", 12))
copies_label.pack(side=LEFT)

copies_var = tb.StringVar(value="3")
copies_entry = tb.Entry(bottom_frame, textvariable=copies_var, font=("Segoe UI", 12), width=5, bootstyle="info")
copies_entry.pack(side=LEFT, padx=(5, 0))





def generate_receipt():
    received_text = received_entry.get().strip()
    sum_text = sum_entry.get().strip()
    cents_text = cent_entry.get().strip()
    date_text = date_entry.entry.get().strip()
    number_text = number_entry.get().strip()
    payment_method = payment_var.get().strip()
    check_number = check_entry.get() if payment_method.lower().strip() in ["επιταγή", "επιταγη"] else ""
    copies = copies_var.get().strip()
    notes = notes_entry.get("1.0", "end").strip()


    try:
        sum_value = int(sum_text)
    except ValueError:
        Messagebox.show_error(title="Μη έγκυρη είσοδος", message="Παρακαλώ εισάγετε έγκυρο αριθμό για το ποσό.")
        return

    try:
        cents_value = int(cents_text)
    except ValueError:
        Messagebox.show_error(title="Μη έγκυρη είσοδος", message="Παρακαλώ εισάγετε έγκυρο αριθμό για τα σεντ.")
        return

    try:
        number_value = int(number_text)
    except ValueError:
        Messagebox.show_error(title="Μη έγκυρη είσοδος", message="Παρακαλώ εισάγετε έγκυρο αριθμό για τον αριθμό απόδειξης.")
        return

    if cents_value > 99:
        Messagebox.show_error(title="Μη έγκυρη είσοδος", message="Τα σεντ δεν μπορούν να είναι πάνω από 99.")
        return

    if sum_value > 199999:
        Messagebox.show_error(title="Μη έγκυρη είσοδος", message="Το ποσό είναι υπερβολικά μεγάλο.")
        return

    if not copies.isdigit() or int(copies) < 1:
        Messagebox.show_error(title="Μη έγκυρη είσοδος", message="Ο αριθμός αντιγράφων πρέπει να είναι θετικός αριθμός.")
        return


    write_latest_receipt_number(number_value)

    #Here we create the text
    if cents_value == 0:
        writtenSum = "ΕΥΡΟ " + int_to_en(sum_value) + " ΜΟΝΟ"
    else:
        writtenSum = "ΕΥΡΟ " + int_to_en(sum_value) + " ΚΑΙ " + int_to_en(cents_value) + " ΣΕΝΤ ΜΟΝΟ"


    copies = int(copies)

    
    if payment_method.lower().strip() in ["Επιταγη", "Επιταγή", "επιταγή", "επιταγη"]:
        generate_receipt_pdf({
        'received_from': received_text,
        'amount': str(sum_value) + "," + cents_text,
        'written_amount': writtenSum,
        'date': date_text,
        'number': str(number_value),
        'payment_method': payment_method,
        'check_number': check_number
    }, copies=copies, notes=notes)
    else:
        generate_receipt_pdf({
        'received_from': received_text,
        'amount': str(sum_value) + "," + cents_text,
        'written_amount': writtenSum,
        'date': date_text,
        'number': str(number_value),
        'payment_method': payment_method
    },copies=copies, notes=notes)



# Hook the function to the button
generate_btn.config(command=generate_receipt)

# Forbidden characters for file names (Windows)


def validate_input(event):
    widget = event.widget
    text = widget.get()
    for char in text:
        if char in INVALID_CHARS:
            Messagebox.show_warning(
                title="Μη έγκυρος χαρακτήρας",
                message=f"Ο χαρακτήρας '{char}' δεν επιτρέπεται στα ονόματα αρχείων."
            )
            # Remove the invalid character from the entry
            widget.delete(text.index(char))
            break

# Bind live validation to entries where user types free text
received_entry.bind("<KeyRelease>", validate_input)
check_entry.bind("<KeyRelease>", validate_input)




# Run the app
app.mainloop()



