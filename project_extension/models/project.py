# -*- coding: utf-8 -*-

import email
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class ProjectTask(models.Model):
    _inherit = 'project.task'
                
    @api.model
    def _notify_task_overdue(self):
        """Send mail notifying of projects that will be due in days
        """
        today = fields.Date.today()
        today_to_string = fields.Date.to_string(today)
        domain_overdue = [('date_deadline', '<', today_to_string), ('stage_id.is_closed', '=', False)]
        overdue_tasks = self.search(domain_overdue)
        for task in overdue_tasks:
            assignees = task.user_ids
            mail_template = self.env.ref("project_extension.task_one_day_overdue")
            for assignee in assignees:
                partner_id = assignee.partner_id
                mail_template.with_context(recipient=partner_id).send_mail(task.id, force_send=True)
        return True
    
    @api.model
    def _notify_task_will_due(self):
        """Send notification to assignee for tasks that are due in two days.
        """
        today = fields.Date.today()
        next_tomorrow = today + relativedelta(days=2)
        next_tomorrow_to_string = fields.Date.to_string(next_tomorrow)
        domain = [('stage_id.is_closed', '=', False), ('date_deadline', '=', next_tomorrow_to_string)]
        tasks_due_in_two_days = self.search(domain)
        mail_template = self.env.ref("project_extension.task_due_in_two_days")
        for task in tasks_due_in_two_days:
            for assignee in task.user_ids:
                mail_template.with_context(recipient=assignee.partner_id).send_mail(task.id, force_send=True)            
        return True
    