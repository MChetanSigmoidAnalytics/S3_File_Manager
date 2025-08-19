from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
import helper  # Make sure this matches your helper file name!
import uuid
import re
from flask import send_file

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this in production

# --- Authentication ---
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Login/Logout Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple hardcoded user for demo; replace with DB in production
        if username == 'admin' and password == 'Chetan@2002':
            session['logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@app.route("/")
@login_required
def index():
    try:
        buckets = helper.list_buckets()
    except Exception as e:
        import botocore
        if hasattr(e, 'response') and hasattr(e, 'operation_name'):
            flash(str(e.response['Error']['Message']), "danger")
        else:
            flash(f"Error fetching buckets: {e}", "danger")
        buckets = []
    return render_template("index.html", buckets=buckets)



def is_valid_bucket_name(name):
    pattern = r'^(?!\d+\.\d+\.\d+\.\d+$)(?!-)(?!.*--)[a-z0-9-]{3,63}(?<!-)$'
    return bool(re.match(pattern, name))

@app.route("/create_bucket", methods=["POST"])
@login_required
def create_bucket():
    bucket_name = request.form.get("bucket_name")
    
    if not is_valid_bucket_name(bucket_name):
        flash("Invalid bucket name. Use lowercase letters, numbers, and hyphens only (3–63 chars).", "danger")
        return redirect(url_for("index"))

    # Make bucket name unique automatically
    bucket_name = f"{bucket_name}-{uuid.uuid4().hex[:6]}"

    try:
        helper.create_bucket(bucket_name)
        flash(f"Bucket '{bucket_name}' created successfully!", "success")
    except Exception as e:
        flash(f"Error creating bucket: {e}", "danger")
    return redirect(url_for("index"))

@app.route("/delete-bucket", methods=["POST"])
@login_required
def delete_bucket():
    bucket_name = request.form.get("bucket_name")
    if not bucket_name:
        flash("Bucket name is required for deletion.", "danger")
        return redirect(url_for("index"))
    try:
        helper.delete_bucket(bucket_name)
        flash(f"Bucket '{bucket_name}' deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting bucket: {e}", "danger")
    return redirect(url_for("index"))


@app.route("/upload/<bucket_name>", methods=["POST"])
@login_required
def upload(bucket_name):
    file = request.files.get("file")
    prefix = request.form.get("prefix", "")
    if not file:
        flash("No file selected.", "danger")
        return redirect(url_for("view_bucket", bucket_name=bucket_name, prefix=prefix))
    key = prefix + file.filename
    try:
        helper.upload_file(bucket_name, file, key)
        flash(f"File '{file.filename}' uploaded!", "success")
    except Exception as e:
        flash(f"Error uploading file: {e}", "danger")
    return redirect(url_for("view_bucket", bucket_name=bucket_name, prefix=prefix))


@app.route("/delete-file/<bucket_name>/<path:key>", methods=["POST"])
@login_required
def delete_file(bucket_name, key):
    try:
        helper.delete_file(bucket_name, key)
        flash(f"File '{key}' deleted!", "success")
    except Exception as e:
        flash(f"Error deleting file: {e}", "danger")
    return redirect(url_for("view_bucket", bucket_name=bucket_name))


@app.route("/copy-file/<bucket_name>/<path:key>", methods=["POST"])
@login_required
def copy_file(bucket_name, key):
    dest_bucket = request.form.get("dest_bucket")
    dest_key = request.form.get("dest_key", key)
    action = request.form.get("action")

    if not dest_bucket:
        flash("Destination bucket is required.", "danger")
        return redirect(url_for("view_bucket", bucket_name=bucket_name))

    try:
        if action == "move":
            helper.move_file(bucket_name, key, dest_bucket, dest_key)
            flash(f"File '{key}' moved to '{dest_bucket}/{dest_key}'", "success")
        else:
            helper.copy_file(bucket_name, key, dest_bucket, dest_key)
            flash(f"File '{key}' copied to '{dest_bucket}/{dest_key}'", "success")
    except Exception as e:
        flash(f"Error during {action}: {e}", "danger")
    return redirect(url_for("view_bucket", bucket_name=bucket_name))


@app.route("/move-file/<bucket_name>/<path:key>", methods=["POST"])
@login_required
def move_file(bucket_name, key):
    dest_bucket = request.form.get("dest_bucket")
    dest_key = request.form.get("dest_key", key)

    if not dest_bucket:
        flash("Destination bucket is required.", "danger")
        return redirect(url_for("view_bucket", bucket_name=bucket_name))

    try:
        helper.move_file(bucket_name, key, dest_bucket, dest_key)
        flash(f"File '{key}' moved to '{dest_bucket}/{dest_key}'", "success")
    except Exception as e:
        flash(f"Error moving file: {e}", "danger")
    return redirect(url_for("view_bucket", bucket_name=bucket_name))


# Fix: Accept both root and subfolder creation by adding a second route
@app.route("/create-folder/<bucket_name>/", methods=["POST"])
@app.route("/create-folder/<bucket_name>/<path:prefix>", methods=["POST"])
@login_required
def create_folder(bucket_name, prefix=""):
    folder_name = request.form.get("folder_name")
    if not folder_name:
        flash("Folder name is required.", "danger")
        return redirect(url_for("view_bucket", bucket_name=bucket_name, prefix=prefix))
    # S3 folders are just objects ending with "/"
    folder_key = f"{prefix}{folder_name.strip().rstrip('/')}/"
    try:
        helper.create_folder(bucket_name, folder_key)
        flash(f"Folder '{folder_name}' created!", "success")
    except Exception as e:
        flash(f"Error creating folder: {e}", "danger")
    return redirect(url_for("view_bucket", bucket_name=bucket_name, prefix=prefix))


@app.route("/bucket/<bucket_name>")
@login_required
def view_bucket(bucket_name):
    prefix = request.args.get("prefix", "")
    try:
        folders, files = helper.list_objects_grouped(bucket_name, prefix)
    except Exception as e:
        flash(f"Error fetching files: {e}", "danger")
        folders, files = [], []
    return render_template("bucket.html", bucket_name=bucket_name, folders=folders, files=files, prefix=prefix)


@app.route("/download-file/<bucket_name>/<path:key>")
@login_required
def download_file(bucket_name, key):
    try:
        return helper.download_file(bucket_name, key)
    except Exception as e:
        flash(f"Error downloading file: {e}", "danger")
        return redirect(url_for("view_bucket", bucket_name=bucket_name))


if __name__ == "__main__":
    app.run(debug=True)
