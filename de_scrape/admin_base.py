

from flask_admin import BaseView

from flask_admin.contrib.sqla import ModelView

from flask_security import login_required, current_user, roles_required


class SecureBaseView(BaseView):
    """
    Makes sure admin areas require logins from authorized users.
    """

    allowed_roles = ['admin_super']

    def is_accessible(self):
        if not current_user.is_active() or not current_user.is_authenticated():
            return False

        role_allowed = False
        for role in self.allowed_roles:
            if current_user.has_role(role):
                role_allowed = True

        return role_allowed


    def is_admin(self):
        """
        Makes user is an administrator. 
        """
        # Temporarily comment out before the 'and' if you need to manually create the first admin
        return current_user.is_authenticated() 


    def _handle_view(self, name, **kwargs):
        if not self.is_admin():
            return redirect(url_for('index'))



class SecureModelView(ModelView):
    """
    Makes sure admin areas require logins from authorized users.
    """

    allowed_roles = ['admin_super']

    def check_role(self):
        role_allowed = False
        for role in self.allowed_roles:
            if current_user.has_role(role):
                role_allowed = True
        return role_allowed   

    def is_accessible(self):
        #print 'checking is_accessible on SecureModelView'
        if not current_user.is_active() or not current_user.is_authenticated():
            #print 'returning false in SecureModelView...'
            return False

        role_allowed = self.check_role()

        #print 'returning', role_allowed, 'in SecureModelView'

        return role_allowed


    def is_admin(self):
        """
        Makes user is an administrator. 
        """
        # Temporarily comment out before the 'and' if you need to manually create the first admin
        #print 'checking is_admin on SecureModelView'
        return self.check_role()


    def _handle_view(self, name, **kwargs):
        if not self.is_admin():
            return redirect(url_for('index'))
