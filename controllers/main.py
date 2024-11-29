from odoo import http
from odoo.http import request
import werkzeug

class DownloadAttachmentController(http.Controller):
    @http.route('/download/expense_attachments', type='http', auth='user')
    def download_expense_attachments(self, active_ids=None):
        if not active_ids:
            return werkzeug.exceptions.NotFound()

        active_ids = [int(id) for id in active_ids.split(',')]
        wizard = request.env['download_exp_attachment'].create({})
        pdf_data = wizard.with_context(active_ids=active_ids).generate_pdf_data()

        filename = 'expense_report.pdf'
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="{filename}"'),
        ]
        return request.make_response(pdf_data, headers=headers)
