#!/usr/bin/env python
import sys
import os

dirname = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gargantext.settings")

# initialize Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


from django.contrib.auth import password_validation
from django.contrib.auth.hashers import ( check_password
                                        , is_password_usable
                                        , make_password
                                        )
from django.db import models
from django.utils.crypto import get_random_string, salted_hmac


# retrieve Django models
import django.apps
django_models = django.apps.apps.get_models()
django_models_names = set(model._meta.db_table for model in django_models)


from gargantext.util.db      import session
from gargantext.models.users import User
from django.core.mail        import send_mail

def make_random_password(length=10
                         , allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                         'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                         '0123456789'):
    """
    Generate a random password with the given length and given
    allowed_chars. The default value of allowed_chars does not have "I" or
    "O" or letters and digits that look similar -- just to avoid confusion.
    (source: django/contrib/auth)
    """
    return get_random_string(length, allowed_chars)


def notify_user(username, email, password):
    message = '''
    Bonjour,
    votre compte vient d'être créé.

    Vous pouvez désormais vous connecter ici:
    http://gargantext.org

    Votre login est: %s
    Votre mot de passe est : %s

    Bientôt, il y aura une formation Gargantext (gratuite).
    Inscription obligatoire pour les dernière places:

                    http://iscpif.fr/

    Nous restons à votre disposition pour tout complément d'information.
    Cordialement
    --
        L'équipe de Gargantext (CNRS)

    ''' % (username, password)

    send_mail('[Gargantext] Votre accès à la plateforme', message, 'alexandre.delanoe@iscpif.fr', [email], fail_silently=False )

    # add option for mass sending email

def create_user(username, email, user=None, password=None, active=False, notify=True):
    if user is None:
        user = User()
    user.username    = username
    user.first_name  = username
    user.email       = email
    user.is_active = True
    if password is None or password == "":
        password = make_random_password()
    user.password = make_password(password)
    session.add(user)
    session.commit()

    if notify == True:
        notify_user(username, email, password)

    return user

def delete_user(username):
    session.query(User).filter(User.username == username).delete()

def active_user(username, active=True):
    '''
    To get inactive, active=False
    '''
    user = session.query(User).filter(User.username == username).first()
    user.is_active = True
    user.save()

def mass_account_creation(fichier=None,init=False):
    if fichier is None:
        fichier = "/tmp/comptes.csv"
    accounts = open(fichier, "r")
    for line in accounts.readlines():
        username, email, password, fin = line.split(',')
        try:
            user = session.query(User).filter(User.username == username).first()
            print("User %s does exist already" % (username))
            if init == True:
                create_user(username, email, user=user, password=password, active=True, notify=True)
                print("User %s updated" % (username))
        except:
            print("User %s does not exist already" % (username))
            create_user(username, email, password=password, active=True, notify=True)
        #delete_user(username)
    accounts.close()

if __name__ == "__main__":
    mass_account_creation(fichier=sys.argv[1], init=True)


