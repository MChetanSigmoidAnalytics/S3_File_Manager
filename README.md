# 🗂️ S3 File Manager

A simple **Flask + Boto3 based web application** to manage AWS S3 buckets with a user-friendly UI.  
Built as part of my **DataOps learning journey** while exploring Python frameworks and AWS services.  

---

## ✨ Features

- 🔐 **User Authentication** – Single-user login using AWS credentials.
- 📋 **List S3 Content** – View all buckets, folders, and files
- 🪣 **Bucket Management** – Create and delete S3 buckets.  
- 📂 **Folder Management** – Create folders inside buckets.  
- 📤 **File Operations** – Upload, move, copy, and delete files between buckets.  
- 🎨 **User-Friendly UI** – Simple and clean interface for file management.  

---

## 🛠️ Tech Stack

- **Python** 🐍  
- **Flask** (web framework)  
- **Boto3** (AWS SDK for Python)  
- **AWS S3** (cloud storage)  

---

## 🚀 Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MChetanSigmoidAnalytics/S3_File_Manager.git
   cd S3_File_Manager
## 🚀 Quick Start  

Run the following commands to set up and start the app:  

```bash
git clone https://github.com/MChetanSigmoidAnalytics/S3_File_Manager.git
cd S3_File_Manager

python3 -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows

pip install -r requirements.txt

# Set AWS credentials in .env or environment variables
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=ap-south-1

# Run below command in terminal 
flask run
# Open your browser
  http://127.0.0.1:5000
