# Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain


class StockPicking(models.Model):
    _inherit = "stock.picking"

    products_availability_state = fields.Selection(
        search="_search_products_availability_state"
    )

    @api.model
    def _search_products_availability_state(self, operator, value):
        if operator in Domain.NEGATIVE_OPERATORS:
            # the ORM negates the result of the positive operator
            return NotImplemented
        if operator != "in":
            raise UserError(_("Invalid domain operator %s", operator))
        if any(not isinstance(v, str) and v is not False for v in value):
            raise UserError(_("Invalid domain right operand %s", value))
        # Search all pickings for which we need to compute the products availability.
        # The value would be ``False`` if the picking doesn't fall under this list.
        domain = Domain(
            [
                ("picking_type_code", "=", "outgoing"),
                ("state", "in", ["confirmed", "waiting", "assigned"]),
            ]
        )
        result = Domain.FALSE
        # Special case for "is not set" domains
        if False in value:
            result |= ~domain
        values = {v for v in value if v is not False}
        if values:
            # Perform a search and compute values to filter on-the-fly
            pickings = self.with_context(prefetch_fields=False).search(domain)
            pickings = pickings.filtered(
                lambda p: p.products_availability_state in values
            )
            result |= Domain("id", "in", pickings.ids)
        return result
