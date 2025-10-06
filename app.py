from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from botocore.exceptions import ClientError
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge, Summary, Counter
import time
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------------------- Prometheus Setup --------------------
metrics = PrometheusMetrics(app)
metrics.info("app_info", "S3 File Manager Flask App", version="1.0.0")

# Custom metrics
bucket_count = Gauge("s3_bucket_total", "Total number of S3 buckets")
file_count = Gauge("s3_file_total", "Total number of files across all buckets")
operation_time = Summary("s3_operation_seconds", "Time spent on S3 operations")
error_counter = Counter("s3_errors_total", "Total number of S3 operation errors")

# -------------------- AWS Setup --------------------
def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION,
    )

# -------------------- Metrics Updater --------------------
@operation_time.time()
def update_metrics():
    try:
        s3 = get_s3_client()
        buckets = s3.list_buckets()
        total_buckets = len(buckets["Buckets"])
        bucket_count.set(total_buckets)

        total_files = 0
        for b in buckets["Buckets"]:
            objs = s3.list_objects_v2(Bucket=b["Name"])
            if "Contents" in objs:
                total_files += len(objs["Contents"])
        file_count.set(total_files)
    except Exception as e:
        error_counter.inc()
        print("Error updating metrics:", e)

# -------------------- Routes --------------------
@app.route("/")
def index():
    s3 = get_s3_client()
    try:
        response = s3.list_buckets()
        buckets = response["Buckets"]
        update_metrics()
        return render_template("index.html", buckets=buckets)
    except ClientError as e:
        error_counter.inc()
        flash(str(e), "danger")
        return render_template("error.html", error=str(e))

@app.route("/create_bucket", methods=["POST"])
def create_bucket():
    bucket_name = request.form["bucket_name"]
    s3 = get_s3_client()
    try:
        s3.create_bucket(Bucket=bucket_name)
        flash(f"Bucket '{bucket_name}' created successfully!", "success")
        update_metrics()
    except ClientError as e:
        error_counter.inc()
        flash(str(e), "danger")
    return redirect(url_for("index"))

@app.route("/delete_bucket/<bucket_name>")
def delete_bucket(bucket_name):
    s3 = get_s3_client()
    try:
        s3.delete_bucket(Bucket=bucket_name)
        flash(f"Bucket '{bucket_name}' deleted successfully!", "success")
        update_metrics()
    except ClientError as e:
        error_counter.inc()
        flash(str(e), "danger")
    return redirect(url_for("index"))

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    bucket = request.form["bucket"]
    s3 = get_s3_client()
    try:
        s3.upload_fileobj(file, bucket, file.filename)
        flash(f"File '{file.filename}' uploaded to '{bucket}'!", "success")
        update_metrics()
    except ClientError as e:
        error_counter.inc()
        flash(str(e), "danger")
    return redirect(url_for("view_bucket", bucket_name=bucket))

@app.route("/view_bucket/<bucket_name>")
def view_bucket(bucket_name):
    s3 = get_s3_client()
    try:
        objs = s3.list_objects_v2(Bucket=bucket_name)
        contents = objs.get("Contents", [])
        update_metrics()
        return render_template("bucket.html", bucket_name=bucket_name, contents=contents)
    except ClientError as e:
        error_counter.inc()
        flash(str(e), "danger")
        return render_template("error.html", error=str(e))

@app.route("/delete_file/<bucket_name>/<file_key>")
def delete_file(bucket_name, file_key):
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=bucket_name, Key=file_key)
        flash(f"File '{file_key}' deleted from '{bucket_name}'!", "success")
        update_metrics()
    except ClientError as e:
        error_counter.inc()
        flash(str(e), "danger")
    return redirect(url_for("view_bucket", bucket_name=bucket_name))

# -------------------- Metrics Endpoint --------------------
@app.route("/metrics")
def metrics_page():
    # The /metrics route is automatically handled by PrometheusMetrics
    # This is optional — you can leave this route empty
    return "Metrics are available at /metrics"

# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
