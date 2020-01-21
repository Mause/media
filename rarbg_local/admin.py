from flask import current_app
from flask_admin.contrib import sqla
from flask_user import current_user
from wtforms import validators
from wtforms.fields import PasswordField

from .db import Roles


class AdminOnly:
    def is_accessible(self):
        return Roles.Admin in getattr(current_user, 'roles', [])


class UserAdmin(sqla.ModelView, AdminOnly):
    column_exclude_list = ('password',)
    form_excluded_columns = ('password',)
    # edit_modal = create_modal = details_modal = True

    # Automatically display human-readable names for the current and available Roles when creating or editing a User
    column_auto_select_related = True

    def scaffold_form(self):
        form_class = super(UserAdmin, self).scaffold_form()

        form_class.password2 = PasswordField('New Password')
        form_class.username.kwargs['validators'] = [validators.DataRequired()]

        return form_class

    def on_model_change(self, form, model, is_created):
        if len(model.password2):
            model.password = current_app.user_manager.hash_password(model.password2)


# Customized Role model for SQL-Admin
class RoleAdmin(sqla.ModelView, AdminOnly):

    pass


class DownloadAdmin(sqla.ModelView, AdminOnly):
    column_exclude_list = ('movie',)
    form_choices = {'type': [('movie', 'movie'), ('episode', 'episode'),]}
    column_filters = ['added_by']
