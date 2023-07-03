# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models


class BaseWip(models.Model):

    _name = "base.wip"
    _description = "Base Wip"

    @api.model
    def _get_states(self):
        return [
            ("draft", "New"),
            ("open", "In Progress"),
            ("pending", "Pending"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
            ("exception", "Exception"),
        ]

    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Model",
        index=True,
    )

    res_id = fields.Integer(
        string="Resource ID",
        index=True,
    )

    state = fields.Selection(
        # string="State",
        selection=[
            ("running", "Running"),
            ("closed", "Closed"),
        ],
        default="running",
        required=True,
    )

    date_hour_start = fields.Datetime(
        # string="Start",
        default=fields.Datetime.now,
        required=True,
    )

    date_start = fields.Date(
        # string="Date Start",
        default=fields.Date.context_today,
        required=False,
    )

    date_hour_stop = fields.Datetime(
        string="Stop",
        required=False,
    )

    date_stop = fields.Date(
        # string="Date Stop",
        required=False,
    )

    wip_time_seconds = fields.Float(
        # string="Lead Time Float",
        compute="_compute_lead_time",
    )

    wip_time = fields.Float(string="Duration", compute="_compute_lead_time", store=True)

    wip_state = fields.Selection(
        selection=_get_states,
        # string="State",
        index=True,
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=False,
        default=lambda self: self.env.uid,
    )

    @api.depends("date_hour_stop", "date_hour_start")
    def _compute_lead_time(self):
        for blocktime in self:
            d1 = fields.Datetime.from_string(blocktime.date_hour_start)
            if blocktime.date_hour_stop:
                d2 = fields.Datetime.from_string(blocktime.date_hour_stop)
            else:
                d2 = datetime.datetime.now()
            diff = d2 - d1
            blocktime.lead_time = round(diff.total_seconds() / 60.0, 2)

    def stop(self):
        for record in self.filtered(lambda o: o.state == "running"):
            record.write(
                {
                    "state": "closed",
                    "date_hour_stop": fields.Datetime.now(),
                    "date_stop": fields.Date.context_today(self),
                }
            )

    def start(self, crm_lead_id, crm_stage_id):
        self.env["crm.stage"].browse(crm_stage_id)
        self.env["crm.wip"].create(
            {
                "crm_lead_id": crm_lead_id,
                "crm_stage_id": crm_stage_id,
            }
        )
