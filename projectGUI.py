import tkinter as tk
from tkinter import ttk, messagebox
import paho.mqtt.client as mqtt
import shelve

# MQTT settings
broker_address = "mqtt-dashboard.com"
port = 1883
ecg_topic = "ecg/data"
bpm_topic = "heartRate/bpm"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe([(ecg_topic, 0), (bpm_topic, 0)])
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    data = msg.payload.decode()
    patient_id = patient_id_entry.get()
    if patient_id:
        if msg.topic == ecg_topic:
            update_ecg(data, patient_id)
        elif msg.topic == bpm_topic:
            update_bpm(data, patient_id)

def update_ecg(data, patient_id):
    ecg_label.config(text=f"ECG Voltage: {data} V")
    save_patient_data(patient_id, "ECG Voltage", data)

def update_bpm(data, patient_id):
    bpm_label.config(text=f"Heart Rate: {data} BPM")
    save_patient_data(patient_id, "Heart Rate", data)

def save_patient_data(patient_id, key, value):
    with shelve.open('patient_info', writeback=True) as db:
        if patient_id not in db:
            db[patient_id] = {}
        db[patient_id][key] = value
        db.sync()

def save_patient_info():
    patient_id = patient_id_entry.get()
    name = entry_name.get()
    age = entry_age.get()
    height = entry_height.get()
    weight = entry_weight.get()
    sex = entry_sex.get()
    patient_data = {'Name': name, 'Age': age, 'Height': height, 'Weight': weight, 'Sex': sex}
    with shelve.open('patient_info', writeback=True) as db:
        if patient_id in db:
            db[patient_id].update(patient_data)
        else:
            db[patient_id] = patient_data
    messagebox.showinfo("Success", "Patient information saved!")

def sign_up():
    username = entry_username.get()
    password = entry_password.get()
    with shelve.open('credentials') as db:
        if username in db:
            messagebox.showerror("Error", "Username already exists!")
        else:
            db[username] = password
            messagebox.showinfo("Success", "Sign up successful! Please log in.")
            login_frame.pack()

def log_in():
    username = entry_username.get()
    password = entry_password.get()
    with shelve.open('credentials') as db:
        if db.get(username) == password:
            messagebox.showinfo("Success", "Login successful!")
            login_frame.pack_forget()
            show_monitor()
        else:
            messagebox.showerror("Error", "Invalid username or password!")

def show_monitor():
    global ecg_label, bpm_label, monitor_frame, entry_name, entry_age, entry_height, entry_weight, entry_sex
    monitor_frame = tk.Frame(root)
    monitor_frame.pack(pady=20, expand=True, fill='both')
    setup_patient_form(monitor_frame)
    setup_monitor_labels(monitor_frame)
    client.connect(broker_address, port)
    client.loop_start()

def setup_patient_form(frame):
    global patient_id_entry, entry_name, entry_age, entry_height, entry_weight, entry_sex
    ttk.Label(frame, text="Patient ID:").pack(pady=5)
    patient_id_entry = ttk.Entry(frame)
    patient_id_entry.pack(pady=5)

    names = ["Name", "Age", "Height", "Weight", "Sex"]
    entries = [ttk.Entry(frame) for _ in names]
    entry_name, entry_age, entry_height, entry_weight, entry_sex = entries
    for name, entry in zip(names, entries):
        ttk.Label(frame, text=f"{name}:").pack(pady=2)
        entry.pack(pady=2)

    save_button = ttk.Button(frame, text="Save", command=save_patient_info)
    save_button.pack(pady=10)

def setup_monitor_labels(frame):
    global ecg_label, bpm_label
    ecg_label = ttk.Label(frame, text="ECG Voltage: ", font=("Helvetica", 16))
    ecg_label.pack(pady=10)
    bpm_label = ttk.Label(frame, text="Heart Rate: ", font=("Helvetica", 16))
    bpm_label.pack(pady=10)
    ttk.Button(frame, text="View Patient Info", command=view_patient_info).pack(pady=10)
    ttk.Button(frame, text="Exit", command=lambda: exit_app(True)).pack(pady=10)

def view_patient_info():
    patient_id = patient_id_entry.get()
    with shelve.open('patient_info') as db:
        if patient_id in db and db[patient_id]:
            patient_data = db[patient_id]
            show_patient_data(patient_data)
        else:
            messagebox.showerror("Error", "No information found for patient ID: " + patient_id)

def show_patient_data(data):
    patient_window = tk.Toplevel(root)
    patient_window.title("Patient Information")
    tree = ttk.Treeview(patient_window, columns=('Field', 'Value'), show='headings')
    tree.heading('Field', text='Field')
    tree.heading('Value', text='Value')
    tree.pack(fill='both', expand=True)
    for key, value in data.items():
        tree.insert('', 'end', values=(key, value))

def exit_app(return_to_login=False):
    if return_to_login:
        monitor_frame.pack_forget()
        show_login_frame()
    else:
        root.quit()

def show_login_frame():
    global login_frame, entry_username, entry_password
    login_frame = tk.Frame(root)
    login_frame.pack(pady=20)
    ttk.Label(login_frame, text="Username:").pack(pady=5)
    entry_username = ttk.Entry(login_frame)
    entry_username.pack(pady=5)
    ttk.Label(login_frame, text="Password:").pack(pady=5)
    entry_password = ttk.Entry(login_frame, show="*")
    entry_password.pack(pady=5)
    ttk.Button(login_frame, text="Sign Up", command=sign_up).pack(side=tk.LEFT, padx=10)
    ttk.Button(login_frame, text="Log In", command=log_in).pack(side=tk.RIGHT, padx=10)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

root = tk.Tk()
root.title("ECG and Heart Rate Monitor")
show_login_frame()

root.mainloop()