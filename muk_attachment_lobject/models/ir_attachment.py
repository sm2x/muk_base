###################################################################################
#
#    Copyright (C) 2018 MuK IT GmbH
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
###################################################################################

import base64
import logging
import mimetypes

from odoo import api, models, _
from odoo.exceptions import AccessError

from odoo.addons.muk_fields_lobject.fields.lobject import LargeObject

_logger = logging.getLogger(__name__)

class LObjectIrAttachment(models.Model):
    
    _inherit = 'ir.attachment'

    store_lobject = LargeObject(
        string="Data")
    
    @api.model
    def storage_locations(self):
        locations = super(LObjectIrAttachment, self).storage_locations()
        locations.append('lobject')
        return locations
    
    @api.model
    def force_storage(self):
        if not self.env.user._is_admin():
            raise AccessError(_('Only administrators can execute this action.'))
        if self._storage() != 'lobject':
            return super(LObjectIrAttachment, self).force_storage()
        else:
            storage_domain = {
                'lobject': ('store_lobject', '=', False),
            }
            record_domain = [
                '&', storage_domain[self._storage()], 
                '|', ('res_field', '=', False), ('res_field', '!=', False)
            ]
            self.search(record_domain).migrate()
            return True
                
    @api.depends('store_lobject')
    def _compute_datas(self):
        bin_size = self._context.get('bin_size')
        for attach in self:
            if attach.store_lobject:
                if bin_size:
                    attach.datas = attach.store_lobject
                else:
                    attach.datas = attach.with_context({'base64': True}).store_lobject
            else:
                super(LObjectIrAttachment, attach)._compute_datas()
        
    def _inverse_datas(self):
        location = self._storage()
        for attach in self:
            if location == 'lobject':
                value = attach.datas
                bin_data = base64.b64decode(value) if value else b''
                vals = {
                    'file_size': len(bin_data),
                    'checksum': self._compute_checksum(bin_data),
                    'index_content': self._index(bin_data, attach.datas_fname, attach.mimetype),
                    'store_fname': False,
                    'db_datas': False,
                    'store_lobject': bin_data,
                }
                fname = attach.store_fname
                super(LObjectIrAttachment, attach.sudo()).write(vals)
                if fname:
                    self._file_delete(fname)
            else:
                super(LObjectIrAttachment, attach)._inverse_datas()