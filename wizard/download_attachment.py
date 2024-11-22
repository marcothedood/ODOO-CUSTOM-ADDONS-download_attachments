
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
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

        related_exp_ids = self.env['hr.expense'].search([('sheet_id', 'in', self.env.context.get('active_ids', []))]).ids
        atms = self.env['ir.attachment'].search([('res_model', '=', 'hr.expense'),('res_id', 'in', related_exp_ids)])


        pdfWriter = PyPDF2.PdfFileWriter()
        temp_path = tempfile.gettempdir()


        if len(atms) == 0:
            raise ValidationError('The report does not have attachments')

        error2raise = False

        for atm in atms:
            try:
                if atm.mimetype == "application/pdf":

                    file_reader = PyPDF2.PdfFileReader(io.BytesIO(base64.b64decode(atm.datas)), strict=False)
                    for pageNum in range(file_reader.numPages):
                        pageObj = file_reader.getPage(pageNum)
                        pdfWriter.addPage(pageObj)

                elif atm.mimetype.startswith("image/"):

                    extension = atm.mimetype.split('/')[-1]
                    path2write = temp_path + "/imageToSave." + extension # for example for jpeg: /tmp/imageToSave.jpeg
                    with open(path2write, "wb") as fh:
                        img_data = atm.datas
                        fh.write(base64.decodebytes(img_data))

                    output_path = temp_path + '/image.pdf' # '/tmp/image.pdf'

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

                    # convert URL to a hyperlink on a pdf page

                    packet = io.BytesIO()
                    can = canvas.Canvas(packet, pagesize=letter)

                    hr_expense_name = self.env['hr.expense'].browse(atm.res_id).name
                    can.drawString(10, 720, hr_expense_name)

                    hostlink = atm.url

                    customColor = colors.Color(red=(37.0/255),green=(150.0/255),blue=(190.0/255))

                    linkRect = (10, 640, 200, 700)
                    can.linkURL(hostlink, linkRect, color=customColor, thickness=4)
                    can.save()

                    #move to the beginning of the buffer
                    packet.seek(0)
                    new_pdf = PyPDF2.PdfFileReader(packet)

                    for pageNum in range(new_pdf.numPages):
                        pageObj = new_pdf.getPage(pageNum)
                        pdfWriter.addPage(pageObj)

                else:
                    error2raise = 'Cannot create pdf.\nAttachment {} is of an unknown format or format not allowed'.format(atm.name)
                    break

            except:
                raise ValidationError('Cannot create pdf.\nCheck attachment: ' + atm.name)

        if error2raise:
            raise ValidationError(error2raise)

        outfile_name = "temp.pdf"
        outfile_path = os.path.join(temp_path, outfile_name)

        # create a temp file and write data to create new combined pdf

        pdfOutputFile = open(outfile_path, 'wb')
        pdfWriter.write(pdfOutputFile)   # do not confuse with .addPage, here we write to disk, in a tempor. pdf file
        pdfOutputFile.close()



        with open(outfile_path, 'rb') as data: # here we read that tempor. pdf file again, to prepare writing to ir.attachment table
            datas = base64.b64encode(data.read())

        os.remove(outfile_path)


        expense_report_id = self.env.context.get('active_ids', [])[0]

        name = "expense_report_{}".format(expense_report_id)

        attachment = self.env['ir.attachment']
        attachment_obj = attachment.sudo().create(
            {'name': name,
            # 'store_fname': 'awb.pdf',
             'mimetype': "application/pdf",
             'type': 'binary',
             'datas': datas})

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        download_url = '/web/content/?model=ir.attachment&id=' + str(attachment_obj.id) + '&filename_field=name&field=datas&download=true'


        return {
            'name': 'Expense attachments',
            'type': 'ir.actions.act_url',
            'url': str(base_url).replace('localhost', '127.0.0.1') + str(download_url),
            'target': 'new',
        }
