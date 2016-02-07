from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from celery import Celery
from colorize import process_image

app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task(bind=True)
def run_colorizer(self, image):

    self.update_state(state='PROGRESS', meta={'current':0, 'total':100,
        'status':'Coloring'})
    
    output = process_image(image)

    return {'current': 100, 'total': 100, 'state':'DONE', 'status': 'DONE', 'result':output}


@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    return redirect(url_for('index'))

@app.route('/color', methods=['POST'])
def color():
    image = request.json
    task = run_colorizer.s(image).apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus', task_id=task.id)}

@app.route('/js/<path:path>')
def js(path):
    return send_from_directory('js', path)

@app.route('/style/<path:path>')
def style(path):
    return send_from_directory('style', path)

@app.route('/status/<task_id>')
def taskstatus(task_id):

    task = run_colorizer.AsyncResult(task_id)

    if task.state == 'PENDING':
            
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending.'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
