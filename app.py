from flask import Flask, render_template, request, send_file
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128
from reportlab.lib import colors

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.json'):
            data = json.load(file)
            return generate_labels(data)
    return render_template('upload.html')

def generate_labels(data):
    c = canvas.Canvas("labels.pdf", pagesize=letter)
    width, height = letter  # Size of letter page
    num_labels_page = 0

    for index, row in enumerate(data):
        if num_labels_page >= 10:
            c.showPage()
            num_labels_page = 0

        # Base positions for the labels, adjusted for margins
        x = 0.25 * inch + ((index % 2) * 4.0 * inch)  # Adjusted width for 4" labels
        y = height - 0.75 * inch - (index // 2 * 2.0 * inch)  # Adjusted height for full 2" label

        # Parse the location data
        parts = row['Field1'].split()
        if len(parts) == 3:
            aisle, column, row_val = parts
        else:
            aisle, column, row_val = 'Unknown', 'Unknown', 'Unknown'  # Fallback

        bay = row.get('Bay', 'Unknown')  # Get the Bay value or default to 'Unknown'

        # Adjust font sizes and positions
        label_y_offset = 1.75 * inch  # Adjusted to ensure proper spacing within the 2" label height
        value_y_offset = -0.2 * inch  # Adjusted for compactness

        c.setFont("Helvetica-Bold", 12)  # Font for labels
        c.drawString(x + 0.08 * inch, y + label_y_offset, "Aisle:")
        c.drawString(x + 1.08 * inch, y + label_y_offset, "Column:")
        c.drawString(x + 2.28 * inch, y + label_y_offset, "Row:")
        c.drawString(x + 3.35 * inch, y + label_y_offset, "Bay:")

        c.setFont("Helvetica-Bold", 40)  # Font for values, adjusted for readability
        c.drawString(x, y + value_y_offset, aisle)
        c.drawString(x + 1.1 * inch, y + value_y_offset, column)
        c.drawString(x + 2.2 * inch, y + value_y_offset, row_val)
        c.drawString(x + 3.2 * inch, y + value_y_offset, bay)  # Add Bay value at 3.38 inch offset

        # Draw the arrow above the Bay value
        arrow_x = x + 3.35 * inch  # Centered slightly more to the right
        arrow_base_y = y + value_y_offset + 40  # Adjust position as necessary
        arrow_tip_y = y + 2.0 * inch  # Stretch to the top margin of the label
        arrow_width = 0.1 * inch  # Width of the arrow shaft

        c.setLineWidth(2)
        c.line(arrow_x, arrow_base_y, arrow_x, arrow_tip_y)  # Arrow shaft

        # Draw the filled arrow tip
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        arrow_head = c.beginPath()
        arrow_head.moveTo(arrow_x - arrow_width, arrow_tip_y - 0.2 * inch)
        arrow_head.lineTo(arrow_x + arrow_width, arrow_tip_y - 0.2 * inch)
        arrow_head.lineTo(arrow_x, arrow_tip_y)
        arrow_head.close()
        c.drawPath(arrow_head, stroke=1, fill=1)

        # Generate and draw the barcode, adjusted to align vertically higher
        barcode = code128.Code128(row['Field1'], barHeight=0.6 * inch, barWidth=1.5)
        barcode_y_offset = -0.5 * inch  # Adjusted for correct placement
        barcode_x_offset = 0.1 * inch  # Adjusted for correct placement
        barcode.drawOn(c, x + barcode_x_offset, y + barcode_y_offset)  # Adjusted for correct placement

        num_labels_page += 1

    c.save()
    return send_file('labels.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
