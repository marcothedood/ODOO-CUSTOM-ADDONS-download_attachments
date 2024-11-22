{
    'name': 'Expense Attachments Downloader',
    'author': 'Martel Innovate IT',
    'version': '16.0.1.0.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Download all expense report attachments as single PDF',
    'depends': ['hr_expense'],
    'data': [
        'wizard/download_attachments.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
