from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import PyPDF2
import base64
import io

class DownloadExpAttachment(models.TransientModel):
    _name = "download_exp_attachment"
    _description = 'Download Expense Attachment'

    @api.model
    def generate_pdf(self):
        """
        Redirects the user to a custom controller to download the PDF.
        """
        # Collect the active IDs (expense reports)
        active_ids = self.env.context.get('active_ids', [])

        # Redirect to the custom controller for downloading
        return {
            'type': 'ir.actions.act_url',
            'url': f'/download/expense_attachments?active_ids={",".join(map(str, active_ids))}',
            'target': 'new',
        }

    @api.model
    def generate_pdf_data(self):
        """
        Generates a single PDF containing all attachments related to the selected expense reports.
        """
        # Find related expense attachments
        related_exp_ids = self.env['hr.expense'].search([
            ('sheet_id', 'in', self.env.context.get('active_ids', []))
        ]).ids

        atms = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.expense'),
            ('res_id', 'in', related_exp_ids)
        ])

        if not atms:
            raise ValidationError('The report does not have attachments')

        # Initialize the PDF writer
        pdfWriter = PyPDF2.PdfFileWriter()

        # Process each attachment
        for atm in atms:
            if atm.mimetype == "application/pdf":
                # Merge PDF attachments
                file_reader = PyPDF2.PdfFileReader(io.BytesIO(base64.b64decode(atm.datas)), strict=False)
                for pageNum in range(file_reader.numPages):
                    pageObj = file_reader.getPage(pageNum)
                    pdfWriter.addPage(pageObj)

            else:
                # Skip unsupported file types
                raise ValidationError(f'Cannot create PDF.\nAttachment {atm.name} is not a supported format')

        # Generate the final PDF data in memory
        pdf_data = io.BytesIO()
        pdfWriter.write(pdf_data)
        pdf_data.seek(0)

        return pdf_data.getvalue()
