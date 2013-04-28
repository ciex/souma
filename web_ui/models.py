import datetime

from flask import url_for
from hashlib import sha256
from keyczar.keys import RsaPrivateKey, RsaPublicKey
from soma import db
from soma.helpers import Serializable, epoch_seconds
from sqlalchemy.exc import OperationalError


class Persona(Serializable, db.Model):
    """A Persona represents a user profile"""

    __tablename__ = "persona"
    id = db.Column(db.String(32), primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    crypt_private = db.Column(db.Text)
    crypt_public = db.Column(db.Text)
    sign_private = db.Column(db.Text)
    sign_public = db.Column(db.Text)
    modified = db.Column(db.DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    def __init__(
            self, id, username, email=None, sign_private=None, sign_public=None, crypt_private=None, crypt_public=None):
        self.id = id
        self.username = username
        self.email = email
        self.sign_private = sign_private
        self.sign_public = sign_public
        self.crypt_private = crypt_private
        self.crypt_public = crypt_public

    def __repr__(self):
        return "<{} [{}]>".format(str(self.username), self.id)

    def get_email_hash(self):
        """Return sha256 hash of this user's email address"""
        return sha256(self.email).hexdigest()

    def get_absolute_url(self):
        return url_for('persona', id=self.id)

    def generate_keys(self, password):
        """ Generate new RSA keypairs for signing and encrypting. Commit to DB afterwards! """

        # TODO: Store keys encrypted
        rsa1 = RsaPrivateKey.Generate()
        self.sign_private = str(rsa1)
        self.sign_public = str(rsa1.public_key)

        rsa2 = RsaPrivateKey.Generate()
        self.crypt_private = str(rsa2)
        self.crypt_public = str(rsa2.public_key)

    def encrypt(self, data):
        """ Encrypt data using RSA """

        key_public = RsaPublicKey.Read(self.crypt_public)
        return key_public.Encrypt(data)

    def decrypt(self, cypher):
        """ Decrypt cyphertext using RSA """

        key_private = RsaPrivateKey.Read(self.crypt_private)
        return key_private.Decrypt(cypher)

    def sign(self, data):
        """ Sign data using RSA """
        from base64 import b64encode

        key_private = RsaPrivateKey.Read(self.sign_private)
        signature = key_private.Sign(data)
        return b64encode(signature)

    def verify(self, data, signature_b64):
        """ Verify a signature using RSA """
        from base64 import b64decode

        signature = b64decode(signature_b64)
        key_public = RsaPublicKey.Read(self.sign_public)
        return key_public.Verify(data, signature)


class Star(Serializable, db.Model):
    """A Star represents a post"""

    __tablename__ = "star"
    id = db.Column(db.String(32), primary_key=True)
    text = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.datetime.now())
    modified = db.Column(db.DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    creator = db.relationship(
        'Persona',
        backref=db.backref('starmap'),
        primaryjoin="Persona.id==Star.creator_id")
    creator_id = db.Column(db.String(32), db.ForeignKey('persona.id'))

    def __init__(self, id, text, creator):
        self.id = id
        # TODO: Attach multiple items as 'planets'
        self.text = text

        self.creator_id = creator

    def __repr__(self):
        return "<Star {}: {}>".format(
            self.creator_id,
            (self.text[:8] if len(self.text) <= 8 else self.text[:6] + ".."))

    def get_absolute_url(self):
        return url_for('star', id=self.id)

    def hot(self):
        """i reddit"""
        from math import log
        # Uncomment to assign a score with analytics.score
        #s = score(self)
        s = 1.0
        order = log(max(abs(s), 1), 10)
        sign = 1 if s > 0 else -1 if s < 0 else 0
        return round(order + sign * epoch_seconds(self.created) / 45000, 7)


class Notification(db.Model):
    """Represents a stored notification to the user"""
    id = db.Column(db.String(32), primary_key=True)
    kind = db.Column(db.String(32))
    created = db.Column(db.DateTime, default=datetime.datetime.now())
    to_persona_id = db.Column(db.String(32))

    def __init__(self, kind, to_persona_id):
        from uuid import uuid4
        self.id = uuid4().hex
        self.kind = kind
        self.to_persona_id = to_persona_id


class ContactRequestNotification(Notification):
    def __init__(self, from_persona_id, to_persona_id):
        Notification.__init__(
            self,
            kind='contact_request',
            to_persona_id=to_persona_id)
        self.from_persona_id = from_persona_id


def init_db():
    try:
        Persona.query.first()
    except OperationalError:
        db.create_all()

        """# Generate test persona #1
        pv = Persona('247a1ca474b04a248c751d0eebf9738f', 'cievent', 'nichte@gmail.com')
        pv.generate_keys('jodat')
        db.session.add(pv)

        # Generate test persona #2
        paul = Persona('6e345777ca1a49cd8d005ac5e2f37cac', 'paul', 'mail@vincentahrend.com')
        paul.generate_keys('jodat')
        db.session.add(paul)

        db.session.commit()"""