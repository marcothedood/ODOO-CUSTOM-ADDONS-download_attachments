from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import PyPDF2
import tempfile
import os
import base64
import io

class DownloadExpAttachment(models.TransientModel):
    _name = "download_exp_attachment"
    _description = 'Download Expense Attachment'

    @api.model
    def generate_pdf(self):
        related_exp_ids = self.env['hr.expense'].search([
            ('sheet_id', 'in', self.env.context.get('active_ids', []))
        ]).ids
        
        atms = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.expense'),
            ('res_id', 'in', related_exp_ids)
        ])

        if not atms:
            raise ValidationError('The report does not have attachments')

        pdfWriter = PyPDF2.PdfFileWriter()
        temp_path = tempfile.gettempdir()

        for atm in atms:
            try:
                if atm.mimetype == "application/pdf":
                    file_reader = PyPDF2.PdfFileReader(io.BytesIO(base64.b64decode(atm.datas)), strict=False)
                    for pageNum in range(file_reader.numPages):
                        pageObj = file_reader.getPage(pageNum)
                        pdfWriter.addPage(pageObj)

                elif atm.mimetype.startswith("image/"):
                    extension = atm.mimetype.split('/')[-1]
                    path2write = temp_path + "/imageToSave." + extension
                    with open(path2write, "wb") as fh:
                        fh.write(base64.b64decode(atm.datas))

                    output_path = temp_path + '/image.pdf'

                    if extension == 'png':
                        path2write_png = path2write
                        path2write = path2write_png.replace('.png', '.jpg')
                        os.system("convert {} {}".format(path2write_png, path2write))

                    os.system("img2pdf --output {} {}".format(output_path, path2write))

                    sample_pdf = open(output_path, mode='rb')
                    pdfdoc = PyPDF2.PdfFileReader(sample_pdf)
                    for pageNum in range(pdfdoc.numPages):
                        pageObj = pdfdoc.getPage(pageNum)
                        pdfWriter.addPage(pageObj)

                    os.remove(path2write)
                    os.remove(output_path)

                elif atm.mimetype == "application/octet-stream":
                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=letter)
                    expense = self.env['hr.expense'].browse(atm.res_id)
                    can.drawString(10, 720, expense.name)
                    hostlink = atm.url
                    linkRect = (10, 640, 200, 700)
                    can.linkURL(hostlink, linkRect, color=colors.Color(37/255, 150/255, 190/255), thickness=4)
                    can.save()
                    packet.seek(0)
                    new_pdf = PyPDF2.PdfFileReader(packet)
                    for pageNum in range(new_pdf.numPages):
                        pageObj = new_pdf.getPage(pageNum)
                        pdfWriter.addPage(pageObj)
                else:
                    raise ValidationError(f'Cannot create pdf.\nAttachment {atm.name} is of an unknown format')

            except Exception as e:
                raise ValidationError(f'Cannot create pdf.\nCheck attachment: {atm.name}\nError: {str(e)}')

        outfile_path = os.path.join(temp_path, "temp.pdf")
        with open(outfile_path, 'wb') as pdfOutputFile:
            pdfWriter.write(pdfOutputFile)

        with open(outfile_path, 'rb') as data:
            datas = base64.b64encode(data.read())

        os.remove(outfile_path)

        expense_report_id = self.env.context.get('active_ids', [])[0]
        name = f"expense_report_{expense_report_id}"

        attachment = self.env['ir.attachment'].sudo().create({
            'name': name,
            'mimetype': "application/pdf",
            'type': 'binary',
            'datas': datas
        })

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        download_url = f'/web/content/?model=ir.attachment&id={attachment.id}&filename_field=name&field=datas&download=true'

        return {
            'name': 'Expense attachments',
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }
