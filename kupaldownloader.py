import sys
import json
import logging
import argparse
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from zk import ZK, const
from tqdm import tqdm
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("KupalDownloader")

def get_device_info(conn):
    try:
        return {
            'firmware_version': conn.get_firmware_version(),
            'serial_number': conn.get_serialnumber(),
            'platform': conn.get_platform(),
            'device_name': conn.get_device_name(),
            'total_users': conn.get_user_count()
        }
    except Exception as e:
        logger.warning(f"Could not get complete device info: {str(e)}")
        return {}

def connect_to_device(ip, port):
    logger.info(f"Connecting to device at {ip}:{port}...")
    try:
        zk = ZK(ip, port=port, timeout=5)
        conn = zk.connect()
        device_info = get_device_info(conn)
        logger.info("Connection successful!")
        logger.info("Device Information:")
        for key, value in device_info.items():
            logger.info(f"  {key.replace('_', ' ').title()}: {value}")
        return conn
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        raise

def download_raw_data(conn):
    """
    Downloads raw data from the ZKTeco device including users and their fingerprint templates.
    
    Args:
        conn: ZK device connection object
    
    Returns:
        dict: Dictionary containing users and their fingerprint data
    """
    try:
        users = conn.get_users()
        data = []
        logger.info(f"Found {len(users)} users")

        for user in tqdm(users, desc="Downloading fingerprint data"):
            user_data = {
                'uid': user.uid,
                'user_id': user.user_id,
                'name': user.name,
                'privilege': user.privilege,
                'password': user.password,
                'group_id': user.group_id,
                'fingerprints': []
            }
            
            # Get fingerprint templates for each user
            templates = conn.get_templates()
            for template in templates:
                if template.uid == user.uid:
                    user_data['fingerprints'].append({
                        'fid': template.fid,
                        'size': template.size,
                        'valid': template.valid,
                        'template': template.template
                    })
            data.append(user_data)
        return data
    except Exception as e:
        logger.error(f"Failed to download raw data: {str(e)}")
        raise

def save_as_json(data, filename):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename.replace('.json', '')}_{timestamp}.json"
        with open(filename, 'w') as f:
            json_data = {
                'export_date': datetime.now().isoformat(),
                'total_records': len(data),
                'fingerprints': data
            }
            json.dump(json_data, f, indent=4)
        logger.info(f"✓ Data saved successfully to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to save data: {str(e)}")
        raise

def upload_data_back(conn, data):
    try:
        fingerprints = data.get('fingerprints', data)  # Support both old and new format
        total = len(fingerprints)
        logger.info(f"Preparing to upload {total} fingerprint templates...")
        
        for item in tqdm(fingerprints, desc="Uploading"):
            try:
                conn.set_user_template(item['user_id'], item['finger_id'], item['template'])
            except Exception as e:
                logger.warning(f"Failed to upload template for user {item['user_id']}: {str(e)}")
        logger.info("✓ Upload completed successfully")
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='KupalDownloader - ZKTeco Fingerprint Data Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--ip', required=True, help='IP address of the ZKTeco device')
    parser.add_argument('--port', type=int, default=4370, help='Port number (default: 4370)')
    parser.add_argument('--action', choices=['download', 'upload', 'both'], required=True,
                      help='Action to perform: download, upload, or both')
    parser.add_argument('--file', default='fingerprint_data',
                      help='Base name for JSON file (timestamp will be added)')
    return parser.parse_args()

class KupalDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kupal Downloader")
        self.root.geometry("600x400")
        self.connection = None
        
        # Create connection frame
        self.create_connection_frame()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Create tabs
        self.create_employee_tab()
        self.create_fingerprint_tab()
        
        # Status label
        self.status_label = ttk.Label(root, text="Ready")
        self.status_label.pack(pady=5)

    def create_connection_frame(self):
        conn_frame = ttk.LabelFrame(self.root, text="Device Connection")
        conn_frame.pack(fill='x', padx=5, pady=5)
        
        # IP and Port entries
        ttk.Label(conn_frame, text="IP Address:").pack(side='left', padx=5)
        self.ip_entry = ttk.Entry(conn_frame, width=15)
        self.ip_entry.insert(0, "192.168.1.201")
        self.ip_entry.pack(side='left', padx=5)
        
        ttk.Label(conn_frame, text="Port:").pack(side='left', padx=5)
        self.port_entry = ttk.Entry(conn_frame, width=6)
        self.port_entry.insert(0, "4370")
        self.port_entry.pack(side='left', padx=5)
        
        # Connection buttons
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_device)
        self.connect_btn.pack(side='left', padx=5)
        
        self.disconnect_btn = ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_device, state='disabled')
        self.disconnect_btn.pack(side='left', padx=5)
        
        # Status indicator
        self.conn_status = ttk.Label(conn_frame, text="Not Connected", foreground='red')
        self.conn_status.pack(side='right', padx=5)

    def connect_device(self):
        try:
            ip = self.ip_entry.get()
            port = int(self.port_entry.get())
            self.connection = connect_to_device(ip, port)
            
            # Update UI
            self.conn_status.config(text="Connected", foreground='green')
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
            self.ip_entry.config(state='disabled')
            self.port_entry.config(state='disabled')
            
            # Get and display device info
            device_info = get_device_info(self.connection)
            info_text = "\n".join([f"{k.replace('_', ' ').title()}: {v}" 
                                 for k, v in device_info.items()])
            messagebox.showinfo("Device Information", info_text)
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect_device(self):
        try:
            if self.connection:
                self.connection.disconnect()
                self.connection = None
            
            # Update UI
            self.conn_status.config(text="Not Connected", foreground='red')
            self.connect_btn.config(state='normal')
            self.disconnect_btn.config(state='disabled')
            self.ip_entry.config(state='normal')
            self.port_entry.config(state='normal')
            
        except Exception as e:
            messagebox.showerror("Disconnection Error", str(e))

    def get_connection(self):
        if not self.connection:
            raise Exception("Not connected to device")
        return self.connection

    def download_employees(self):
        try:
            if not self.connection:
                raise Exception("Please connect to device first")
            users = self.connection.get_users()
            
            employee_data = [{
                'uid': user.uid,
                'user_id': user.user_id,
                'name': user.name,
                'privilege': user.privilege,
                'password': user.password,
                'group_id': user.group_id
            } for user in users]
            
            filename = save_as_json({'employees': employee_data}, 'employee_data')
            self.employee_text.delete(1.0, tk.END)
            self.employee_text.insert(tk.END, f"Downloaded {len(users)} employees\n")
            for user in users:
                self.employee_text.insert(tk.END, f"ID: {user.user_id}, Name: {user.name}\n")
            
            self.connection.disconnect()
            messagebox.showinfo("Success", f"Employee data saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def download_fingerprints(self):
        try:
            if not self.connection:
                raise Exception("Please connect to device first")
            data = download_raw_data(self.connection)
            filename = save_as_json(data, "fingerprint_data")
            
            self.fingerprint_text.delete(1.0, tk.END)
            self.fingerprint_text.insert(tk.END, f"Downloaded {len(data)} fingerprint records\n")
            
            self.connection.disconnect()
            messagebox.showinfo("Success", f"Fingerprint data saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def upload_employees(self):
        try:
            if not self.connection:
                raise Exception("Please connect to device first")
            filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if filename:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                for emp in data.get('employees', []):
                    self.connection.set_user(uid=emp['uid'], name=emp['name'], 
                                privilege=emp['privilege'], 
                                password=emp['password'],
                                group_id=emp['group_id'],
                                user_id=emp['user_id'])
                
                self.connection.disconnect()
                messagebox.showinfo("Success", "Employee data uploaded successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def upload_fingerprints(self):
        try:
            if not self.connection:
                raise Exception("Please connect to device first")
            filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if filename:
                with open(filename, 'r') as f:
                    data = json.load(f)
                upload_data_back(self.connection, data)
                self.connection.disconnect()
                messagebox.showinfo("Success", "Fingerprint data uploaded successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_employee_tab(self):
        """Creates the Employees tab with download/upload buttons and text area"""
        employee_frame = ttk.Frame(self.notebook)
        self.notebook.add(employee_frame, text='Employees')
        
        # Buttons
        btn_frame = ttk.Frame(employee_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Download Employees", 
                   command=self.download_employees).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Upload Employees", 
                   command=self.upload_employees).pack(side='left', padx=5)
        
        # Text area for displaying employee data
        self.employee_text = scrolledtext.ScrolledText(employee_frame, height=15)
        self.employee_text.pack(expand=True, fill='both', padx=5, pady=5)

    def create_fingerprint_tab(self):
        """Creates the Fingerprints tab with download/upload buttons and text area"""
        fingerprint_frame = ttk.Frame(self.notebook)
        self.notebook.add(fingerprint_frame, text='Fingerprints')
        
        # Buttons
        btn_frame = ttk.Frame(fingerprint_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Download Fingerprints", 
                   command=self.download_fingerprints).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Upload Fingerprints", 
                   command=self.upload_fingerprints).pack(side='left', padx=5)
        
        # Text area for displaying fingerprint data
        self.fingerprint_text = scrolledtext.ScrolledText(fingerprint_frame, height=15)
        self.fingerprint_text.pack(expand=True, fill='both', padx=5, pady=5)

def main():
    args = parse_arguments() if len(sys.argv) > 1 else None
    
    if args:
        # CLI mode
        try:
            conn = connect_to_device(args.ip, args.port)
            if args.action in ['download', 'both']:
                data = download_raw_data(conn)
                save_as_json(data, args.file)
            if args.action in ['upload', 'both']:
                with open(args.file, 'r') as f:
                    data = json.load(f)
                upload_data_back(conn, data)
            conn.disconnect()
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            sys.exit(1)
    else:
        # GUI mode
        root = tk.Tk()
        app = KupalDownloaderGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()
