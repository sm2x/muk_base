###################################################################################
# 
#    Copyright (C) 2017 MuK IT GmbH
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

import os
import hashlib
import logging
import itertools

from odoo import _, SUPERUSER_ID
from odoo import models, api, fields
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class LockingModel(models.AbstractModel):
    
    _name = 'muk_security.mixins.locking'
    _description = 'Locking Mixin'
    
    #----------------------------------------------------------
    # Database
    #----------------------------------------------------------
    
    locked_by = fields.Many2one(
        comodel_name='res.users',
        string="Locked by")
    
    is_locked = fields.Boolean(
        compute='_compute_locked',
        string="Locked")
    
    is_lock_editor = fields.Boolean(
        compute='_compute_locked', 
        string="Editor")
        
    #----------------------------------------------------------
    # Locking
    #----------------------------------------------------------

    @api.multi
    def lock(self):
        self.write({'locked_by': self.env.uid})
    
    @api.multi
    def unlock(self):
        self.write({'locked_by': None})
    
    @api.multi
    def check_lock(self, *largs, **kwargs):
        for record in self:
            if record.locked_by.exists() and not record.locked_by.id in (self.env.uid, SUPERUSER_ID):
                raise AccessError(_("The record (%s [%s]) is locked, by an other user.") % (record._description, record.id)) 

    #----------------------------------------------------------
    # Read, View 
    #----------------------------------------------------------
    
    @api.depends('locked_by')
    def _compute_locked(self):
        for record in self:
            if record.locked_by.exists():
                record.update({'is_locked': True, 'is_lock_editor': record.locked_by.id == record.env.uid})
            else:
                record.update({'is_locked': False, 'is_lock_editor': False})

    #----------------------------------------------------------
    # Create, Update, Delete
    #----------------------------------------------------------

    @api.multi
    def write(self, vals):
        self.check_lock()
        return super(BaseModelLocking, self).write(vals)


    @api.multi
    def unlink(self):  
        self.check_lock()
        return super(BaseModelLocking, self).unlink()
    
