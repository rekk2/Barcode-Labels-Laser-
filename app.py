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
        color = request.form.get('background_color')
        template_name = request.form.get('template_name', 'default')
        selected_template = templates.get(template_name, {})

        if 'upload_json' in request.form:
            if file and file.filename.endswith('.json'):
                try:
                    data = json.load(file)
                    return generate_labels(data, color, selected_template)
                except json.JSONDecodeError:
                    return "Invalid JSON file.", 400
            else:
                return "No JSON file provided or wrong file type.", 400
        elif 'generate_json' in request.form:
            return generate_json_file(request.form)
    return render_template('upload.html', templates=templates)


def generate_json_file(form):
    labels = []
    for aisle in range(int(form['aisle_min']), int(form['aisle_max']) + 1):
        for row in range(int(form['row_min']), int(form['row_max']) + 1):
            for bin in range(int(form['bin_min']), int(form['bin_max']) + 1):
                for bay in range(int(form['bay_min']), int(form['bay_max']) + 1):
                    labels.append({
                        'Field1': f"{aisle:02} {row:02} {bin:02}",
                        'Bay': f"{bay:02}"
                    })
    return download_json(labels)

def download_json(data):
    buffer = BytesIO()
    json_str = json.dumps(data, indent=4)
    buffer.write(json_str.encode('utf-8'))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='labels.json', mimetype='application/json')

def generate_labels(data, color, template):
    # Check if necessary keys exist in the template
    required_keys = [
        'label_height', 'label_width', 'top_margin', 'side_margin',
        'gap_between_labels', 'labels_per_row', 'labels_per_sheet',
        'font_size_label', 'font_size_value', 'barcode_height',
        'barcode_width', 'arrow_thickness', 'arrow_length',
        'arrow_x_offset', 'arrow_start_y_offset', 'arrowhead_size',
        'white_rect_width', 'white_rect_height'
    ]
    if not all(key in template for key in required_keys):
        return "Template is incomplete.", 400

    c = canvas.Canvas("labels.pdf", pagesize=letter)
    width, height = letter

    label_height = template['label_height'] * inch
    label_width = template['label_width'] * inch
    top_margin = template['top_margin'] * inch
    side_margin = template['side_margin'] * inch
    gap_between_labels = template['gap_between_labels'] * inch
    labels_per_row = template['labels_per_row']
    labels_per_sheet = template['labels_per_sheet']
    font_size_label = template['font_size_label']
    font_size_value = template['font_size_value']
    barcode_height = template['barcode_height'] * inch
    barcode_width = template['barcode_width']
    barcode_y_offset = template['barcode_y_offset'] * inch
    barcode_x_offset = template['barcode_x_offset'] * inch
    arrow_thickness = template['arrow_thickness']
    arrow_length = template['arrow_length'] * inch
    arrow_x_offset = template['arrow_x_offset']
    arrow_start_y_offset = template['arrow_start_y_offset'] * inch
    arrowhead_size = template['arrowhead_size'] * inch
    white_rect_width = template['white_rect_width'] * inch
    white_rect_height = template['white_rect_height'] * inch
    white_rect_x_offset = template['white_rect_x_offset'] * inch
    white_rect_y_offset = template['white_rect_y_offset'] * inch
    text_y_offset = template['text_y_offset'] * inch
    value_y_offset = template['value_y_offset'] * inch
    text_x_offset_aisle = template['text_x_offset_aisle'] * inch
    text_x_offset_row = template['text_x_offset_row'] * inch
    text_x_offset_bay = template['text_x_offset_bay'] * inch
    text_x_offset_bin = template['text_x_offset_bin'] * inch
    value_x_offset_aisle = template['value_x_offset_aisle'] * inch
    value_x_offset_row = template['value_x_offset_row'] * inch
    value_x_offset_bay = template['value_x_offset_bay'] * inch
    value_x_offset_bin = template['value_x_offset_bin'] * inch
    
    num_labels_page = 0
    total_labels = 0
    for index, row in enumerate(data):
        if num_labels_page >= labels_per_sheet:
            c.showPage()
            num_labels_page = 0

        column_index = index % labels_per_row
        page_index = index // labels_per_sheet  
        row_index = (index - page_index * labels_per_sheet) // labels_per_row

        x = side_margin + (column_index * (label_width + gap_between_labels))
        y = height - top_margin - (row_index + 1) * label_height  

        c.setFillColor(colors.HexColor(color))
        c.rect(x, y, label_width, label_height, fill=1, stroke=0)


        parts = row['Field1'].split()
        aisle, row_val, bin = parts if len(parts) == 3 else ('Unknown', 'Unknown', 'Unknown')
        bay = row.get('Bay', 'Unknown')

        text_y_position = y + label_height - text_y_offset
        value_y_position = text_y_position - value_y_offset


        c.setFont("Helvetica", font_size_label)
        c.setFillColor(colors.black)
        c.drawString(x + text_x_offset_aisle, text_y_position, "Aisle:")
        c.drawString(x + text_x_offset_row, text_y_position, "Row:")
        c.drawString(x + text_x_offset_bay, text_y_position, "Bay:")
        c.drawString(x + text_x_offset_bin, text_y_position, "Bin:")

        c.setFont("Helvetica-Bold", font_size_value)
        c.drawString(x + value_x_offset_aisle, value_y_position, aisle)
        c.drawString(x + value_x_offset_row, value_y_position, row_val)
        c.drawString(x + value_x_offset_bay, value_y_position, bay)
        c.drawString(x + value_x_offset_bin, value_y_position, bin)


        white_rect_x = x + white_rect_x_offset
        white_rect_y = y + white_rect_y_offset
        c.setFillColor(colors.white)
        c.rect(white_rect_x, white_rect_y, white_rect_width, white_rect_height, fill=1, stroke=0)
        c.setFillColor(colors.black)
        
        barcode_y_position = y + barcode_y_offset
        barcode = code128.Code128(row['Field1'], barHeight=barcode_height, barWidth=barcode_width)
        barcode.drawOn(c, x + barcode_x_offset, barcode_y_position)

        arrow_x = x + arrow_x_offset * inch
        arrow_start_y = y + label_height - arrow_start_y_offset
        arrow_end_y = arrow_start_y + arrow_length

        c.setLineWidth(arrow_thickness)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)  
        c.line(arrow_x, arrow_start_y, arrow_x, arrow_end_y)  

        p = c.beginPath()
        p.moveTo(arrow_x, arrow_end_y)
        p.lineTo(arrow_x - arrowhead_size, arrow_end_y - arrowhead_size)
        p.lineTo(arrow_x + arrowhead_size, arrow_end_y - arrowhead_size)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

        num_labels_page += 1

    c.save()
    return send_file('labels.pdf', as_attachment=True)



def load_templates():
    try:
        with open('templates.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("The templates.json file was not found.")
        return {}
    except json.JSONDecodeError:
        print("Error decoding the templates.json file.")
        return {}

templates = load_templates()

if __name__ == '__main__':
    app.run(debug=True)

