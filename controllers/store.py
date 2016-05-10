# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bet@net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Author Daniel J. Ramirez <djrmuv@gmail.com>
# Author Francisco Betancourt <francisco@betanetweb.com>


@auth.requires_membership('Config')
def create():
    """ args: [id_address] """
    address = db.address(request.args(0))
    if not address:
        redirect(URL('address', 'create', vars=dict(_next=URL('create'))))
    form = SQLFORM(db.store)
    form.vars.id_address = address.id
    if form.process().accepted:
        # insert store group
        db.auth_group.insert(role='Store %s' % form.vars.id)
        response.flash = T('form accepted')
        redirect(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Config')
def get():
    store = db.store(request.args(0))
    if not store:
        raise HTTP(404, T('Store NOT FOUND'))

    store_config = db(db.store_config.id_store == store.id).select()
    store_roles = db(db.store_role.id_store == store.id).select()
    return locals()


@auth.requires_membership('Config')
def update():
    return common_update('store', request.args, _vars=request.vars)


@auth.requires_membership('Config')
def delete():
    return common_delete('store', request.args)


@auth.requires_membership('Config')
def index():
    def store_options(row):
        update_btn, hide_btn = supert_default_options(row)
        return update_btn, hide_btn, OPTION_BTN('vpn_key', URL('seals', args=row.id),title=T('upload seals'))
    title = T('stores')
    data = SUPERT(db.store, fields=[
        'name', {
            'fields': ['id_address.street', 'id_address.exterior'],
            'label_as': T('Address')
        }
    ], options_func=store_options)
    return locals()

def read_certificate(certificate):
    """Read a certificate number and returns its base64 representation"""
    from OpenSSL import crypto
    from base64 import b64encode
    certificate_file=certificate.file.read()
    certificate.file.seek(0)
    try:
        cert = crypto.load_certificate(crypto.FILETYPE_ASN1,certificate_file)
    except:
        return (None,None,'Could not transform certificate')
    cert_number=hex(cert.get_serial_number())[2:-1].decode('hex')
    cert64=b64encode(certificate_file)
    return (cert64,cert_number,'Certificate read successfully')

def change_encoded_name_extension(filename,new_extension,table,field):
	from base64 import b16decode,b16encode
	coded_name=filename.split(".")
	new_filename=b16decode(coded_name[3].upper())[:-4]+new_extension
	return table+"."+field+"."+coded_name[2]+"."+b16encode(new_filename).lower()+new_extension

def clean_up_private_key(store_id,files_to_delete):    
    sdel_command="from sh import %s as sdel"%CONF.take('secure_delete.sdel')
    exec(sdel_command)
    for delete in files_to_delete:
		try:
			sdel(delete)
		except:
			pass
    db(db.store.id==store_id).update(
        private_key=None,
        csdpass=None,
        )

def read_private_key(path_key,path_pem,path_crypt,csdpass,new_pass):
    from sh import openssl
    try:
    	output=openssl.pkcs8('-inform','DER','-in',path_key,'-out',path_pem,'-passin','stdin',_in=csdpass)
    except:
        return False
    if output.exit_code!=0:
        return False
    try:
        output=openssl.rsa('-in',path_pem,'-des3','-out',path_crypt,'-passout','stdin',_in=new_pass)
    except:
        return False
    return True

def new_password(certificate_base64,store_created_on):
	from hashlib import sha1
	return sha1(certificate_base64+str(store_created_on)).hexdigest()[:-10]

def check_key_loading(path_key,key_pass):
	from Crypto.PublicKey import RSA
	from Crypto.Signature import PKCS1_v1_5
	try:
		key_file=open(path_key).read()
		rsakey=RSA.importKey(key_file,key_pass)
	except:
		return False
	return True

def check_key_cert_match(path_key,path_cer,key_pass):
    from sh import openssl
    try:
        out_cer=openssl.x509('-inform','DER','-noout','-modulus','-in',path_cer)
        out_key=openssl.rsa('-noout','-modulus','-in',path_key,'-passin','stdin',_in=key_pass)
    except:
        return False
    if out_cer.split("=")[1]!=out_key.split("=")[1]:
        return False
    return True

def validate_private_key(form):
    """Validate private key"""
    #If no private key is included there's nothing to do
    if form.vars.private_key==None or form.vars.private_key=="":    
        return
    #If the private_key is a string it's already read, if the private key is PEM skip
    elif isinstance(form.vars.private_key,str) and form.vars.private_key[-3:]=='pem':
        pass
    else:
		#The path to all files
        path_cer=db.store.certificate.uploadfolder+form.vars.certificate
        path_key=db.store.private_key.uploadfolder+form.vars.private_key
        path_pem=path_key[:-3]+'pem'
        path_crypt=db.store.private_key.uploadfolder+change_encoded_name_extension(form.vars.private_key,'.pem','store','private_key')
        #Check if you have password
        if not form.vars.csdpass:
            session.flash=T("Can't read private key without password")
            clean_up_private_key(form.vars.id,[path_cer,path_key,path_pem,path_crypt])
            redirect(URL('store','index'))
        new_pass=new_password(form.vars.certificate_base64,form.vars.created_on)
        #Read the key and transform to pem
        if not read_private_key(path_key,path_pem,path_crypt,form.vars.csdpass,new_pass):
            session.flash=T("Error reading private key, check your key file and password")
            clean_up_private_key(form.vars.id,[path_cer,path_key,path_pem,path_crypt])
            redirect(URL('store','index'))
        #Clean up before saving
        clean_up_private_key(form.vars.id,[path_key,path_pem])
        #Save the new path to the key
        db(db.store.id==form.vars.id).update(private_key=path_crypt)
        #Now lets check if the certificate and the key match
        if not check_key_cert_match(path_crypt,path_cer,new_pass): 
            session.flash=T("The certificate doesn't match the key file")
            clean_up_private_key(form.vars.id,[path_cer,path_key,path_pem,path_crypt])
            redirect(URL('store','index'))
    session.flash=T('Seals procesed correctly')

def validate_certificate(form):
    """Validates certificate"""
    from cgi import FieldStorage
    #Check if you received both the certificate and private key
    if form.vars.private_key=='' and form.vars.certificate=='':
        form.errors.certificate=T("Please input your certificate")
        form.errors.private_key=T("Please input your private key")
    if isinstance(form.vars.private_key,FieldStorage) and not isinstance(form.vars.certificate,FieldStorage):
        form.errors.certificate=T("Please input your certificate")
        form.errors.private_key=T("You must provide a private key and a certificate simultaneously")
        return
    if isinstance(form.vars.certificate,FieldStorage) and not isinstance(form.vars.private_key,FieldStorage):
        form.errors.certificate=T("You must provide a private key and a certificate simultaneously")
        form.errors.private_key=T("Please input your private key")
        return
    #If one is selected for deleting delete both
    if form.vars.certificate__delete=='on' or form.vars.private_key__delete=='on':
        form.vars.certificate_base64=None
        form.vars.certificate_number=None
        form.vars.private_key__delete='on'
        form.vars.certificate__delete='on'
        form.vars.csdpass=None
        return
    if isinstance(form.vars.certificate,str):
        return
    #Read certificate
    cert64,cert_number,text=read_certificate(form.vars.certificate)
    if cert64==None or cert_number==None:
        form.error.certificate=T(text)
        return
    form.vars.certificate_number=cert_number
    form.vars.certificate_base64=cert64
    

@auth.requires_membership('Config')
def seals():
    store = db.store(request.args(0))
    if not store:
        raise HTTP(404,T('Store NOT FOUND'))
    has_seals=False
    if store.certificate and store.private_key:
        has_seals=True
    db.store.id.readable=False
    db.store.name.writable=False
    db.store.name.readable=False
    db.store.map_url.writable=False
    db.store.map_url.readable=False
    db.store.id_address.writable=False
    db.store.id_address.readable=False
    db.store.certificate.writable=True
    db.store.private_key.writable=True
    db.store.image.writable=False
    db.store.image.readable=False
    db.store.invoice_series.writable=False
    db.store.invoice_series.readable=False
    db.store.csdpass.writable=True
    form=SQLFORM(db.store,store)
    if form.process(onvalidation=validate_certificate,onsuccess=validate_private_key).accepted:
        redirect(URL('store','index'))
    return locals()
