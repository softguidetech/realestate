from odoo import fields, http, SUPERUSER_ID, _
from odoo.http import request
import werkzeug
from odoo.osv.expression import AND, OR
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from collections import OrderedDict
from operator import itemgetter
from odoo.exceptions import AccessError, MissingError
import base64
from odoo.tools import plaintext2html
from datetime import datetime, timedelta,date

class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        contract_count = http.request.env['contract.details'].search_count(
            [('partner_id', '=', http.request.env.user.partner_id.id)])
        maintenance_count = http.request.env['property.maintanance'].search_count(
            [('requister_id', '=', http.request.env.user.partner_id.id)])
        values['contract_count'] = contract_count
        values['maintenance_count'] = maintenance_count
        return values

    def _ticket_get_searchbar_sortings(self):
        return {
            "date": {
                "label": _("Newest"),
                "order": "create_date desc",
                "sequence": 1,
            },
            "name": {"label": _("Title"), "order": "name", "sequence": 2},
            # "stage": {"label": _("Stage"), "order": "stage_id", "sequence": 3},
            "update": {
                "label": _("Last Update"),
                # "order": "last_stage_update desc",
                "sequence": 4,
            },
        }

    # def _ticket_get_page_view_values(self, ticket, access_token, **kwargs):
    #     # closed_stages = request.env["helpdesk.ticket.stage"].search(
    #     #     [("close_from_portal", "=", True)]
    #     # )
    #     values = {
    #         # "closed_stages": closed_stages,  # used to display close buttons
    #         "page_name": "ticket",
    #         "ticket": ticket,
    #         "user": request.env.user,
    #     }
    #     return self._get_page_view_values(
    #         ticket, access_token, values, "my_tickets_history", False, **kwargs
    #     )

    def _ticket_get_groupby_mapping(self):
        return {
            "property": "property_id",
            # "stage": "stage_id",
        }

    @http.route(["/my/tickets1", "/my/tickets1/page/<int:page>"], type="http", auth="user", website=True, )
    def portal_my_tickets1(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None,
                          search_in=None, groupby=None, **kw):
        maintenance_ticket = request.env["property.maintanance"]
        # Avoid error if the user does not have access.
        if not maintenance_ticket.check_access_rights("read", raise_exception=False):
            return request.redirect("/my")

        values = self._prepare_portal_layout_values()

        searchbar_sortings = self._ticket_get_searchbar_sortings()
        searchbar_sortings = dict(
            sorted(
                self._ticket_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )

        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        # for stage in request.env["helpdesk.ticket.stage"].search([]):
        #     searchbar_filters[str(stage.id)] = {
        #         "label": stage.name,
        #         "domain": [("stage_id", "=", stage.id)],
        #     }
        #
        # searchbar_inputs = self._ticket_get_searchbar_inputs()
        # searchbar_groupby = self._ticket_get_searchbar_groupby()

        # if not sortby:
        #     sortby = "date"
        # order = searchbar_sortings[sortby]["order"]

        # if not filterby:
        #     filterby = "all"
        domain = searchbar_filters.get(filterby, searchbar_filters.get("all"))["domain"]
        #
        # if not groupby:
        #     groupby = "none"

        # if date_begin and date_end:
        #     domain += [
        #         ("create_date", ">", date_begin),
        #         ("create_date", "<=", date_end),
        #     ]
        #
        # if not search_in:
        #     search_in = "all"
        # if search:
        #     domain += self._ticket_get_search_domain(search_in, search)
        #
        # domain = AND(
        #     [
        #         domain,
        #         request.env["ir.rule"]._compute_domain(HelpdeskTicket._name, "read"),
        #     ]
        # )

        # count for pager
        ticket_count = 5
        # ticket_count = HelpdeskTicket.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/tickets1",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "groupby": groupby,
                "search": search,
                "search_in": search_in,
            },
            total=ticket_count,
            page=page,
            step=self._items_per_page,
        )

        # order = self._ticket_get_order(order, groupby)
        tickets = maintenance_ticket.sudo().search([('requister_id', '=', request.env.user.partner_id.id)] + domain,
            # order=order,
            limit=self._items_per_page,
            offset=pager["offset"]
        )
        request.session["property.maintanance"] = tickets.ids[:100]

        groupby_mapping = self._ticket_get_groupby_mapping()
        group = groupby_mapping.get(groupby)
        if group:
            grouped_tickets = [
                request.env["property.maintanance"].concat(*g)
                for k, g in groupbyelem(tickets, itemgetter(group))
            ]
        elif tickets:
            grouped_tickets = [tickets]
        else:
            grouped_tickets = []

        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "grouped_tickets": grouped_tickets,
                "page_name": "tt",
                "default_url": "/my/tickets1",
                "pager": pager,
                # "searchbar_sortings": searchbar_sortings,
                # "searchbar_groupby": searchbar_groupby,
                # "searchbar_inputs": searchbar_inputs,
                "search_in": search_in,
                "search": search,
                "sortby": sortby,
                "groupby": groupby,
                # "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
                "filterby": filterby,
            }
        )
        return request.render("realestate_sgt.portal_my_tickets1", values)

    @http.route(
        ["/my/ticket1/<int:maintenance_id>"], type="http", auth="public", website=True
    )
    def portal_my_ticket1(self, maintenance_id, access_token=None, **kw):
        maintenance_ids = request.env['property.maintanance'].browse(maintenance_id)
        try:
            ticket_sudo = self._document_check_access(
                "property.maintanance", maintenance_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        # ensure attachments are accessible with access token inside template
        for attachment in ticket_sudo.sudo().attachment_ids:
            attachment.generate_access_token()
        # values = self._ticket_get_page_view_values(ticket_sudo, access_token, **kw)
        return request.render("realestate_sgt.portal_helpdesk_ticket_page1",
            {
                "name": maintenance_ids.name,
                "maintenance_ids": maintenance_ids,
                # "values": values,
            })

    @http.route(['/my/contract', '/my/contract/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_contracts(self, **kwargs):
        contracts = request.env['contract.details'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)])
        values = {
            'contracts': contracts
        }
        return request.render("realestate_sgt.portal_my_contracts", values)

    @http.route(
        ["/my/contract/<int:contract_id>"], type="http", auth="public", website=True
    )
    def portal_my_contract(self, contract_id, access_token=None, **kw):
        contract_obj = request.env['contract.details'].sudo().browse(contract_id)
        return request.render("realestate_sgt.portal_contract_page",
                              {
                                  "contract_obj": contract_obj,
                              })


    @http.route(['/my/maintenance', '/my/maintenance/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_maintenance(self, **kwargs):
        maintenances = request.env['property.maintanance'].sudo().search([('requister_id', '=', request.env.user.partner_id.id)])
        values = {
            'maintenances': maintenances
        }
        return request.render("realestate_sgt.portal_my_maintenance", values)

    @http.route("/new/maintenance", type="http", auth="user", website=True)
    def create_new_maintenance(self, **kw):
        contract_ids = http.request.env["contract.details"].sudo().search([('partner_id', '=', request.env.user.partner_id.id),('state','in',['new','running'])])
        return http.request.render(
            "realestate_sgt.portal_create_maintenance",
            {
                "contract_ids": contract_ids,
                "today": self.format_date_today(),
            },
        )

    def format_date_today(self):
        today = date.today()
        return today.strftime("%Y-%m-%d")

    def _prepare_submit_maintenance_vals(self, **kw):
        property = http.request.env["product.product"].sudo().browse(
            int(kw.get("property"))
        )
        unit = request.env['property.unit'].sudo().browse(int(kw.get("unit")))
        vals = {
            "date": kw.get("date"),
            "operation": kw.get("operation"),
            "property_id": property.id,
            "unit_id": unit.id,
            "description": plaintext2html(kw.get("description")),
            "requister_id": request.env.user.partner_id.id,
            "name": kw.get("name"),
            "maintain_cost": property.maintain_charge,
            "responsible_id": property.user_id.partner_id.id,
        }
        return vals

    @http.route("/submitted/maintenance", type="http", auth="user", website=True, csrf=True)
    def submit_maintenance(self, **kw):
        attachment = False
        attachment_ids = []
        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    attachment = request.env["ir.attachment"].sudo().create(
                        {
                            "name": c_file.filename,
                            "datas": base64.b64encode(data),
                            "res_model": "property.maintanance",
                            # "res_id": new_maintenance.id,
                        }
                    )
                    attachment_ids.append(attachment)
        vals = self._prepare_submit_maintenance_vals(**kw)
        vals['attachment_ids'] = [(6, 0, [att.id for att in attachment_ids])]
        new_maintenance = request.env["property.maintanance"].sudo().create(vals)
        # new_maintenance.message_subscribe(partner_ids=request.env.user.partner_id.ids)
        self.send_maintenance_request_notification(new_maintenance)
        return werkzeug.utils.redirect("/my/ticket1/%s" % new_maintenance.id)

    def send_maintenance_request_notification(self, maintenance_request):
        manager_group = request.env.ref('realestate_sgt.group_manager').sudo()
        if manager_group:
            manager_users = manager_group.users.mapped('partner_id.email')
            if manager_users:
                template = request.env.ref('realestate_sgt.maintenance_request_notification_template').sudo()
                if template:
                    template.write({'email_to': ','.join(manager_users)})
                    template.sudo().send_mail(maintenance_request.id, force_send=False)

