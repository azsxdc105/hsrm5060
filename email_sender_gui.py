#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
برنامج إرسال الملفات عبر البريد الإلكتروني - نسخة الواجهة الرسومية
Email File Sender Script - GUI Version

هذا البرنامج يوفر واجهة رسومية لإرسال الملفات عبر البريد الإلكتروني
This program provides a GUI interface for sending files via email
"""

import os
import smtplib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import threading

class EmailSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("برنامج إرسال الملفات عبر البريد الإلكتروني / Email File Sender")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # قائمة الملفات المحددة / Selected files list
        self.selected_files = []
        
        # إعداد الواجهة / Setup interface
        self.setup_interface()
        
        # إعدادات افتراضية / Default settings
        self.load_default_settings()
    
    def setup_interface(self):
        """إعداد واجهة المستخدم / Setup user interface"""
        
        # العنوان الرئيسي / Main title
        title_frame = tk.Frame(self.root, bg='#2c3e50', pady=10)
        title_frame.pack(fill='x')
        
        title_label = tk.Label(title_frame, 
                              text="برنامج إرسال الملفات عبر البريد الإلكتروني\nEmail File Sender",
                              font=('Arial', 14, 'bold'),
                              fg='white',
                              bg='#2c3e50')
        title_label.pack()
        
        # إطار رئيسي للمحتوى / Main content frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # ========== قسم اختيار الملفات / File Selection Section ==========
        files_frame = tk.LabelFrame(main_frame, 
                                   text="اختيار الملفات / File Selection",
                                   font=('Arial', 10, 'bold'),
                                   padx=10, pady=10)
        files_frame.pack(fill='x', pady=(0, 10))
        
        # أزرار اختيار الملفات / File selection buttons
        button_frame = tk.Frame(files_frame)
        button_frame.pack(fill='x', pady=(0, 10))
        
        self.select_files_btn = tk.Button(button_frame,
                                         text="اختيار ملفات / Select Files",
                                         command=self.select_files,
                                         bg='#3498db',
                                         fg='white',
                                         font=('Arial', 10),
                                         padx=20, pady=5)
        self.select_files_btn.pack(side='left', padx=(0, 10))
        
        self.select_folder_btn = tk.Button(button_frame,
                                          text="اختيار مجلد / Select Folder",
                                          command=self.select_folder,
                                          bg='#9b59b6',
                                          fg='white',
                                          font=('Arial', 10),
                                          padx=20, pady=5)
        self.select_folder_btn.pack(side='left', padx=(0, 10))
        
        self.clear_files_btn = tk.Button(button_frame,
                                        text="مسح القائمة / Clear List",
                                        command=self.clear_files,
                                        bg='#e74c3c',
                                        fg='white',
                                        font=('Arial', 10),
                                        padx=20, pady=5)
        self.clear_files_btn.pack(side='left')
        
        # قائمة الملفات المحددة / Selected files list
        self.files_listbox = tk.Listbox(files_frame, height=6, font=('Arial', 9))
        self.files_listbox.pack(fill='both', expand=True, pady=(0, 10))
        
        # شريط التمرير للقائمة / Scrollbar for listbox
        scrollbar = tk.Scrollbar(files_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        self.files_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.files_listbox.yview)
        
        # ========== قسم إعدادات البريد الإلكتروني / Email Settings Section ==========
        email_frame = tk.LabelFrame(main_frame,
                                   text="إعدادات البريد الإلكتروني / Email Settings",
                                   font=('Arial', 10, 'bold'),
                                   padx=10, pady=10)
        email_frame.pack(fill='x', pady=(0, 10))
        
        # البريد المرسل منه / Sender email
        sender_frame = tk.Frame(email_frame)
        sender_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(sender_frame, text="بريدك الإلكتروني / Your Email:", 
                font=('Arial', 9)).pack(anchor='w')
        self.sender_email_entry = tk.Entry(sender_frame, font=('Arial', 9))
        self.sender_email_entry.pack(fill='x', pady=(2, 0))
        
        # كلمة المرور / Password
        password_frame = tk.Frame(email_frame)
        password_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(password_frame, text="كلمة مرور التطبيق / App Password:", 
                font=('Arial', 9)).pack(anchor='w')
        self.password_entry = tk.Entry(password_frame, show='*', font=('Arial', 9))
        self.password_entry.pack(fill='x', pady=(2, 0))
        
        # البريد المرسل إليه / Recipient email
        recipient_frame = tk.Frame(email_frame)
        recipient_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(recipient_frame, text="البريد المرسل إليه / Recipient Email:", 
                font=('Arial', 9)).pack(anchor='w')
        self.recipient_email_entry = tk.Entry(recipient_frame, font=('Arial', 9))
        self.recipient_email_entry.pack(fill='x', pady=(2, 0))
        
        # موضوع الرسالة / Subject
        subject_frame = tk.Frame(email_frame)
        subject_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(subject_frame, text="موضوع الرسالة / Subject:", 
                font=('Arial', 9)).pack(anchor='w')
        self.subject_entry = tk.Entry(subject_frame, font=('Arial', 9))
        self.subject_entry.pack(fill='x', pady=(2, 0))
        
        # نص الرسالة / Message body
        message_frame = tk.Frame(email_frame)
        message_frame.pack(fill='both', expand=True)
        
        tk.Label(message_frame, text="نص الرسالة / Message Body:", 
                font=('Arial', 9)).pack(anchor='w')
        self.message_text = scrolledtext.ScrolledText(message_frame, 
                                                     height=6, 
                                                     font=('Arial', 9))
        self.message_text.pack(fill='both', expand=True, pady=(2, 0))
        
        # ========== قسم الحالة والإرسال / Status and Send Section ==========
        status_frame = tk.LabelFrame(main_frame,
                                    text="الحالة والإرسال / Status and Send",
                                    font=('Arial', 10, 'bold'),
                                    padx=10, pady=10)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # شريط التقدم / Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0, 10))
        
        # حالة العملية / Operation status
        self.status_label = tk.Label(status_frame, 
                                    text="جاهز للإرسال / Ready to send",
                                    font=('Arial', 9),
                                    fg='green')
        self.status_label.pack(pady=(0, 10))
        
        # زر الإرسال / Send button
        self.send_button = tk.Button(status_frame,
                                    text="إرسال الملفات / Send Files",
                                    command=self.send_email_threaded,
                                    bg='#27ae60',
                                    fg='white',
                                    font=('Arial', 12, 'bold'),
                                    padx=30, pady=10)
        self.send_button.pack()
    
    def load_default_settings(self):
        """تحميل الإعدادات الافتراضية / Load default settings"""
        self.sender_email_entry.insert(0, "your_email@gmail.com")
        self.recipient_email_entry.insert(0, "recipient@example.com")
        self.subject_entry.insert(0, "مطالبة جديدة - الملفات مرفقة")
        
        default_message = """السلام عليكم،

أرفق لكم الملفات المطلوبة.

شكراً."""
        self.message_text.insert('1.0', default_message)
    
    def select_files(self):
        """اختيار ملفات محددة / Select specific files"""
        files = filedialog.askopenfilenames(
            title="اختر الملفات المراد إرسالها / Select files to send",
            filetypes=[("جميع الملفات / All files", "*.*")]
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.files_listbox.insert(tk.END, Path(file).name)
        
        self.update_status(f"تم إضافة {len(files)} ملف / Added {len(files)} files")
    
    def select_folder(self):
        """اختيار مجلد كامل / Select entire folder"""
        folder = filedialog.askdirectory(
            title="اختر المجلد المراد إرسال ملفاته / Select folder to send"
        )
        
        if folder:
            folder_path = Path(folder)
            files_found = 0
            
            for file_path in folder_path.iterdir():
                if file_path.is_file():
                    file_str = str(file_path)
                    if file_str not in self.selected_files:
                        self.selected_files.append(file_str)
                        self.files_listbox.insert(tk.END, file_path.name)
                        files_found += 1
            
            self.update_status(f"تم إضافة {files_found} ملف من المجلد / Added {files_found} files from folder")
    
    def clear_files(self):
        """مسح قائمة الملفات / Clear files list"""
        self.selected_files.clear()
        self.files_listbox.delete(0, tk.END)
        self.update_status("تم مسح القائمة / List cleared")
    
    def update_status(self, message, color='black'):
        """تحديث رسالة الحالة / Update status message"""
        self.status_label.config(text=message, fg=color)
        self.root.update_idletasks()
    
    def validate_inputs(self):
        """التحقق من صحة البيانات المدخلة / Validate input data"""
        if not self.selected_files:
            messagebox.showerror("خطأ / Error", "يرجى اختيار الملفات أولاً / Please select files first")
            return False
        
        if not self.sender_email_entry.get().strip():
            messagebox.showerror("خطأ / Error", "يرجى إدخال بريدك الإلكتروني / Please enter your email")
            return False
        
        if not self.password_entry.get().strip():
            messagebox.showerror("خطأ / Error", "يرجى إدخال كلمة مرور التطبيق / Please enter app password")
            return False
        
        if not self.recipient_email_entry.get().strip():
            messagebox.showerror("خطأ / Error", "يرجى إدخال البريد المرسل إليه / Please enter recipient email")
            return False
        
        return True
    
    def create_email_message(self):
        """إنشاء رسالة البريد الإلكتروني / Create email message"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email_entry.get().strip()
            msg['To'] = self.recipient_email_entry.get().strip()
            msg['Subject'] = self.subject_entry.get().strip()
            
            # إضافة نص الرسالة / Add message body
            body = self.message_text.get('1.0', tk.END).strip()
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # إضافة المرفقات / Add attachments
            for file_path in self.selected_files:
                try:
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    filename = Path(file_path).name
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
                    
                    self.update_status(f"تم إرفاق: {filename} / Attached: {filename}")
                    
                except Exception as e:
                    self.update_status(f"خطأ في إرفاق {Path(file_path).name}: {str(e)}", 'red')
            
            return msg
            
        except Exception as e:
            self.update_status(f"خطأ في إنشاء الرسالة: {str(e)} / Error creating message: {str(e)}", 'red')
            return None
    
    def send_email_threaded(self):
        """إرسال البريد الإلكتروني في خيط منفصل / Send email in separate thread"""
        if not self.validate_inputs():
            return
        
        # تعطيل زر الإرسال / Disable send button
        self.send_button.config(state='disabled')
        self.progress.start()
        
        # إنشاء خيط منفصل للإرسال / Create separate thread for sending
        thread = threading.Thread(target=self.send_email)
        thread.daemon = True
        thread.start()
    
    def send_email(self):
        """إرسال البريد الإلكتروني / Send email"""
        try:
            self.update_status("جاري إنشاء الرسالة... / Creating message...")
            
            # إنشاء الرسالة / Create message
            message = self.create_email_message()
            if not message:
                return
            
            self.update_status("جاري الاتصال بخادم Gmail... / Connecting to Gmail server...")
            
            # إرسال الرسالة / Send message
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.sender_email_entry.get().strip(), 
                        self.password_entry.get().strip())
            
            self.update_status("جاري إرسال الرسالة... / Sending message...")
            server.send_message(message)
            server.quit()
            
            # إظهار رسالة نجاح / Show success message
            self.root.after(0, self.on_send_success)
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "خطأ في المصادقة - تحقق من البريد وكلمة المرور\nAuthentication error - Check email and password"
            self.root.after(0, lambda: self.on_send_error(error_msg))
            
        except Exception as e:
            error_msg = f"خطأ في الإرسال: {str(e)}\nSend error: {str(e)}"
            self.root.after(0, lambda: self.on_send_error(error_msg))
    
    def on_send_success(self):
        """عند نجاح الإرسال / On successful send"""
        self.progress.stop()
        self.send_button.config(state='normal')
        self.update_status("✅ تم إرسال جميع الملفات بنجاح! / ✅ All files sent successfully!", 'green')
        
        messagebox.showinfo("نجح الإرسال / Success", 
                           "تم إرسال جميع الملفات بنجاح!\nAll files sent successfully!")
    
    def on_send_error(self, error_message):
        """عند فشل الإرسال / On send failure"""
        self.progress.stop()
        self.send_button.config(state='normal')
        self.update_status("❌ فشل في الإرسال / ❌ Send failed", 'red')
        
        messagebox.showerror("خطأ في الإرسال / Send Error", error_message)

def main():
    """الدالة الرئيسية / Main function"""
    root = tk.Tk()
    app = EmailSenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()