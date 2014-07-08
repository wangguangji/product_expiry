# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import datetime
from openerp.osv import fields, osv
from openerp import pooler
from openerp.tools.translate import _


def strToDate(dt):
    dt_date=datetime.date(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]))
    return dt_date

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'

    def _get_date(dtype):
        """Return a function to compute the limit date for this type"""
        def calc_date(self, cr, uid, context=None):
            """Compute the limit date for a given date"""
            if context is None:
                context = {}
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            if not context.get('product_id', False):
                date = False
            else:
                product = pooler.get_pool(cr.dbname).get('product.product').browse(
                    cr, uid, context['product_id'])
                duration = getattr(product, dtype)
                if context.get('date',False):
                    dateTime = datetime.datetime.strptime(context['date'],DATETIME_FORMAT)
                else:
                    dateTime =  datetime.datetime.today()
                # set date to False when no expiry time specified on the product
                date = duration and (dateTime
                    + datetime.timedelta(days=duration))
            return date and date.strftime('%Y-%m-%d') or False
        return calc_date
    
    def _default_name(self, cr, uid, ids, name, arg, context=None):
        result = {}
        if context is None:
            context = {}
        for p in self.browse(cr, uid, ids, context=context):
            if strToDate(p.product_date) >datetime.date.today():
                raise osv.except_osv(
                    _('警告'),
                    _(
                        '生产日期不能超过今天！'
                    )
                ) 
            result[p.id] = "%s"%(p.product_date.replace('-',''))
        return result
    
    def _default_code(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for p in self.browse(cr, uid, ids, context=context):
            name = p['name'][0:8]
            res[p.id] = int(name)
        return res
        
    _columns = {
        'name':fields.function(_default_name,type='char',store=True, string='Serial Number'),
        'sort':fields.function(_default_code, type='integer', store=True, string=''),
        'product_date':fields.date(u'生产日期',required=True),       
        'life_date': fields.datetime('End of Life Date',
            help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.'),
        'use_date': fields.datetime('Best before Date',
            help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.'),
        'removal_date': fields.datetime('Removal Date',
            help='This is the date on which the goods with this Serial Number should be removed from the stock.'),
        'alert_date': fields.datetime('Alert Date',
            help="This is the date on which an alert should be notified about the goods with this Serial Number."),
    }
    # Assign dates according to products data
    def create(self, cr, uid, vals, context=None):
        newid = super(stock_production_lot, self).create(cr, uid, vals, context=context)
        obj = self.browse(cr, uid, newid, context=context)
        towrite = []
        for f in ('life_date', 'use_date', 'removal_date', 'alert_date'):
            if not getattr(obj, f):
                towrite.append(f)
        if context is None:
            context = {}
        context['product_id'] = obj.product_id.id
        self.write(cr, uid, [obj.id], self.default_get(cr, uid, towrite, context=context))
        return newid

    _defaults = {
        'life_date': _get_date('life_time'),
        'use_date': _get_date('use_time'),
        'removal_date': _get_date('removal_time'),
        'alert_date': _get_date('alert_time'),
    }
    
    _order = 'sort desc'
    
    def onchange_product_date(self, cr, uid, vals, product_date,product_id, context=None):
        if product_id is False:
            raise osv.except_osv(
                _('警告'),
                _(
                    '请首先选择商品！'
                )
            )
        
        DATETIME_FORMAT = "%Y-%m-%d"
        
        dateTime = datetime.datetime.strptime(product_date,DATETIME_FORMAT)
        if strToDate(product_date) >datetime.date.today():
            raise osv.except_osv(
                _('警告'),
                _(
                    '生产日期不能超过今天！'
                )
            )
            
        product = pooler.get_pool(cr.dbname).get('product.product').browse(cr, uid, product_id)
        result = {}
        for pro_time in ('life_', 'use_', 'removal_', 'alert_'):
            duration = getattr(product, pro_time+'time')
            dateTime = datetime.datetime.strptime(product_date,DATETIME_FORMAT)
            date = duration and (dateTime + datetime.timedelta(days=duration))
            date = date and date.strftime(DATETIME_FORMAT) or False
            result[pro_time+'date']  = date
        result['name'] = product_date.replace('-','')
        return {'value': result}
    
    
    
stock_production_lot()

class product_product(osv.osv):
    _inherit = 'product.product'
    _columns = {
        'life_time': fields.integer('Product Life Time',
            help='When a new a Serial Number is issued, this is the number of days before the goods may become dangerous and must not be consumed.'),
        'use_time': fields.integer('Product Use Time',
            help='When a new a Serial Number is issued, this is the number of days before the goods starts deteriorating, without being dangerous yet.'),
        'removal_time': fields.integer('Product Removal Time',
            help='When a new a Serial Number is issued, this is the number of days before the goods should be removed from the stock.'),
        'alert_time': fields.integer('Product Alert Time',
            help='When a new a Serial Number is issued, this is the number of days before an alert should be notified.'),
    }
product_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
