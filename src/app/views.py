from flask import render_template, render_template_string, request, current_app as app

import cpuinfo
import psutil
import platform
import datetime


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/info")
def info():
    osinfo = {}
    osinfo["plat"] = platform
    osinfo["cpu"] = cpuinfo.get_cpu_info()
    osinfo["mem"] = psutil.virtual_memory()
    osinfo["net"] = psutil.net_if_addrs()
    osinfo["boottime"] = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return render_template("info.html", info=osinfo)


@app.route("/monitor")
def monitor():
    return render_template("monitor.html")

@app.route('/vulnerable')
def vulnerable():
    # Get the username parameter from the request
    username = request.args.get('username', 'Guest')

    # Create a template with the username - THIS IS VULNERABLE!
    template = f'''
    <h1>Hello, {username}!</h1>
    <p>Welcome to our application.</p>
    '''

    # Render the template with the user input directly included
    return render_template_string(template)
