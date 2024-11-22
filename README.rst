Introduction
============

This module installs a menuitem 'Download attachments' in the Action menu of an expense report.
Pressing this buttons results in the collective download of all attachments in one pdf file, to disk, that will be opened in the browser.




Installation
============

Prerequisites

* sudo apt update && sudo apt install img2pdf && sudo apt install imagemagick
* pip3 install PyPDF2==1.26.0
* pip3 install reportlab==3.5.13


Module installation


Note that a cron job is installed as well and can be found under:

* Settings -> technical -> Scheduled Actions


The autovacuum job, is activated once a week, to delete the downloaded pdfs from the ir.attachment table.
Explanation: the overall report containing all the individual attachments, is downloaded from the table ir.attachment where it was inserted
from the script.



Usage
=====

It sometimes happens that Firefox does not automatically open the download.
In case the message 'Firefox prevented this site from opening a pop-up window' is displayed,
press the button Preferences, and choose on of the displayed options.


Note that if we have an url:
http://127.0.0.1:8069/web#id=266&action=1080&model=hr.expense.sheet&view_type=form&cids=&menu_id=779

that the id 266 in this example is the id of the expense report as it is stored in the PSQL database.

This id also used in the name of the generated report: file:///Users/macbook/Downloads/expense_report_266-1.pdf



The following types of attachments are supported:

* pdf
* jpeg
* png
* url

When one of the attachments is of an unsupported type, a Validation error is raised.

If for some reason the conversion to pdf and the merging of pdf pages to the overall pdf fails,
another Validation error is raised.

In both cases the filename of the attachment that is the cause of the error, is specified.


urls are converted to hyperlinks, that can be clicked inside a box.
The expense name is displayed as a title above this box.


