from flask import Flask, render_template, request, send_file, jsonify
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128
from reportlab.lib import colors
from io import BytesIO

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        file = request.files.get('file')
        color = request.form.get('background_color', '#800080')  # Default to purple if not provided

        if 'upload_json' in request.form:
            if file and file.filename.endswith('.json'):
                data = json.load(file)
                return generate_labels(data, color)  # Pass color here
            else:
                return "No JSON file provided or wrong file type.", 400
    return render_template('upload.html')

def generate_json_file(form):
    aisle_min = int(form['aisle_min'])
    aisle_max = int(form['aisle_max'])
    row_min = int(form['row_min'])
    row_max = int(form['row_max'])
    bin_min = int(form['bin_min'])
    bin_max = int(form['bin_max'])
    bay_min = int(form['bay_min'])
    bay_max = int(form['bay_max'])

    labels = []
    for aisle in range(aisle_min, aisle_max + 1):
        for row in range(row_min, row_max + 1):
            for bin in range(bin_min, bin_max + 1):
                for bay in range(bay_min, bay_max + 1):
                    label = {
                        'Field1': f"{aisle:02} {row:02} {bin:02}",
                        'Bay': f"{bay:02}"
                    }
                    labels.append(label)

    return download_json(labels)

def download_json(data):
    buffer = BytesIO()
    # Convert the JSON data to string, then encode it to bytes, and finally write it to the buffer.
    json_str = json.dumps(data, indent=4)
    buffer.write(json_str.encode('utf-8'))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='labels.json', mimetype='application/json')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        color = request.form.get('background_color', '#800080')  # Default color is purple
        if file and file.filename.endswith('.json'):
            data = json.load(file)
            return generate_labels(data, color)
        else:
            return "No JSON file provided or wrong file type.", 400
    return render_template('upload.html')

def generate_labels(data, color):
    c = canvas.Canvas("labels.pdf", pagesize=letter)
    width, height = letter  # Size of letter page
    num_labels_page = 0

    label_height = 2.0 * inch
    label_width = 4.0 * inch
    top_margin = 0.50 * inch
    side_margin = 0.15 * inch
    gap_between_labels = 0.2 * inch

    for index, row in enumerate(data):
        if num_labels_page >= 10:
            c.showPage()
            num_labels_page = 0

        column_index = index % 2
        row_index = (index // 2) % 5

        x = side_margin + (column_index * (label_width + gap_between_labels))
        y = height - top_margin - (row_index * label_height) - label_height


        c.setFillColor(colors.HexColor(color))  
        c.rect(x, y, label_width, label_height, fill=1, stroke=0)

        barcode_y_position = y + 0.1 * inch

        parts = row['Field1'].split()
        aisle, row_val, bin = parts if len(parts) >= 3 else ('Unknown', 'Unknown', 'Unknown')
        bay = row.get('Bay', 'Unknown')

        text_y_position = y + label_height - 0.25 * inch
        value_y_position = text_y_position - 0.45 * inch

        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black)  # Set text color to black
        c.drawString(x + 0.26 * inch, text_y_position, "Aisle:")
        c.drawString(x + 1.37 * inch, text_y_position, "Row:")
        c.drawString(x + 2.47 * inch, text_y_position, "Bay:")
        c.drawString(x + 3.50 * inch, text_y_position, "Bin:")

        c.setFont("Helvetica-Bold", 35)
        c.drawString(x + 0.18 * inch, value_y_position, aisle)
        c.drawString(x + 1.28 * inch, value_y_position, row_val)
        c.drawString(x + 2.38 * inch, value_y_position, bay)
        c.drawString(x + 3.40 * inch, value_y_position, bin)

        # Define and draw the white rectangle for the barcode area
        white_rect_x = x + 0.25 * inch
        white_rect_y = y + 0.001 * inch
        white_rect_width = 3.38 * inch - 0.25 * inch  # Ending at 3.38" from the left side
        white_rect_height = 0.7 * inch

        c.setFillColor(colors.white)
        c.rect(white_rect_x, white_rect_y, white_rect_width, white_rect_height, fill=1, stroke=0)
        c.setFillColor(colors.black)

        # Draw the barcode after resetting fill color to ensure it has a white background
        barcode = code128.Code128(row['Field1'], barHeight=0.5 * inch, barWidth=1.6)
        barcode.drawOn(c, x + 0.2 * inch, barcode_y_position)
        
        #Drawing arrow
        arrow_x = x + 3.7 * inch
        arrow_start_y = y + label_height - 1.7 * inch
        arrow_end_y = y + label_height - 0.87 * inch

        c.setLineWidth(6)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)  # Set fill color for a solid arrowhead
        c.line(arrow_x, arrow_start_y, arrow_x, arrow_end_y)  # Draw the shaft of the arrow

        # Draw solid arrowhead
        arrowhead_size = 0.11 * inch  # Increase size for bigger arrowhead
        p = c.beginPath()
        p.moveTo(arrow_x, arrow_end_y)
        p.lineTo(arrow_x - arrowhead_size, arrow_end_y - arrowhead_size)
        p.lineTo(arrow_x + arrowhead_size, arrow_end_y - arrowhead_size)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        
        num_labels_page += 1

    c.save()
    return send_file('labels.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

