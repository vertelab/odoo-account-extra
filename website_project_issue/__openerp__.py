# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Project issue upload attachement',
    'version': '0.1',
    'author': 'Vertel AB',
    'category': 'base',
    'website': 'http://www.vertel.se',
    'summary': 'Add form for upload attachements to project_issue',
    'description': """
A new form for upload attachements to project_issue
===================================================


    """,
    'depends': ['document','project_issue','website','project_issue_account' ],
    'external_dependencies': {
        'python': ['wand', ],
    },
    'data': ['project_issue_view.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
